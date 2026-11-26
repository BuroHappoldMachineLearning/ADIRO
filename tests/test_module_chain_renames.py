"""A module renamed twice: the tooling follows a chain of renames (config/module_renames.json, #171, #281).

The first rename (aec_* -> adiro_*, #171) is covered by test_module_renames.py with one hop. #281 renames three
modules a second time (adiro_common_symbols -> adiro_drawing_symbology, and so on), so the history of one module then runs
through three names. A toy suite proves that each tool that reads the map follows the whole chain before the real rename:

    aec_a (1.0.0, 2.0.0)  ->  adiro_a (3.0.0, and 3.0.1, its final release, deprecated)  ->  adiro_z (enters at 3.0.1)
"""
import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("rdflib")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from rdflib import Graph  # noqa: E402

import check_prior_versions as cpv  # noqa: E402
import compat_diff as cd  # noqa: E402
import migrate_aec_to_adiro as mig  # noqa: E402
import module_renames as mr  # noqa: E402
import ontology_versions as ov  # noqa: E402
import prepare_release as pr  # noqa: E402
import release_badges as rb  # noqa: E402
import release_notes as rn  # noqa: E402
import validate_ontology as vo  # noqa: E402
from test_module_renames import W3ID, ttl, write  # noqa: E402

CHAIN = {"renames": [{"from": "aec_a", "to": "adiro_a", "reason": "test"}, {"from": "adiro_a", "to": "adiro_z", "reason": "test"}]}
DEPRECATED = f"    owl:deprecated true ;\n    dcterms:isReplacedBy <{W3ID}adiro_z> ;\n"
DCTERMS = "@prefix dcterms: <http://purl.org/dc/terms/> .\n"


@pytest.fixture
def repo(tmp_path):
    """The toy suite midway through the second rename: both old names released, the deprecated final release out, the new
    module in src/ beside the old one, declaring the old module's last release."""
    write(tmp_path / "config" / "module_renames.json", json.dumps(CHAIN))
    write(tmp_path / "versions" / "aec_a" / "1.0.0" / "aec_a.ttl", ttl("aec_a", "1.0.0"))
    write(tmp_path / "versions" / "aec_a" / "2.0.0" / "aec_a.ttl", ttl("aec_a", "2.0.0", [("aec_a", "1.0.0")]))
    priors = [("aec_a", "1.0.0"), ("aec_a", "2.0.0")]
    write(tmp_path / "versions" / "adiro_a" / "3.0.0" / "adiro_a.ttl", ttl("adiro_a", "3.0.0", priors))
    final = DCTERMS + ttl("adiro_a", "3.0.1", [*priors, ("adiro_a", "3.0.0")], header=DEPRECATED)
    write(tmp_path / "versions" / "adiro_a" / "3.0.1" / "adiro_a.ttl", final)
    write(tmp_path / "src" / "adiro_a.ttl", final)
    # the new module enters at the old module's last release; the release cut makes it + 1 MAJOR
    write(tmp_path / "src" / "adiro_z.ttl", ttl("adiro_z", "3.0.1", [*priors, ("adiro_a", "3.0.0")]))
    write(tmp_path / "changelogs" / "adiro_a.md", "# Changelog\n\n## [Unreleased]\n\n## [3.0.1]\n\n")
    write(tmp_path / "changelogs" / "adiro_z.md", "# Changelog\n\n## [Unreleased]\n\n### Changed\n\n- Renamed.\n\n")
    return tmp_path


# --- the map --------------------------------------------------------------------------------------------------------

def test_the_map_accepts_a_chain_and_gives_each_name_the_whole_history(repo):
    renames = mr.load(repo)
    assert renames == {"adiro_a": "aec_a", "adiro_z": "adiro_a"}
    assert mr.lineage(renames, "adiro_z") == ["adiro_z", "adiro_a", "aec_a"]
    assert mr.lineage(renames, "adiro_a") == ["adiro_a", "aec_a"]
    for name in ("aec_a", "adiro_a", "adiro_z"):  # whichever end it is given by
        assert mr.names(renames, name) == ["adiro_z", "adiro_a", "aec_a"]
    assert mr.predecessor(renames, "adiro_z") == "adiro_a" and mr.successor(renames, "aec_a") == "adiro_a"


def test_a_chain_is_still_refused_when_it_closes_on_itself_or_forks(tmp_path):
    for entries, problem in (
        ([{"from": "a", "to": "b"}, {"from": "b", "to": "c"}, {"from": "c", "to": "a"}], "cycle"),
        ([{"from": "a", "to": "b"}, {"from": "b", "to": "c"}, {"from": "a", "to": "d"}], "renamed twice"),
        ([{"from": "a", "to": "c"}, {"from": "b", "to": "c"}], "new name of two modules"),
    ):
        write(tmp_path / "config" / "module_renames.json", json.dumps({"renames": entries}))
        with pytest.raises(ValueError, match=problem):
            mr.load(tmp_path)


