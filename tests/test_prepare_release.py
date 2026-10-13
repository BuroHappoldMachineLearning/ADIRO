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
    assert 'owl:versionInfo "1.1.0"' in ttl and "owl:versionIRI <https://w3id.org/adiro/aec_x/1.1.0>" in ttl
    assert "owl:versionIRI <https://w3id.org/adiro/aec_x/1.0.0>" not in ttl  # the old IRI is now only a prior version
    assert "owl:priorVersion <https://w3id.org/adiro/aec_x/1.0.0> ;" in ttl

    cl = (repo / "changelogs" / "aec_x.md").read_text(encoding="utf-8")
    assert cl.index("## [Unreleased]") < cl.index("_Pending") < cl.index("## [1.1.0] — 2026-10-09") < cl.index("- A new thing.")
    assert pr.unreleased_body(cl) == ""  # a fresh, empty [Unreleased] is left behind

    assert "| `aec_x` | 1.1.0 |" in (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "(currently `aec_x` 1.1.0)." in (repo / "AGENTS.md").read_text(encoding="utf-8")

    assert pr.plan(repo) == []  # nothing left pending once the cut is in
    assert pr.releases_to_complete(repo) == ["aec_x-v1.1.0"]  # cut merged, snapshot not there yet
    snap = repo / "versions" / "aec_x" / "1.1.0"
    snap.mkdir(parents=True)
    (snap / "aec_x.ttl").write_text("# snapshot", encoding="utf-8")
    assert pr.releases_to_complete(repo) == []  # snapshot landed: the release is complete


def test_first_release_keeps_declared_version(tmp_path):
    repo = make_repo(tmp_path, entry=ENTRY, released=False)
    (e,) = pr.plan(repo)
    assert (e["released"], e["next"], e["bump"]) == (None, "1.0.0", "initial")
    pr.apply_plan(repo, [e], "2026-10-09")
    assert 'owl:versionInfo "1.0.0"' in (repo / "src" / "aec_x.ttl").read_text(encoding="utf-8")
    assert pr.plan(repo) == []
    assert pr.releases_to_complete(repo) == ["aec_x-v1.0.0"]


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


def test_a_release_stays_incomplete_until_its_snapshot_exists(tmp_path):
    # A cut whose Release/tag may already exist but whose snapshot never landed is listed again,
    # so a run that failed half way is recovered by the next run (idempotent completion).
    repo = make_repo(tmp_path, ":B a owl:Class .\n", ENTRY)
    pr.apply_plan(repo, pr.plan(repo), "2026-10-09")
    assert pr.releases_to_complete(repo) == ["aec_x-v1.1.0"]
    assert pr.releases_to_complete(repo) == ["aec_x-v1.1.0"]  # asking twice changes nothing


def test_a_complete_old_release_is_not_listed(tmp_path):
    assert pr.releases_to_complete(make_repo(tmp_path)) == []  # 1.0.0: dated heading and snapshot both present



def test_the_cut_bumps_the_readme_release_links(tmp_path):
    repo = make_repo(tmp_path, ":B a owl:Class .\n", ENTRY)
    (repo / "README.md").write_text(
        '<a href="https://github.com/o/r/releases/tag/aec_x-v1.0.0"><img alt="aec_x"></a>\n'
        '<a href="https://github.com/o/r/releases/tag/aec_other-v9.9.9">other</a>\n',
        encoding="utf-8",
    )
    pr.apply_plan(repo, pr.plan(repo), "2026-10-09")
    text = (repo / "README.md").read_text(encoding="utf-8")
    assert "releases/tag/aec_x-v1.1.0" in text and "aec_x-v1.0.0" not in text
    assert "releases/tag/aec_other-v9.9.9" in text  # a module not in src/ is left alone


def add_archive(repo, version, module="aec_x"):
    folder = repo / "versions" / module / version
    folder.mkdir(parents=True)
    (folder / f"{module}.ttl").write_text(HEADER.replace("1.0.0", version), encoding="utf-8")


def test_archived_versions_are_ordered_numerically_and_a_release_never_names_itself(tmp_path):
    repo = make_repo(tmp_path, released=False)
    for v in ("1.10.0", "1.9.0", "1.2.0"):
        add_archive(repo, v)
    (repo / "versions" / "aec_x" / "not-a-version").mkdir()  # ignored
    assert pr.archived_versions(repo, "aec_x") == ["1.2.0", "1.9.0", "1.10.0"]  # numeric, not alphabetical
    assert pr.prior_version_iris(repo, "aec_x", "1.10.0") == [
        "https://w3id.org/adiro/aec_x/1.2.0",
        "https://w3id.org/adiro/aec_x/1.9.0",
    ]


def test_the_cut_names_every_earlier_archived_version_in_order(tmp_path):
    repo = make_repo(tmp_path, ":B a owl:Class .\n", ENTRY)  # archive 1.0.0 exists
    add_archive(repo, "0.9.0")
    pr.apply_plan(repo, pr.plan(repo), "2026-10-09")
    ttl = (repo / "src" / "aec_x.ttl").read_text(encoding="utf-8")
    first = ttl.index("owl:priorVersion <https://w3id.org/adiro/aec_x/0.9.0> ;")
    second = ttl.index("owl:priorVersion <https://w3id.org/adiro/aec_x/1.0.0> ;")
    assert first < second < ttl.index("owl:versionIRI <https://w3id.org/adiro/aec_x/1.1.0>")
    assert ttl.count("owl:priorVersion") == 2  # never the release itself: it is not archived yet


def test_a_first_release_has_no_prior_versions(tmp_path):
    repo = make_repo(tmp_path, entry=ENTRY, released=False)
    pr.apply_plan(repo, pr.plan(repo), "2026-10-09")
    assert "owl:priorVersion" not in (repo / "src" / "aec_x.ttl").read_text(encoding="utf-8")


def test_priors_are_rewritten_not_appended_and_keep_crlf(tmp_path):
    repo = make_repo(tmp_path)
    ttl = repo / "src" / "aec_x.ttl"
    ttl.write_bytes(ttl.read_bytes().replace(b"\n", b"\r\n"))
    add_archive(repo, "0.9.0")
    assert pr.sync_priors(repo) == ["aec_x"]
    raw = ttl.read_bytes()
    assert b"owl:priorVersion <https://w3id.org/adiro/aec_x/0.9.0> ;\r\n" in raw
    assert raw.count(b"\n") == raw.count(b"\r\n")  # no bare LF introduced
    assert pr.sync_priors(repo) == []  # idempotent
    add_archive(repo, "0.8.0")
    assert pr.sync_priors(repo) == ["aec_x"]
    assert ttl.read_bytes().count(b"owl:priorVersion") == 2


def test_a_prior_version_form_the_script_cannot_rewrite_fails_loudly(tmp_path):
    repo = make_repo(tmp_path)
    ttl = repo / "src" / "aec_x.ttl"
    comma_list = "    owl:priorVersion <https://w3id.org/adiro/aec_x/0.1.0>, <https://w3id.org/adiro/aec_x/0.2.0> ;\n"
    ttl.write_text(ttl.read_text(encoding="utf-8").replace("    owl:versionIRI", comma_list + "    owl:versionIRI"), encoding="utf-8")
    with pytest.raises(ValueError, match="priorVersion"):
        pr.sync_priors(repo)


CHANGES = [("#108", "Add a thing"), ("#99", "Another change"), ("abc1234", "a direct push")]


def test_body_lists_the_merged_prs_per_module_between_the_table_and_the_checklist(tmp_path):
    repo = make_repo(tmp_path, ":B a owl:Class .\n", ENTRY)
    text = pr.body(pr.plan(repo), repo, changes={"aec_x": CHANGES}, repo="o/r")
    assert "### Pull requests in this release" in text and "**`aec_x`** 1.0.0 → 1.1.0" in text
    assert "- [#108](https://github.com/o/r/pull/108) Add a thing" in text
    assert "- [#99](https://github.com/o/r/pull/99) Another change" in text
    assert "- `abc1234` a direct push" in text  # a commit pushed straight to main has no PR
    assert text.index("| `aec_x` |") < text.index("### Pull requests in this release") < text.index("### Before merging")
    assert "a PR merged while this one is open appears here on the next rebuild" in text


def test_body_without_changes_has_no_pr_section(tmp_path):
    repo = make_repo(tmp_path, ":B a owl:Class .\n", ENTRY)
    assert "Pull requests in this release" not in pr.body(pr.plan(repo), repo)


def test_a_module_with_nothing_to_count_from_or_nothing_merged_says_so(tmp_path):
    repo = make_repo(tmp_path, ":B a owl:Class .\n", ENTRY)
    (entry,) = pr.plan(repo)
    assert "its previous release (1.0.0) was not tagged" in pr.body([entry], repo, changes={"aec_x": None}, repo="o/r")
    assert "no merged PR changed the ontology file since the last release" in pr.body([entry], repo, changes={"aec_x": []}, repo="o/r")
    (tmp_path / "first").mkdir()
    first = make_repo(tmp_path / "first", entry=ENTRY, released=False)
    (first_entry,) = pr.plan(first)
    assert "this is its first release" in pr.body([first_entry], first, changes={"aec_x": None}, repo="o/r")


def test_merged_changes_counts_from_the_last_tag_up_to_main(tmp_path, monkeypatch):
    repo = make_repo(tmp_path, ":B a owl:Class .\n", ENTRY)
    monkeypatch.setattr(pr, "_tag_exists", lambda root, tag: tag == "aec_x-v1.0.0")
    seen = []

    def collect(root, repo_name, module, previous, tag):
        seen.append((repo_name, module, previous, tag))
        return [("#5", "x")]

    assert pr.merged_changes(repo, pr.plan(repo), "o/r", collect=collect) == {"aec_x": [("#5", "x")]}
    assert seen == [("o/r", "aec_x", "1.0.0", "HEAD")]  # the release is not tagged yet, so the range ends at main


def test_merged_changes_has_nothing_to_count_from_without_a_previous_tag(tmp_path, monkeypatch):
    def never(*args):
        raise AssertionError("must not look anything up")

    (tmp_path / "first").mkdir()
    first = make_repo(tmp_path / "first", entry=ENTRY, released=False)
    assert pr.merged_changes(first, pr.plan(first), "o/r", collect=never) == {"aec_x": None}
    repo = make_repo(tmp_path, ":B a owl:Class .\n", ENTRY)
    monkeypatch.setattr(pr, "_tag_exists", lambda root, tag: False)  # the previous release was made before tagging began
    assert pr.merged_changes(repo, pr.plan(repo), "o/r", collect=never) == {"aec_x": None}


def test_tag_exists_asks_git(tmp_path):
    import subprocess

    def git(*args):
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.org", *args], cwd=tmp_path, check=True, capture_output=True)

    git("init", "-q")
    (tmp_path / "f").write_text("x", encoding="utf-8")
    git("add", "-A")
    git("commit", "-q", "-m", "c")
    git("tag", "aec_x-v1.0.0")
    assert pr._tag_exists(tmp_path, "aec_x-v1.0.0") and not pr._tag_exists(tmp_path, "aec_x-v2.0.0")
