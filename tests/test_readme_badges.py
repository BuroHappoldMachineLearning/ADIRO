"""The README shows a latest-release badge per module in src/; keep the two in step."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
MODULES = sorted(p.stem for p in (ROOT / "src").glob("*.ttl"))
BADGE_FILTER = re.compile(r"img\.shields\.io/endpoint\?url=[^\"]*%2Fbadges%2F([a-z0-9_]+)\.json")


def test_every_module_has_a_release_badge():
    badged = set(BADGE_FILTER.findall(README))
    assert set(MODULES) - badged == set(), "add a release badge to README.md for: " + ", ".join(sorted(set(MODULES) - badged))


def test_no_badge_for_a_module_that_does_not_exist():
    stale = set(BADGE_FILTER.findall(README)) - set(MODULES)
    assert stale == set(), "README.md has a release badge for a module not in src/: " + ", ".join(sorted(stale))
