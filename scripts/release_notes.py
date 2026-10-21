#!/usr/bin/env python3
"""
GitHub Release notes for one module release (used by .github/workflows/backup-version.yml).

Usage:
    release_notes.py <module> <version> [--repo OWNER/NAME] [--root DIR]

Prints Markdown to stdout, starting with a summary line (SemVer bump, previous -> this version,
compare link), then the link bullets (the module's published documentation page, then its latest and
this-version w3id.org URLs), the module's changelog section, and the pull
requests that changed the module's ontology file since the previous release (the compare link and PR
list need the previous release to be tagged; earlier ones were released before tagging began).

Needs `git` with tags fetched; PR lookup uses the `gh` CLI (GH_TOKEN) and degrades to commit
subjects when it is unavailable. The pure parts (previous version, bump kind, rendering) are
unit-tested; stdlib only.
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_changelog import section  # noqa: E402

SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
SITE = "https://burohappoldmachinelearning.github.io/ADIRO"
W3ID = "https://w3id.org/adiro"


def _key(version):
    return tuple(int(x) for x in SEMVER_RE.match(version).groups())


def previous_version(tags, module, version):
    """Highest released `<module>-v<semver>` version below `version`, or None."""
    found = []
    for tag in tags:
        m = re.fullmatch(rf"{re.escape(module)}-v(\d+\.\d+\.\d+)", tag)
        if m and _key(m.group(1)) < _key(version):
            found.append(m.group(1))
    return max(found, key=_key) if found else None


def changelog_versions(text):
    """Released versions named by `## [x.y.z]` headings in a Keep-a-Changelog file."""
    return re.findall(r"^## \[(\d+\.\d+\.\d+)\]", text, re.M)


def previous_released(tags, changelog_text, module, version):
    """Highest version below `version` known from tags OR changelog headings, or None.

    Tags alone are not enough: the earliest tagged releases (2.0.0, 3.0.0) follow versions that were
    released before tagging began, and calling them "first release" would be wrong.
    """
    known = [v for v in changelog_versions(changelog_text) if _key(v) < _key(version)]
    tagged = previous_version(tags, module, version)
    if tagged:
        known.append(tagged)
    return max(known, key=_key) if known else None


def bump_kind(previous, version):
    if previous is None:
        return "FIRST"
    old, new = _key(previous), _key(version)
    return "MAJOR" if new[0] > old[0] else "MINOR" if new[1] > old[1] else "PATCH"


def render(module, version, previous, changelog, changes, repo, previous_tagged=True, previous_module=None):
    """The Release body. `changes` is a list of (reference, text) pairs; reference is '#N' or a short SHA.

    `previous_module` is the module a renamed module replaced (#171), when `previous` is that module's release.
    """
    docs = f"{SITE}/ontologies/{module}/"
    kind = bump_kind(previous, version)
    old = previous_module or module
    parts = [f"**{'First release' if kind == 'FIRST' else kind + ' release'}**"]
    if previous:
        parts.append(f"`{old}` {previous} → `{module}` {version}" if previous_module else f"{previous} → {version}")
    if previous and previous_tagged:
        parts.append(f"[Compare](https://github.com/{repo}/compare/{old}-v{previous}...{module}-v{version})")
    lines = [
        " · ".join(parts),
        "",
        f"- Documentation: {docs}",
        f"- Ontology (latest): {W3ID}/{module}",
        f"- This version ({version}): {W3ID}/{module}/{version}",
        *([f"- Renamed from `{previous_module}`: its releases keep their own IRIs, at {W3ID}/{previous_module}"] if previous_module else []),
        "",
        changelog,
        "",
    ]
    if changes:
        lines += ["### Pull requests in this release", ""]
        for ref, text in changes:
            link = f"[{ref}](https://github.com/{repo}/pull/{ref[1:]})" if ref.startswith("#") else f"`{ref}`"
            lines.append(f"- {link} {text}")
        lines.append("")
    elif previous and not previous_tagged:
        lines += [f"_The previous release ({previous}) was not tagged, so there is no compare link or pull-request list; earlier history is in the repository log._", ""]
    return "\n".join(lines).rstrip("\n") + "\n"


def _run(args, root):
    return subprocess.run(args, cwd=root, capture_output=True, text=True)


def collect_changes(root, repo, module, previous, tag, previous_module=None):
    """(reference, text) per PR (or bare commit) that changed the module's ontology file between the previous tag and `tag`.

    For a renamed module (#171) the previous tag is the old module's (`previous_module`), and both files count.
    """
    if previous is None:
        return []
    old = previous_module or module
    paths = [f"src/{module}.ttl"] + ([f"src/{old}.ttl"] if old != module else [])
    log = _run(["git", "log", "--format=%H%x09%s", f"{old}-v{previous}..{tag}", "--", *paths], root)
    seen, changes = set(), []
    for line in log.stdout.splitlines():
        sha, _, subject = line.partition("\t")
        found = []
        try:
            prs = _run(["gh", "api", f"repos/{repo}/commits/{sha}/pulls", "--jq", r'.[] | "\(.number)\t\(.title)"'], root)
            if prs.returncode == 0:
                found = [l.split("\t", 1) for l in prs.stdout.splitlines()]
            else:  # e.g. a missing token permission: say so rather than silently degrade
                print(f"::warning::PR lookup failed for {sha[:7]} (gh exit {prs.returncode}): listing the commit instead", file=sys.stderr)
        except FileNotFoundError:  # no gh CLI: fall back to the commit subject
            print(f"::warning::gh CLI not found: listing commit {sha[:7]} instead of its PR", file=sys.stderr)
        if found:
            for number, title in found:
                if number not in seen:
                    seen.add(number)
                    changes.append((f"#{number}", title))
        else:
            changes.append((sha[:7], subject))
    return changes


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("module")
    ap.add_argument("version")
    ap.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "BuroHappoldMachineLearning/ADIRO"))
    ap.add_argument("--root", default=".")
    args = ap.parse_args(argv)
    root = Path(args.root)

    cl = root / "changelogs" / f"{args.module}.md"
    cl_text = cl.read_text(encoding="utf-8") if cl.is_file() else ""
    previous_module, previous, tags = previous_across_renames(root, args.module, args.version, cl_text)
    previous_tagged = bool(previous) and f"{previous_module}-v{previous}" in tags
    text = section(cl_text, args.version) if cl_text else None
    changelog = text or f"_No changelog entry for {args.version}._"
    renamed = previous_module if previous_module != args.module else None
    changes = (collect_changes(root, args.repo, args.module, previous, f"{args.module}-v{args.version}", renamed)
               if previous_tagged else [])
    sys.stdout.buffer.write(
        render(args.module, args.version, previous, changelog, changes, args.repo, previous_tagged, renamed).encode("utf-8"))


def previous_across_renames(root, module, version, changelog_text, tag_lister=None):
    """(module, previous version, its tags): the previous release of `module`, or, for a renamed module's first
    release, the last release of the module it replaced (config/module_renames.json, #171)."""
    import module_renames as mr

    def list_tags(name):
        return tag_lister(name) if tag_lister else _run(["git", "tag", "--list", f"{name}-v*"], root).stdout.split()

    names = mr.lineage(mr.load(root), module)
    for name in names:
        tags = list_tags(name)
        text = changelog_text
        if name != module:
            old_log = Path(root) / "changelogs" / f"{name}.md"
            text = old_log.read_text(encoding="utf-8") if old_log.is_file() else ""
        previous = previous_released(tags, text, name, version)
        if previous:
            return name, previous, tags
    return module, None, list_tags(module)


if __name__ == "__main__":
    main()
