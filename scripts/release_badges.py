#!/usr/bin/env python3
"""
Per-module release-badge data (shields.io "endpoint" JSON).

Writes ``docs/badges/<module>.json`` for every ``src/<module>.ttl``, holding the module's latest
RELEASED version (the highest SemVer under ``versions/<module>/``). generate_docs.py calls it, so
the files are published with the site and refresh on every deploy, including the one the snapshot
job dispatches after a release. The README badges read them through
``https://img.shields.io/endpoint?url=<site>/badges/<module>.json``; the same files can feed
anything else that wants "the latest version of each module".

The JSON follows shields.io's endpoint schema (unknown keys would be rejected), so it carries only
``schemaVersion``, ``label``, ``message`` and ``color``.
"""

import json
import re
from pathlib import Path

SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
COLOR_RELEASED = "16305f"  # ADIRO navy
COLOR_UNRELEASED = "lightgrey"


def latest_released_version(repo_root, module):
    """Highest SemVer directory under versions/<module>/ that holds the snapshot, or None."""
    base = Path(repo_root) / "versions" / module
    if not base.is_dir():
        return None
    found = [
        (tuple(int(x) for x in m.groups()), d.name)
        for d in base.iterdir()
        if d.is_dir() and (m := SEMVER_RE.match(d.name)) and (d / f"{module}.ttl").is_file()
    ]
    return max(found)[1] if found else None


def badge_json(repo_root, module):
    version = latest_released_version(repo_root, module)
    return {
        "schemaVersion": 1,
        "label": module,
        "message": version or "unreleased",
        "color": COLOR_RELEASED if version else COLOR_UNRELEASED,
    }


def write_release_badges(repo_root, output_dir):
    """Write docs/badges/<module>.json for each module in src/. Returns the list of files written."""
    repo_root, out = Path(repo_root), Path(output_dir) / "badges"
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for ttl in sorted((repo_root / "src").glob("*.ttl")):
        path = out / f"{ttl.stem}.json"
        path.write_text(json.dumps(badge_json(repo_root, ttl.stem), indent=2) + "\n", encoding="utf-8")
        written.append(path)
    return written
