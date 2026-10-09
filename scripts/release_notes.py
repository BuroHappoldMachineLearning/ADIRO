#!/usr/bin/env python3
"""
GitHub Release notes for one module release (used by .github/workflows/backup-version.yml).

Usage:
    release_notes.py <module> <version> [--repo OWNER/NAME] [--root DIR]

Prints Markdown to stdout, starting with a "Relevant links" block (the module's published
documentation page, then its latest and this-version w3id.org URLs), followed by a summary line
(SemVer bump, previous -> this version, compare link), the module's changelog section, and the pull
requests that changed the module's ontology file since the previous release.

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


def bump_kind(previous, version):
    if previous is None:
        return "FIRST"
    old, new = _key(previous), _key(version)
    return "MAJOR" if new[0] > old[0] else "MINOR" if new[1] > old[1] else "PATCH"


def render(module, version, previous, changelog, changes, repo):
    """The Release body. `changes` is a list of (reference, text) pairs; reference is '#N' or a short SHA."""
    docs = f"{SITE}/ontologies/{module}/"
    kind = bump_kind(previous, version)
    parts = [f"**{'First release' if kind == 'FIRST' else kind + ' release'}**"]
    if previous:
        parts.append(f"{previous} → {version}")
    if previous:
        parts.append(f"[Compare](https://github.com/{repo}/compare/{module}-v{previous}...{module}-v{version})")
    lines = [
        "## Relevant links",
        "",
        f"- Documentation: {docs}",
        f"- Ontology (latest): {W3ID}/{module}",
        f"- This version ({version}): {W3ID}/{module}/{version}",
        "",
        " · ".join(parts),
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
    elif previous is None:
        lines += ["_First tagged release of this module; earlier history is in the repository log._", ""]
    return "\n".join(lines).rstrip("\n") + "\n"


def _run(args, root):
    return subprocess.run(args, cwd=root, capture_output=True, text=True)


def collect_changes(root, repo, module, previous, tag):
    """(reference, text) per PR (or bare commit) that changed the module's ontology file between the previous tag and `tag`."""
    if previous is None:
        return []
    log = _run(["git", "log", "--format=%H%x09%s", f"{module}-v{previous}..{tag}", "--", f"src/{module}.ttl"], root)
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

    tags = _run(["git", "tag", "--list", f"{args.module}-v*"], root).stdout.split()
    previous = previous_version(tags, args.module, args.version)
    cl = root / "changelogs" / f"{args.module}.md"
    text = section(cl.read_text(encoding="utf-8"), args.version) if cl.is_file() else None
    changelog = text or f"_No changelog entry for {args.version}._"
    changes = collect_changes(root, args.repo, args.module, previous, f"{args.module}-v{args.version}")
    sys.stdout.buffer.write(render(args.module, args.version, previous, changelog, changes, args.repo).encode("utf-8"))


if __name__ == "__main__":
    main()