def test_the_superseded_modules_of_a_chain(repo):
    renames = mr.load(repo)
    assert mr.superseded(renames, ["aec_a", "adiro_a", "adiro_z"]) == {"aec_a", "adiro_a"}
    assert mr.superseded(renames, ["adiro_a", "adiro_z"]) == {"adiro_a"}  # aec_a has left src/
    # both old names: aec_a has left src/ too, and adiro_z carries its line on, so its pages keep being generated (#323)
    assert mr.retired(renames, ["adiro_z"]) == {"aec_a", "adiro_a"}


# --- the compatibility check ----------------------------------------------------------------------------------------

# The final release of the old module says it is deprecated; the new module is a copy of it without that, so the header
# differs by exactly that. It is listed beside the rename (non-breaking) and is the only thing that is.
HEADER = ("ONTOLOGY_HEADER_CHANGED", f"{W3ID}adiro_z")


def test_the_second_rename_is_one_major_change_from_the_old_modules_final_release(repo):
    res = cd.analyze_module(repo, "adiro_z")
    assert res["baseline_module"] == "adiro_a" and res["renamed_from"] == "adiro_a"
    assert res["deltas"] == [("MODULE_RENAMED", f"{W3ID}adiro_z"), HEADER]  # not a wall of removed and added terms
    assert (res["old_version"], res["required_bump"], res["prospective_version"], res["verdict"]) == \
        ("3.0.1", cd.BUMP_MAJOR, "4.0.0", "RELEASE_PENDING")


def test_the_baseline_skips_a_name_that_has_no_release_and_the_terms_are_renamed_twice(repo):
    """If the middle name had no release, the baseline is the first name's, and its IRIs are mapped through both renames."""
    import shutil

    shutil.rmtree(repo / "versions" / "adiro_a")
    write(repo / "src" / "adiro_z.ttl", ttl("adiro_z", "2.0.0", [("aec_a", "1.0.0")]))
    res = cd.analyze_module(repo, "adiro_z")
    assert res["baseline_module"] == "aec_a" and res["deltas"][0] == ("MODULE_RENAMED", f"{W3ID}adiro_z")
    assert all(term.startswith(f"{W3ID}adiro_z") for _, term in res["deltas"]), "no old IRI is left in a delta"
    assert not [d for d, _ in res["deltas"] if d in ("TERM_ADDED", "TERM_REMOVED")], "the terms matched after two renames"
    assert (res["old_version"], res["prospective_version"]) == ("2.0.0", "3.0.0")


def test_what_changed_besides_the_name_is_listed_with_the_second_rename(repo):
    write(repo / "src" / "adiro_z.ttl", ttl("adiro_z", "3.0.1", extra=":Other a owl:Class .\n"))
    deltas = cd.analyze_module(repo, "adiro_z")["deltas"]
    assert deltas[0] == ("MODULE_RENAMED", f"{W3ID}adiro_z")
    assert set(deltas[1:]) == {HEADER, ("TERM_ADDED", f"{W3ID}adiro_z#Other")}


def test_the_pr_that_adds_the_new_module_diffs_it_against_its_predecessor(repo, tmp_path_factory):
    base = tmp_path_factory.mktemp("base")
    write(base / "adiro_a.ttl", (repo / "src" / "adiro_a.ttl").read_text(encoding="utf-8"))  # the base has the old module only
    res = cd.analyze_pr_change(repo, base, "adiro_z")
    assert res["renamed_from"] == "adiro_a" and res["required_bump"] == cd.BUMP_MAJOR
    assert res["deltas"] == [("MODULE_RENAMED", f"{W3ID}adiro_z"), HEADER]


def test_the_pr_that_removes_the_old_module_retires_it(repo, tmp_path_factory):
    base = tmp_path_factory.mktemp("base")
    write(base / "adiro_a.ttl", (repo / "src" / "adiro_a.ttl").read_text(encoding="utf-8"))
    (repo / "src" / "adiro_a.ttl").unlink()
    res = cd.analyze_pr_change(repo, base, "adiro_a")
    assert res["deltas"] == [("MODULE_RETIRED", f"{W3ID}adiro_a")] and res["required_bump"] == cd.BUMP_NONE


def test_the_report_says_which_module_the_new_one_replaces(repo):
    md = cd.to_markdown([cd.analyze_module(repo, "adiro_z")])
    assert "| `adiro_z` | `adiro_a` `3.0.1` | **`4.0.0`** (MAJOR) |" in md and "`adiro_z` replaces `adiro_a`" in md


