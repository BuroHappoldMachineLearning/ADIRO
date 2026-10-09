"""The README shows a latest-release badge per module in src/; keep the two in step."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
MODULES = sorted(p.stem for p in (ROOT / "src").glob("*.ttl"))
BADGE_FILTER = re.compile(r"img\.shields\.io/endpoint\?url=[^\"]*%2Fbadges%2F([a-z0-9_]+)\.json")
RELEASE_LINK = re.compile(r"/releases/tag/([a-z0-9_]+)-v(\d+\.\d+\.\d+)")


def _declared(module):
    ttl = (ROOT / "src" / f"{module}.ttl").read_text(encoding="utf-8")
    return re.search(r'owl:versionInfo\s+"([^"]+)"', ttl).group(1)


def test_every_module_has_a_release_badge():
    badged = set(BADGE_FILTER.findall(README))
    assert set(MODULES) - badged == set(), "add a release badge to README.md for: " + ", ".join(sorted(set(MODULES) - badged))


def test_no_badge_for_a_module_that_does_not_exist():
    stale = set(BADGE_FILTER.findall(README)) - set(MODULES)
    assert stale == set(), "README.md has a release badge for a module not in src/: " + ", ".join(sorted(stale))


def test_each_badge_links_to_the_release_page_of_the_declared_version():
    # The declared version only changes at a release cut, so this holds between releases and the
    # Release PR (scripts/prepare_release.py) keeps it true when it bumps the version.
    links = dict(RELEASE_LINK.findall(README))
    assert set(links) == set(MODULES), "every module needs exactly one badge link to its release page"
    wrong = {m: (links[m], _declared(m)) for m in MODULES if links[m] != _declared(m)}
    assert wrong == {}, f"README release links out of date (linked, declared): {wrong}"
