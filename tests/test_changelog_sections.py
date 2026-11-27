"""An [Unreleased] section names each kind of change once (review of #332).

Two pull requests that each add a `### Changed` under [Unreleased] far enough apart are merged by git without a conflict,
so the worklog bot never sees it (#313), and the release cut would copy both headings into the released section.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_no_heading_is_repeated_under_unreleased():
    repeated = {}
    for path in sorted((ROOT / "changelogs").glob("*.md")):
        text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
        m = re.search(r"^## \[Unreleased\]\n(.*?)(?=^## \[|\Z)", text, re.S | re.M)
        if not m:
            continue
        headings = re.findall(r"^### (.+)$", m.group(1), re.M)
        twice = sorted({h for h in headings if headings.count(h) > 1})
        if twice:
            repeated[path.name] = twice
    assert not repeated, f"join the repeated headings under [Unreleased]: {repeated}"
