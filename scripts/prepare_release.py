#!/usr/bin/env python3
"""
Release-cut helper for the Release PR automation (.github/workflows/release-pr.yml, #99).

Per-module SemVer releases are cut deliberately (see docs/contribute/versioning/). This script
does the mechanical part so a reviewer only has to approve it:

    plan   [--json]   which modules have a release pending, and to which version
    apply  [--date D] write the release cut into the working tree: bump owl:versionInfo /
                      owl:versionIRI, move each [Unreleased] changelog section under a dated
                      heading, update the root CHANGELOG.md rollup, the README release-badge links and the AGENTS.md versions line
    priors            rewrite the owl:priorVersion lines of every module's header for its declared
                      version (idempotent; `apply` does this for each module it releases)
    body              the Release PR description (Markdown) for the current plan, including, per module, the
                      merged PRs that changed its ontology file since its last tagged release; it is rebuilt
                      on every push to main, so a PR merged while the Release PR is open appears on the next
                      rebuild
    tags              releases still to be completed: modules whose declared version has a
                      dated changelog heading (a merged release cut) but no snapshot under
                      versions/ yet. Idempotent: a release stays listed until its snapshot
                      lands, so a run that failed half way is picked up by the next run.

config/release_overrides.json maps a module to ONE value: a bump level ("patch" | "minor" |
"major") that raises that module's bump (never lowers it below what compat_diff requires), or
"hold", which leaves the module out of the Release PR. A bump override is consumed by the cut.

Every release names ALL of its earlier published versions with owl:priorVersion (one line per
version IRI, taken from versions/<module>/), so a tool that reads only the latest release (OntoCanvas
does not follow the chain) can list and open every earlier one. Archived releases are never edited.

Bumps come from scripts/compat_diff.py: the next version is the last released version plus the
bump the changes require. A module never released before keeps its declared version.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date as _date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compat_diff as cd  # noqa: E402
import module_renames as mr  # noqa: E402
import release_notes as rn  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# Dependency order (matches scripts/generate_docs.py); unknown modules sort after these.
MODULE_ORDER = [
    "adiro_provenance",
    "adiro_geometry",
    "adiro_drawing_metadata",
    "adiro_common_symbols",
    "adiro_domain_common",
    "adiro_facade_domain",
]
PENDING_VERDICTS = {"RELEASE_PENDING", "INSUFFICIENT_BUMP"}
OVERRIDES_FILE = Path("config") / "release_overrides.json"
OVERRIDE_VALUES = {cd.BUMP_PATCH, cd.BUMP_MINOR, cd.BUMP_MAJOR, "hold"}
MARKER = "<!-- release-pr -->"

UNRELEASED_RE = re.compile(r"## \[Unreleased\]([\r\n]+)(_Pending changes[^\r\n]*[\r\n]+)?")
NEXT_HEADING_RE = re.compile(r"^## \[", re.M)
VERSION_INFO_RE = re.compile(r'owl:versionInfo\s+"([^"]+)"')
AGENTS_VERSIONS_RE = re.compile(r"\(currently `[a-z]\w*` \d.*?\)\.", re.S)  # any module names, also after a rename (#171)


def _read(path):
    return Path(path).read_bytes().decode("utf-8")


def _write(path, text):
    Path(path).write_bytes(text.encode("utf-8"))


def order_key(module, renames=None):
    """Dependency position of `module`; a module and the one it replaced, or that replaced it, share a place (#171)."""
    names = mr.names(renames or {}, module)
    position = next((MODULE_ORDER.index(n) for n in names if n in MODULE_ORDER), len(MODULE_ORDER))
    return (position, module)


def modules(root=ROOT):
    names = [p.stem for p in (Path(root) / "src").glob("*.ttl")]
    renames = mr.load(root)
    return sorted(names, key=lambda m: order_key(m, renames))


def src_version(root, module):
    m = VERSION_INFO_RE.search(_read(Path(root) / "src" / f"{module}.ttl"))
    return m.group(1) if m else None


def unreleased_body(changelog_text):
    """Text of the [Unreleased] section, minus the standard placeholder line."""
    m = UNRELEASED_RE.search(changelog_text)
    if not m:
        return ""
    rest = changelog_text[m.end():]
    nxt = NEXT_HEADING_RE.search(rest)
    return (rest[: nxt.start()] if nxt else rest).strip()


def has_dated_heading(changelog_text, version):
    return bool(re.search(rf"^## \[{re.escape(version)}\] [—-] \d{{4}}-\d{{2}}-\d{{2}}", changelog_text, re.M))


def load_overrides(root=ROOT):
    """`{module: "patch"|"minor"|"major"|"hold"}` from config/release_overrides.json; {} if absent."""
    path = Path(root) / OVERRIDES_FILE
    if not path.is_file():
        return {}
    data = json.loads(_read(path) or "{}")
    known = set(modules(root))
    problems = [f"{m!r}: not a module in src/" for m in data if m not in known]
    problems += [f"{m!r}: {v!r} is not one of {sorted(OVERRIDE_VALUES)}" for m, v in data.items() if v not in OVERRIDE_VALUES]
    if problems:
        raise ValueError(f"{OVERRIDES_FILE}: " + "; ".join(problems))
    return data


def _pending(root):
    """Every module with a release pending, before overrides are applied."""
    root = Path(root)
    entries = []
    for module in modules(root):
        current = src_version(root, module)
        changelog = _read(root / "changelogs" / f"{module}.md")
        res = cd.analyze_module(root, module)
        if res["status"] == "no-baseline":
            if has_dated_heading(changelog, current):
                continue  # already cut; tagging is a separate step
            released, nxt, bump, deltas = None, current, "initial", []
        elif res["verdict"] in PENDING_VERDICTS:
            released, nxt, bump, deltas = res["old_version"], res["prospective_version"], res["required_bump"], res["deltas"]
        else:
            continue
        entries.append(
            {
                "module": module,
                # the module whose release `released` is: the module itself, or the one it replaced (#171)
                "released_module": res.get("baseline_module") or module,
                "released": released,
                "declared": current,
                "next": nxt,
                "bump": bump,
                "changelog_empty": not unreleased_body(changelog),
                "deltas": [{"type": t, "name": str(n), "severity": cd.DELTA_SEVERITY[t]} for t, n in deltas],
                "override": None,
            }
        )
    return entries


def _with_override(e, value):
    """Apply a bump override to a pending entry. It can raise the bump, never lower it."""
    if e["bump"] == "initial":
        e["override"] = f"{value} (no effect: first release keeps its declared version)"
    elif cd.BUMP_RANK[value] > cd.BUMP_RANK[e["bump"]]:
        e["override"] = f"raised from {e['bump'].upper()}"
        e["bump"], e["next"] = value, cd.apply_bump(e["released"], value)
    else:
        e["override"] = f"{value} (no effect: the changes already require {e['bump'].upper()})"
    return e


def plan(root=ROOT):
    """One entry per module that will be released, in dependency order (overrides applied)."""
    overrides = load_overrides(root)
    return [_with_override(e, overrides[e["module"]]) if e["module"] in overrides else e
            for e in _pending(root) if overrides.get(e["module"]) != "hold"]


def held(root=ROOT):
    """Pending modules left out of the Release PR by a `hold` override."""
    overrides = load_overrides(root)
    return [e for e in _pending(root) if overrides.get(e["module"]) == "hold"]


def _move_unreleased(text, version, day):
    m = UNRELEASED_RE.search(text)
    if not m:
        raise ValueError("no [Unreleased] heading")
    nl = "\r\n" if "\r\n" in m.group(1) else "\n"
    heading = f"## [{version}] — {day}{nl}{nl}"
    if m.group(2):  # keep the placeholder under a fresh, empty [Unreleased]
        return text[: m.end()] + nl + heading + text[m.end():]
    return text[: m.end()] + heading + text[m.end():]


def _bump_ttl(text, module, old, new):
    iri_old, iri_new = f"https://w3id.org/adiro/{module}/{old}>", f"https://w3id.org/adiro/{module}/{new}>"
    if text.count(iri_old) != 1 or text.count(f'owl:versionInfo "{old}"') != 1:
        raise ValueError(f"{module}: expected exactly one versionIRI/versionInfo for {old}")
    return text.replace(iri_old, iri_new).replace(f'owl:versionInfo "{old}"', f'owl:versionInfo "{new}"')


PRIOR_LINE_RE = re.compile(r"^[ \t]*owl:priorVersion[ \t]+<[^>\r\n]*>[ \t]*;[ \t]*\r?\n", re.M)
VERSION_IRI_LINE_RE = re.compile(r"^([ \t]*)owl:versionIRI[ \t]+<[^>\r\n]*>[ \t]*;", re.M)


def _semver_key(version):
    return tuple(int(x) for x in cd.SEMVER_RE.match(version).groups())


def archived_versions(root, module):
    """Versions archived under versions/<module>/, lowest first: the releases whose version IRI is published."""
    base = Path(root) / "versions" / module
    found = []
    if base.is_dir():
        for d in base.iterdir():
            if d.is_dir() and cd.SEMVER_RE.match(d.name) and (d / f"{module}.ttl").is_file():
                found.append(d.name)
    return sorted(found, key=_semver_key)


def prior_version_iris(root, module, below):
    """The version IRIs a release of `below` must name with owl:priorVersion: every earlier archived version.

    A renamed module's history includes the releases of the module it replaced (config/module_renames.json, #171),
    named by their own IRIs: the numbering continues across the rename, so they all sort below the new versions.
    """
    cutoff = _semver_key(below)
    found = [(_semver_key(v), name, v) for name in mr.lineage(mr.load(root), module)
             for v in archived_versions(root, name) if _semver_key(v) < cutoff]
    return [f"https://w3id.org/adiro/{name}/{v}" for _, name, v in sorted(found)]


def _set_prior_versions(text, iris):
    """Rewrite the owl:priorVersion lines of the owl:Ontology header: one per IRI, just before owl:versionIRI."""
    nl = "\r\n" if "\r\n" in text else "\n"
    text = PRIOR_LINE_RE.sub("", text)
    if "owl:priorVersion" in text:
        raise ValueError("owl:priorVersion in a form this script does not rewrite: use one `owl:priorVersion <iri> ;` line each")
    found = list(VERSION_IRI_LINE_RE.finditer(text))
    if len(found) != 1:
        raise ValueError("expected exactly one owl:versionIRI line in the ontology header")
    at, indent = found[0].start(), found[0].group(1)
    return text[:at] + "".join(f"{indent}owl:priorVersion <{iri}> ;{nl}" for iri in iris) + text[at:]


def sync_priors(root):
    """Rewrite every module's owl:priorVersion lines for its declared version; return the modules that changed."""
    root, changed = Path(root), []
    for module in modules(root):
        version = src_version(root, module)
        if not version:
            continue
        ttl = root / "src" / f"{module}.ttl"
        old = _read(ttl)
        new = _set_prior_versions(old, prior_version_iris(root, module, version))
        if new != old:
            _write(ttl, new)
            changed.append(module)
    return changed


def apply_plan(root, entries, day):
    root = Path(root)
    for e in entries:
        module = e["module"]
        ttl = root / "src" / f"{module}.ttl"
        text = old = _read(ttl)
        if e["declared"] != e["next"]:
            text = _bump_ttl(text, module, e["declared"], e["next"])
        text = _set_prior_versions(text, prior_version_iris(root, module, e["next"]))
        if text != old:
            _write(ttl, text)
        cl = root / "changelogs" / f"{module}.md"
        _write(cl, _move_unreleased(_read(cl), e["next"], day))

    overrides_path = root / OVERRIDES_FILE
    if overrides_path.is_file():  # a bump override applies to one release only
        overrides = load_overrides(root)
        released = {e["module"] for e in entries}
        kept = {m: v for m, v in overrides.items() if v == "hold" or m not in released}
        if kept != overrides:
            _write(overrides_path, json.dumps(kept, indent=2) + "\n")

    versions = {m: src_version(root, m) for m in modules(root)}
    rollup = root / "CHANGELOG.md"
    if rollup.is_file():
        text = _read(rollup)
        for module, ver in versions.items():
            text = re.sub(rf"(\| `{module}` \| )[^|]*( \|)", rf"\g<1>{ver}\g<2>", text)
        _write(rollup, text)
    readme = root / "README.md"
    if readme.is_file():  # the badges link to each module's latest release page
        text = _read(readme)
        for module, ver in versions.items():
            text = re.sub(rf"(releases/tag/{module}-v)\d+\.\d+\.\d+", rf"\g<1>{ver}", text)
        _write(readme, text)
    agents = root / "AGENTS.md"
    if agents.is_file():
        text = _read(agents)
        listing = "; ".join(f"`{m}` {v}" for m, v in versions.items())
        _write(agents, AGENTS_VERSIONS_RE.sub(lambda _: f"(currently {listing}).", text, count=1))


def releases_to_complete(root=ROOT):
    """`<module>-v<ver>` for each merged release cut whose snapshot is not in versions/ yet.

    The snapshot is the last artefact the release chain writes (tag -> Release -> backup-version.yml
    -> versions/<module>/<ver>/), so "no snapshot" means the release is not finished, whether it was
    never started or failed part-way. The caller decides what is missing: create the Release, or
    re-dispatch the snapshot job for a tag/Release that already exists.
    """
    root = Path(root)
    out = []
    for module in modules(root):
        ver = src_version(root, module)
        snapshot = root / "versions" / module / ver / f"{module}.ttl" if ver else None
        if ver and not snapshot.is_file() and has_dated_heading(_read(root / "changelogs" / f"{module}.md"), ver):
            out.append(f"{module}-v{ver}")
    return out


def _delta_summary(e):
    notable = [d for d in e["deltas"] if d["severity"] != cd.NON_BREAKING]
    if e["bump"] == "initial":
        return "First release"
    if not notable:
        counts = {}
        for d in e["deltas"]:
            counts[d["type"]] = counts.get(d["type"], 0) + 1
        return ", ".join(f"{n}× {t}" for t, n in sorted(counts.items())) or "—"
    shown = ", ".join(f"`{d['name']}` ({d['type']})" for d in notable[:6])
    more = f" and {len(notable) - 6} more" if len(notable) > 6 else ""
    return shown + more


def _tag_exists(root, tag):
    return subprocess.run(["git", "rev-parse", "-q", "--verify", f"refs/tags/{tag}"], cwd=root, capture_output=True).returncode == 0


def merged_changes(root, entries, repo, collect=rn.collect_changes):
    """{module: [(reference, text)] or None}: what changed each module's ontology file since its last tagged release.

    The references are the merged PRs ('#N') behind those commits, or a short hash for a commit pushed straight to
    main: the same list the GitHub Release notes give (release_notes.collect_changes), with the range ending at
    HEAD (main) because the release is not tagged yet. None means there is nothing to count from: a first release,
    or a previous release that was never tagged (the ones made before tagging began).
    """
    changes = {}
    for e in entries:
        released, released_module = e["released"], e.get("released_module") or e["module"]
        if released and _tag_exists(root, f"{released_module}-v{released}"):
            if released_module == e["module"]:
                changes[e["module"]] = collect(root, repo, e["module"], released, "HEAD")
            else:  # a renamed module: from the old module's last tag, over both files (#171)
                changes[e["module"]] = collect(root, repo, e["module"], released, "HEAD", previous_module=released_module)
        else:
            changes[e["module"]] = None
    return changes


def _changes_section(entries, changes, repo):
    out = ["", "### Pull requests in this release", "",
           "Every merged change to a module's ontology file since its last release. This description is rebuilt from `main` after "
           "every merge, so a PR merged while this one is open appears here on the next rebuild."]
    for e in entries:
        items = changes.get(e["module"])
        head = f"**`{e['module']}`** {_released_text(e)} → {e['next']}"
        if items is None:
            why = "this is its first release" if not e["released"] else f"its previous release ({e['released']}) was not tagged"
            out += ["", f"{head}: _no list, because {why}._"]
        elif not items:
            out += ["", f"{head}: _no merged PR changed the ontology file since the last release._"]
        else:
            out += ["", head, ""]
            for ref, text in items:
                link = f"[{ref}](https://github.com/{repo}/pull/{ref[1:]})" if ref.startswith("#") else f"`{ref}`"
                out.append(f"- {link} {text}")
    return out


def _released_text(e):
    """The last release, naming the module it belongs to when that is the module a renamed one replaced (#171)."""
    if not e["released"]:
        return "never released"
    released_module = e.get("released_module") or e["module"]
    return e["released"] if released_module == e["module"] else f"`{released_module}` {e['released']}"


def body(entries, root=ROOT, held_entries=(), changes=None, repo=None):
    root = Path(root)
    repo = repo or os.environ.get("GITHUB_REPOSITORY") or "BuroHappoldMachineLearning/ADIRO"
    empty = [e["module"] for e in entries if e["changelog_empty"]]
    out = [MARKER, "## Release cut", ""]
    out.append(
        "Maintained automatically: this PR is rebuilt from `main` after every merge, so it always shows "
        "everything that is unreleased. Merging it tags and publishes one release per module below."
    )
    out += ["", "| Module | Released | Next | Bump | Driven by |", "|---|---|---|---|---|"]
    for e in entries:
        out.append(
            f"| `{e['module']}` | {_released_text(e) if e['released'] else 'never'} | **{e['next']}** | {e['bump'].upper()} | "
            f"{_delta_summary(e)}{' — **override:** ' + e['override'] if e['override'] else ''} |"
        )
    if held_entries:
        out += ["", "**Held back** by `config/release_overrides.json` (not in this release): "
                + ", ".join(f"`{h['module']}` (would be {h['next']}, {h['bump'].upper()})" for h in held_entries) + "."]
    if empty:
        out += [
            "",
            "> [!WARNING]",
            "> No `[Unreleased]` changelog entry for: " + ", ".join(f"`{m}`" for m in empty) + ". The release notes "
            "for these would be empty, so this PR is a draft. Add the entry to `changelogs/<module>.md` on `main`; "
            "this PR updates itself.",
        ]
    if changes is not None:
        out += _changes_section(entries, changes, repo)
    out += ["", "### Before merging"]
    out += [
        "- [ ] Each bump is right. It is the compat-diff **minimum** unless an override raised it. To release a larger bump, or to "
        "leave a module out, set it in `config/release_overrides.json` on `main` (`\"minor\"`, `\"major\"`, `\"patch\"` or `\"hold\"`); the "
        "branch is rebuilt on every merge, so edits made directly on it are lost.",
        "- [ ] The changelog entries below read well as release notes.",
    ]
    out += ["", "### What merging does", "- Tags each module `<module>-v<semver>` and publishes a GitHub Release.",
            "- `backup-version.yml` snapshots `versions/<module>/<semver>/` and dispatches the Pages deploy.", ""]
    for e in entries:
        text = unreleased_body(_read(root / "changelogs" / f"{e['module']}.md")) or "_(empty)_"
        out += [f"<details><summary><code>{e['module']}</code> {e['next']} — changelog</summary>", "", text, "", "</details>", ""]
    return "\n".join(out).rstrip() + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_plan = sub.add_parser("plan")
    p_plan.add_argument("--json", action="store_true")
    p_apply = sub.add_parser("apply")
    p_apply.add_argument("--date", default=_date.today().isoformat())
    sub.add_parser("body")
    sub.add_parser("tags")
    sub.add_parser("priors")
    args = ap.parse_args(argv)

    if args.cmd == "tags":
        for t in releases_to_complete():
            print(t)
        return
    if args.cmd == "priors":
        changed = sync_priors(ROOT)
        print("owl:priorVersion rewritten for: " + ", ".join(changed) if changed else "owl:priorVersion already up to date.")
        return
    try:
        entries = plan()
    except ValueError as err:
        sys.exit(f"error: {err}")
    if args.cmd == "plan":
        if args.json:
            print(json.dumps(entries, indent=2))
        else:
            for e in entries:
                print(f"{e['module']}: {e['released'] or 'never'} -> {e['next']} ({e['bump']})" + ("  [empty changelog]" if e["changelog_empty"] else ""))
            if not entries:
                print("No release pending.")
    elif args.cmd == "apply":
        apply_plan(ROOT, entries, args.date)
    elif args.cmd == "body":
        repo = os.environ.get("GITHUB_REPOSITORY") or "BuroHappoldMachineLearning/ADIRO"
        changes = merged_changes(ROOT, entries, repo)
        sys.stdout.buffer.write(body(entries, ROOT, held(), changes, repo).encode("utf-8"))


if __name__ == "__main__":
    main()
