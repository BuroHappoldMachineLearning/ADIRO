"""Tests for the release-cut helper (scripts/prepare_release.py, #99)."""
import sys
from pathlib import Path

import pytest

pytest.importorskip("rdflib")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import prepare_release as pr  # noqa: E402

HEADER = """@prefix : <https://w3id.org/adiro/aec_x#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
<https://w3id.org/adiro/aec_x> a owl:Ontology ;
    owl:versionIRI <https://w3id.org/adiro/aec_x/1.0.0> ;
    owl:versionInfo "1.0.0" .
:A a owl:Class .
"""
CHANGELOG = """# Changelog — aec_x

## [Unreleased]

_Pending changes accumulate here. `owl:versionInfo` / `owl:versionIRI` are bumped only at a release cut._
{entry}
## [1.0.0] — 2026-01-01

First release.
"""
ENTRY = "\n### Added\n- A new thing.\n"


def make_repo(tmp_path, src_extra="", entry="", released=True, crlf=False):
    (tmp_path / "src").mkdir()
    (tmp_path / "changelogs").mkdir()
    (tmp_path / "src" / "aec_x.ttl").write_text(HEADER + src_extra, encoding="utf-8", newline="")
    if released:
        snap = tmp_path / "versions" / "aec_x" / "1.0.0"
        snap.mkdir(parents=True)
        (snap / "aec_x.ttl").write_text(HEADER, encoding="utf-8", newline="")
    text = CHANGELOG.format(entry=entry)
    if not released:
        text = text.split("## [1.0.0]")[0]
    if crlf:
        text = text.replace("\n", "\r\n")
    (tmp_path / "changelogs" / "aec_x.md").write_bytes(text.encode("utf-8"))
    (tmp_path / "CHANGELOG.md").write_text("| `aec_x` | 1.0.0 | [c](c.md) |\n\nNo release yet.\n", encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text("versions (currently `aec_x` 1.0.0;\n`aec_y` 9.9.9). Rest.\n", encoding="utf-8")
    return tmp_path


def test_nothing_pending_when_unchanged(tmp_path):
    assert pr.plan(make_repo(tmp_path)) == []


def test_addition_is_minor(tmp_path):
    (e,) = pr.plan(make_repo(tmp_path, ":B a owl:Class .\n", ENTRY))
    assert (e["released"], e["next"], e["bump"], e["changelog_empty"]) == ("1.0.0", "1.1.0", "minor", False)


def test_removal_is_major(tmp_path):
    repo = make_repo(tmp_path)
    (repo / "src" / "aec_x.ttl").write_text(HEADER.replace(":A a owl:Class .\n", ""), encoding="utf-8")
    (e,) = pr.plan(repo)
    assert (e["next"], e["bump"]) == ("2.0.0", "major")
    assert e["changelog_empty"] and any(d["type"] == "TERM_REMOVED" for d in e["deltas"])


def test_apply_cuts_the_release_and_is_idempotent(tmp_path):
    repo = make_repo(tmp_path, ":B a owl:Class .\n", ENTRY)
    pr.apply_plan(repo, pr.plan(repo), "2026-10-09")

    ttl = (repo / "src" / "aec_x.ttl").read_text(encoding="utf-8")
    assert 'owl:versionInfo "1.1.0"' in ttl and "aec_x/1.1.0>" in ttl and "aec_x/1.0.0>" not in ttl

    cl = (repo / "changelogs" / "aec_x.md").read_text(encoding="utf-8")
    assert cl.index("## [Unreleased]") < cl.index("_Pending") < cl.index("## [1.1.0] — 2026-10-09") < cl.index("- A new thing.")
    assert pr.unreleased_body(cl) == ""  # a fresh, empty [Unreleased] is left behind

    assert "| `aec_x` | 1.1.0 |" in (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "(currently `aec_x` 1.1.0)." in (repo / "AGENTS.md").read_text(encoding="utf-8")

    assert pr.plan(repo) == []  # nothing left pending once the cut is in
    assert pr.tags_to_create(repo, tags=set()) == ["aec_x-v1.1.0"]
    assert pr.tags_to_create(repo, tags={"aec_x-v1.1.0"}) == []


def test_first_release_keeps_declared_version(tmp_path):
    repo = make_repo(tmp_path, entry=ENTRY, released=False)
    (e,) = pr.plan(repo)
    assert (e["released"], e["next"], e["bump"]) == (None, "1.0.0", "initial")
    pr.apply_plan(repo, [e], "2026-10-09")
    assert 'owl:versionInfo "1.0.0"' in (repo / "src" / "aec_x.ttl").read_text(encoding="utf-8")
    assert pr.plan(repo) == []
    assert pr.tags_to_create(repo, tags=set()) == ["aec_x-v1.0.0"]


def test_crlf_changelog_keeps_its_line_endings(tmp_path):
    repo = make_repo(tmp_path, ":B a owl:Class .\n", ENTRY, crlf=True)
    pr.apply_plan(repo, pr.plan(repo), "2026-10-09")
    raw = (repo / "changelogs" / "aec_x.md").read_bytes().decode("utf-8")
    assert "\r\n## [1.1.0] — 2026-10-09\r\n\r\n" in raw
    assert "\n" not in raw.replace("\r\n", "")


def test_body_flags_an_empty_changelog_and_carries_the_marker(tmp_path):
    repo = make_repo(tmp_path, ":B a owl:Class .\n")  # change with no changelog entry
    text = pr.body(pr.plan(repo), repo)
    assert text.startswith(pr.MARKER) and "| `aec_x` | 1.0.0 | **1.1.0** | MINOR |" in text
    assert "No `[Unreleased]` changelog entry for: `aec_x`" in text


def test_body_has_no_warning_when_the_changelog_is_filled_in(tmp_path):
    repo = make_repo(tmp_path, ":B a owl:Class .\n", ENTRY)
    text = pr.body(pr.plan(repo), repo)
    assert "No `[Unreleased]`" not in text and "- A new thing." in text


def set_overrides(repo, overrides):
    import json

    (repo / "config").mkdir(exist_ok=True)
    (repo / "config" / "release_overrides.json").write_text(json.dumps(overrides), encoding="utf-8")


def test_override_can_raise_the_bump(tmp_path):
    repo = make_repo(tmp_path, ":B a owl:Class .\n", ENTRY)  # classifier: MINOR
    set_overrides(repo, {"aec_x": "major"})
    (e,) = pr.plan(repo)
    assert (e["next"], e["bump"], e["override"]) == ("2.0.0", "major", "raised from MINOR")
    assert "**override:** raised from MINOR" in pr.body([e], repo)


def test_override_cannot_lower_the_bump(tmp_path):
    repo = make_repo(tmp_path, entry=ENTRY)
    (repo / "src" / "aec_x.ttl").write_text(HEADER.replace(":A a owl:Class .\n", ""), encoding="utf-8")  # MAJOR
    set_overrides(repo, {"aec_x": "patch"})
    (e,) = pr.plan(repo)
    assert (e["next"], e["bump"]) == ("2.0.0", "major") and "no effect" in e["override"]


def test_hold_leaves_the_module_out_and_says_so(tmp_path):
    repo = make_repo(tmp_path, ":B a owl:Class .\n", ENTRY)
    set_overrides(repo, {"aec_x": "hold"})
    assert pr.plan(repo) == []
    (h,) = pr.held(repo)
    assert (h["module"], h["next"]) == ("aec_x", "1.1.0")
    assert "Held back" in pr.body([], repo, [h]) and "`aec_x` (would be 1.1.0, MINOR)" in pr.body([], repo, [h])


def test_a_bump_override_is_consumed_by_the_cut_but_hold_stays(tmp_path):
    import json

    repo = make_repo(tmp_path, ":B a owl:Class .\n", ENTRY)
    set_overrides(repo, {"aec_x": "major"})
    pr.apply_plan(repo, pr.plan(repo), "2026-10-09")
    assert json.loads((repo / "config" / "release_overrides.json").read_text(encoding="utf-8")) == {}
    set_overrides(repo, {"aec_x": "hold"})
    pr.apply_plan(repo, [], "2026-10-09")  # nothing released: a hold is left alone
    assert json.loads((repo / "config" / "release_overrides.json").read_text(encoding="utf-8")) == {"aec_x": "hold"}


def test_override_on_a_first_release_has_no_effect(tmp_path):
    repo = make_repo(tmp_path, entry=ENTRY, released=False)
    set_overrides(repo, {"aec_x": "major"})
    (e,) = pr.plan(repo)
    assert e["next"] == "1.0.0" and "no effect" in e["override"]


@pytest.mark.parametrize("bad", [{"aec_nope": "minor"}, {"aec_x": "bogus"}, {"aec_x": True}])
def test_invalid_overrides_fail_loudly(tmp_path, bad):
    repo = make_repo(tmp_path)
    set_overrides(repo, bad)
    with pytest.raises(ValueError, match="release_overrides.json"):
        pr.plan(repo)
