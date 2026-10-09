"""Tests for the Release-notes generator (scripts/release_notes.py); the git/gh lookups are not exercised."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import release_notes as rn  # noqa: E402

TAGS = ["aec_x-v1.0.0", "aec_x-v2.0.0", "aec_x-v10.0.0", "aec_y-v9.0.0", "aec_x-v2.0.1"]


def test_previous_version_is_the_highest_lower_semver_of_the_same_module():
    assert rn.previous_version(TAGS, "aec_x", "2.0.1") == "2.0.0"
    assert rn.previous_version(TAGS, "aec_x", "10.0.0") == "2.0.1"  # numeric, not alphabetical
    assert rn.previous_version(TAGS, "aec_x", "1.0.0") is None
    assert rn.previous_version(TAGS, "aec_z", "1.0.0") is None


def test_bump_kind():
    assert [rn.bump_kind(p, v) for p, v in [(None, "1.0.0"), ("1.2.3", "2.0.0"), ("1.2.3", "1.3.0"), ("1.2.3", "1.2.4")]] == [
        "FIRST", "MAJOR", "MINOR", "PATCH"]


def test_render_links_docs_compare_and_prs():
    text = rn.render("aec_x", "2.0.1", "2.0.0", "### Added\n- a thing", [("#108", "Add a thing"), ("abc1234", "a direct commit")], "o/r")
    assert text.startswith("## aec_x 2.0.1")
    assert "**PATCH release** · 2.0.0 → 2.0.1" in text
    assert "[Documentation](https://burohappoldmachinelearning.github.io/ADIRO/ontologies/aec_x/)" in text
    assert "[Compare](https://github.com/o/r/compare/aec_x-v2.0.0...aec_x-v2.0.1)" in text
    assert "- [#108](https://github.com/o/r/pull/108) Add a thing" in text and "- `abc1234` a direct commit" in text
    assert "### Added\n- a thing" in text and "https://w3id.org/adiro/aec_x/2.0.1" in text


def test_render_a_first_release_has_no_compare_or_pr_list():
    text = rn.render("aec_x", "1.0.0", None, "notes", [], "o/r")
    assert "**First release**" in text and "Compare" not in text and "Pull requests in this release" not in text
    assert "First tagged release of this module" in text