# --- the release cut and the version history ------------------------------------------------------------------------

def test_the_release_cut_continues_the_numbering_from_the_final_release(repo):
    entries = {e["module"]: e for e in pr.plan(repo)}
    assert set(entries) == {"adiro_z"}  # the old modules are released already and unchanged
    z = entries["adiro_z"]
    assert (z["released_module"], z["released"], z["next"], z["bump"]) == ("adiro_a", "3.0.1", "4.0.0", cd.BUMP_MAJOR)


def test_the_new_module_names_every_release_of_both_old_names(repo):
    expected = [f"{W3ID}aec_a/1.0.0", f"{W3ID}aec_a/2.0.0", f"{W3ID}adiro_a/3.0.0", f"{W3ID}adiro_a/3.0.1"]
    assert pr.prior_version_iris(repo, "adiro_z", "4.0.0") == expected
    pr.apply_plan(repo, pr.plan(repo), "2026-11-17")
    path = repo / "src" / "adiro_z.ttl"
    text = path.read_text(encoding="utf-8")
    assert f"owl:versionIRI <{W3ID}adiro_z/4.0.0>" in text and 'owl:versionInfo "4.0.0"' in text
    assert all(f"owl:priorVersion <{iri}>" in text for iri in expected)
    assert vo.find_prior_version_problems(Graph().parse(str(path), format="turtle"), path) == []


def test_the_prior_version_check_requires_the_releases_of_every_name_in_the_chain(repo):
    path = repo / "src" / "adiro_z.ttl"
    for dropped in (("adiro_a", "3.0.0"), ("aec_a", "1.0.0")):
        priors = [p for p in [("aec_a", "1.0.0"), ("aec_a", "2.0.0"), ("adiro_a", "3.0.0"), ("adiro_a", "3.0.1")] if p != dropped]
        write(path, ttl("adiro_z", "4.0.0", priors))
        problems = vo.find_prior_version_problems(Graph().parse(str(path), format="turtle"), path)
        assert len(problems) == 1 and f"release {dropped[1]} of {dropped[0]} is archived but not named" in problems[0]
    write(path, ttl("adiro_z", "4.0.0", [("aec_a", "1.0.0"), ("aec_a", "2.0.0"), ("adiro_a", "3.0.0"), ("adiro_a", "3.0.1"), ("aec_b", "1.0.0")]))
    problems = vo.find_prior_version_problems(Graph().parse(str(path), format="turtle"), path)
    assert len(problems) == 1 and "must be a version IRI of this ontology" in problems[0]


def test_the_release_notes_compare_with_the_last_tag_of_the_nearest_name_that_has_one(repo):
    tags = {"adiro_a": ["adiro_a-v3.0.0", "adiro_a-v3.0.1"], "aec_a": ["aec_a-v1.0.0", "aec_a-v2.0.0"], "adiro_z": []}
    module, previous, _ = rn.previous_across_renames(repo, "adiro_z", "4.0.0", "", tag_lister=lambda m: tags.get(m, []))
    assert (module, previous) == ("adiro_a", "3.0.1")
    tags["adiro_a"] = []  # the middle name was never tagged, and its changelog names no release: the first name's last tag is the one
    write(repo / "changelogs" / "adiro_a.md", "# Changelog\n\n## [Unreleased]\n\n")
    module, previous, _ = rn.previous_across_renames(repo, "adiro_z", "4.0.0", "", tag_lister=lambda m: tags.get(m, []))
    assert (module, previous) == ("aec_a", "2.0.0")
    notes = rn.render("adiro_z", "4.0.0", "3.0.1", "Renamed.", [], "o/r", True, previous_module="adiro_a")
    assert notes.startswith("**MAJOR release** · `adiro_a` 3.0.1 → `adiro_z` 4.0.0 · ")


def test_the_release_pr_lists_the_changes_since_the_old_names_last_tag(repo, monkeypatch):
    calls = []
    monkeypatch.setattr(pr, "_tag_exists", lambda root, tag: tag == "adiro_a-v3.0.1")
    entries = [e for e in pr.plan(repo) if e["module"] == "adiro_z"]
    pr.merged_changes(repo, entries, "o/r", collect=lambda *a, **k: calls.append((a[2:], k)) or [])
    assert calls == [(("adiro_z", "3.0.1", "HEAD"), {"previous_module": "adiro_a"})]


