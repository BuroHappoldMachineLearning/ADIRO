#!/usr/bin/env python3
"""Extract one version's section from a module's Keep-a-Changelog file (RES-82 / #49).

Usage:
    extract_changelog.py <module> <version> [changelogs_dir]

Prints (to stdout) the body under the ``## [<version>]`` heading, heading
excluded. If that heading is absent, falls back to the ``## [Unreleased]``
section (with a note); if neither exists, prints a short notice. Stdlib only —
runs on a bare CI Python.
"""
import re
import sys
from pathlib import Path


def section(text, heading):
    """Return the body under '## [<heading>]' up to the next '## [' or EOF, or None."""
    pat = re.compile(
        r"^##\s*\[" + re.escape(heading) + r"\][^\n]*\n(.*?)(?=^##\s*\[|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pat.search(text)
    return m.group(1).strip() if m else None


def main():
    if len(sys.argv) < 3:
        print("usage: extract_changelog.py <module> <version> [changelogs_dir]", file=sys.stderr)
        sys.exit(2)
    module, version = sys.argv[1], sys.argv[2]
    cdir = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("changelogs")
    path = cdir / f"{module}.md"
    if not path.is_file():
        print(f"_No changelog file `{path}`._")
        return
    text = path.read_text(encoding="utf-8")

    body = section(text, version)
    if body:
        print(body)
        return
    unreleased = section(text, "Unreleased")
    if unreleased:
        print(f"_No `[{version}]` heading in the changelog yet — showing **Unreleased**:_\n\n{unreleased}")
        return
    print(f"_No changelog entry for `{version}` in `{path}`._")


if __name__ == "__main__":
    main()