def test_the_published_check_resolves_each_old_release_under_its_own_name(repo):
    write(repo / "src" / "adiro_z.ttl", ttl("adiro_z", "4.0.0", [("aec_a", "1.0.0"), ("aec_a", "2.0.0"), ("adiro_a", "3.0.0"), ("adiro_a", "3.0.1")]))
    found = {(m, iri, v) for m, iri, v in cpv.prior_versions(repo / "src") if m in ("aec_a", "adiro_a")}
    assert ("aec_a", f"{W3ID}aec_a/2.0.0", "2.0.0") in found and ("adiro_a", f"{W3ID}adiro_a/3.0.1", "3.0.1") in found
    answer = (200, ttl("adiro_a", "3.0.1"))
    assert cpv.problem_with("adiro_a", f"{W3ID}adiro_a/3.0.1", "3.0.1", lambda url: answer) is None


# --- the documentation ----------------------------------------------------------------------------------------------

def test_the_dropdown_lists_the_releases_of_both_old_names_after_the_new_ones(repo):
    earlier = ov.earlier_names(repo, "adiro_z")
    assert earlier == [("adiro_a", ["3.0.1", "3.0.0"]), ("aec_a", ["2.0.0", "1.0.0"])]
    page = ov.selector_html("4.0.0", ["4.0.0"], earlier)
    assert '<a href="../adiro_a/">adiro_a 3.0.1</a>' in page and '<a href="../aec_a/1.0.0/">aec_a 1.0.0</a>' in page
    assert page.index("4.0.0 (latest)") < page.index("adiro_a 3.0.1") < page.index("aec_a 2.0.0")


def test_a_badge_says_deprecated_for_the_old_name_and_not_for_the_new(repo):
    assert rb.badge_json(repo, "adiro_a")["message"] == "3.0.1 (deprecated)"
    assert "deprecated" not in rb.badge_json(repo, "adiro_z")["message"]


# --- the migration of data and links --------------------------------------------------------------------------------

def test_data_and_links_written_against_any_earlier_name_end_at_the_last(repo):
    text = " ".join(f"<{W3ID}{m}#Thing>" for m in ("aec_a", "adiro_a")) + f" <{W3ID}aec_a> <{W3ID}adiro_a/exampleImage/Thing_01.png>"
    out = mig.rewrite_text(text, repo).split()
    assert out == [f"<{W3ID}adiro_z#Thing>", f"<{W3ID}adiro_z#Thing>", f"<{W3ID}adiro_z>", f"<{W3ID}adiro_z/exampleImage/Thing_01.png>"]
    assert mig.rewrite_text(f"<{W3ID}aec_a/2.0.0> <{W3ID}adiro_a/3.0.1>", repo).split() == [f"<{W3ID}aec_a/2.0.0>", f"<{W3ID}adiro_a/3.0.1>"]


def test_the_published_mapping_sends_every_old_iri_to_the_last_name(repo):
    pairs = set(mig.mapping_pairs(repo))
    for old in ("aec_a", "adiro_a"):
        assert (f"{W3ID}{old}", f"{W3ID}adiro_z") in pairs and (f"{W3ID}{old}#Thing", f"{W3ID}adiro_z#Thing") in pairs
    assert not any(new.endswith(("/aec_a", "/adiro_a")) or "adiro_a#" in new or "aec_a#" in new for _, new in pairs)


def test_the_generated_page_of_the_new_module_links_the_pages_of_both_old_names(repo):
    import types

    # generate_docs imports pyLODE at module level; the Markdown pages never call it (as in test_module_renames.py)
    for name in ("pylode", "pylode.profiles", "pylode.profiles.ontpub"):
        sys.modules.setdefault(name, types.ModuleType(name))
    sys.modules["pylode.profiles.ontpub"].__dict__.setdefault("OntPub", object)
    import generate_docs as gd

    gd.generate_ontology_markdown_pages(gd.sort_by_dependency(sorted((repo / "src").glob("*.ttl"))), repo / "docs", repo)
    page = (repo / "docs" / "ontologies" / "adiro_z.md").read_text(encoding="utf-8")
    assert "Version 3.0.1 (latest)" in page
    assert '<a href="../adiro_a/3.0.0/">adiro_a 3.0.0</a>' in page and '<a href="../aec_a/1.0.0/">aec_a 1.0.0</a>' in page


def test_both_old_names_are_retired_once_the_middle_one_leaves_src(repo):
    """#323: when adiro_a leaves src/, aec_a is still retired, because adiro_z carries the line on; so their pages keep being
    generated from their final releases, and neither needs a changelog entry or a fix."""
    (repo / "src" / "adiro_a.ttl").unlink()
    renames = mr.load(repo)
    assert mr.retired(renames, [p.stem for p in (repo / "src").glob("*.ttl")]) == {"aec_a", "adiro_a"}
    assert mr.retired(renames, ["adiro_a", "adiro_z"]) == {"aec_a"}, "while the middle one is there, only the first is retired"
    assert mr.retired(renames, []) == set(), "a line with no module left in src/ is not retired but removed"
