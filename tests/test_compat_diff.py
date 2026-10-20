"""Regression tests for the compatibility-diff classifier (scripts/compat_diff.py, RES-67).

Covers the spec's Minimal Test Matrix. Skips cleanly where rdflib is unavailable.
"""
import sys
from pathlib import Path

import pytest

pytest.importorskip("rdflib")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from rdflib import Graph  # noqa: E402
import compat_diff as cd  # noqa: E402

BASE = """@prefix : <https://ex.org/m#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
<https://ex.org/m> a owl:Ontology ; owl:versionInfo "1.0.0" .
:A a owl:Class .
:p a owl:ObjectProperty ; rdfs:domain :A ; rdfs:range :A .
"""
R0 = BASE + ':A rdfs:subClassOf [ a owl:Restriction ; owl:onProperty :p ; owl:minCardinality "0"^^xsd:nonNegativeInteger ] .\n'
R1 = BASE + ':A rdfs:subClassOf [ a owl:Restriction ; owl:onProperty :p ; owl:minCardinality "1"^^xsd:nonNegativeInteger ] .\n'


def _deltas(old_ttl, new_ttl):
    def syms(ttl):
        g = Graph()
        g.parse(data=ttl, format="turtle")
        return cd.build_symbols(g)

    return cd.compute_deltas(syms(old_ttl), syms(new_ttl))


@pytest.mark.parametrize(
    "name,old,new,expected_type,expected_bump",
    [
        ("add-only", BASE, BASE + ":B a owl:Class .\n", "TERM_ADDED", cd.BUMP_MINOR),
        ("remove", BASE + ":B a owl:Class .\n", BASE, "TERM_REMOVED", cd.BUMP_MAJOR),
        ("type-change", BASE, BASE.replace(":p a owl:ObjectProperty", ":p a owl:DatatypeProperty"), "TYPE_CHANGED", cd.BUMP_MAJOR),
        ("annotation-only", BASE, BASE.replace(":A a owl:Class .", ':A a owl:Class ; rdfs:label "A" .'), "ANNOTATION_CHANGED", cd.BUMP_PATCH),
        ("tighten", R0, R1, "RESTRICTION_TIGHTENED", cd.BUMP_MAJOR),
        ("loosen", R1, R0, "RESTRICTION_LOOSENED", cd.BUMP_MINOR),
    ],
)
def test_matrix(name, old, new, expected_type, expected_bump):
    deltas = _deltas(old, new)
    types = {t for t, _ in deltas}
    assert expected_type in types, f"{name}: expected {expected_type} in {sorted(types)}"
    assert cd.required_bump(deltas) == expected_bump, f"{name}: bump"


def test_no_change_needs_no_bump():
    assert cd.required_bump(_deltas(BASE, BASE)) == cd.BUMP_NONE


def test_declared_bump():
    assert cd.declared_bump("1.0.0", "1.1.0") == cd.BUMP_MINOR
    assert cd.declared_bump("1.0.0", "2.0.0") == cd.BUMP_MAJOR
    assert cd.declared_bump("2.0.0", "2.0.0") == cd.BUMP_NONE
    assert cd.declared_bump("2.0.0", "1.0.0") == "decreased"


def test_apply_bump():
    assert cd.apply_bump("2.0.0", cd.BUMP_MAJOR) == "3.0.0"
    assert cd.apply_bump("1.2.3", cd.BUMP_MINOR) == "1.3.0"
    assert cd.apply_bump("1.2.3", cd.BUMP_PATCH) == "1.2.4"
    assert cd.apply_bump("1.2.3", cd.BUMP_NONE) == "1.2.3"
    assert cd.apply_bump("not-semver", cd.BUMP_MAJOR) is None


def test_prospective_version_in_markdown():
    # add-only against a baseline -> MINOR -> next version bumps the minor.
    # versionInfo not yet bumped (accumulation) -> RELEASE_PENDING, not a warning.
    results = [
        {
            "module": "m", "status": "analyzed", "old_version": "1.0.0",
            "new_version": "1.0.0", "required_bump": cd.BUMP_MINOR,
            "declared_bump": cd.BUMP_NONE, "prospective_version": "1.1.0",
            "verdict": "RELEASE_PENDING", "deltas": [("TERM_ADDED", "https://ex.org/m#B")],
        }
    ]
    md = cd.to_markdown(results)
    assert "1.1.0" in md and "MINOR" in md
    # accumulation forecast is just a table row — no under-bump warning
    assert "Heads-up" not in md


def test_two_section_markdown_this_pr_vs_cumulative():
    cumulative = [{
        "module": "m", "status": "analyzed", "old_version": "1.0.0",
        "new_version": "1.0.0", "required_bump": cd.BUMP_MINOR,
        "declared_bump": cd.BUMP_NONE, "prospective_version": "1.1.0",
        "verdict": "RELEASE_PENDING", "deltas": [("TERM_ADDED", "https://ex.org/m#B")],
    }]
    pr_with_change = [{"module": "m", "deltas": [("TERM_ADDED", "https://ex.org/m#B")], "required_bump": cd.BUMP_MINOR}]
    md = cd.to_markdown(cumulative, pr_with_change)
    assert "### Changes in this PR" in md and "### Next version if released" in md
    assert "TERM_ADDED" in md and "1.1.0" in md

    # a PR that changes no ontology file -> explicit "no changes" in section 1
    md2 = cd.to_markdown(cumulative, [{"module": "m", "deltas": [], "required_bump": cd.BUMP_NONE}])
    assert "makes **no changes**" in md2


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))


def test_a_module_deleted_by_the_pr_diffs_as_all_removed(tmp_path):
    (tmp_path / "src").mkdir()
    base_dir = tmp_path / "base"
    base_dir.mkdir()
    (base_dir / "m.ttl").write_text(BASE, encoding="utf-8")  # in the base, gone from src/
    res = cd.analyze_pr_change(tmp_path, base_dir, "m")
    assert res["required_bump"] == cd.BUMP_MAJOR
    assert {d for d, _ in res["deltas"]} == {"TERM_REMOVED"}
    assert cd.analyze_pr_change(tmp_path, base_dir, "never_existed") is None


def test_a_deleted_module_is_reported_as_removed_against_its_snapshot(tmp_path):
    (tmp_path / "src").mkdir()
    snap = tmp_path / "versions" / "m" / "1.0.0"
    snap.mkdir(parents=True)
    (snap / "m.ttl").write_text(BASE, encoding="utf-8")
    res = cd.analyze_module(tmp_path, "m")
    assert (res["verdict"], res["required_bump"], res["prospective_version"]) == ("MODULE_REMOVED", cd.BUMP_MAJOR, "2.0.0")


def test_ontology_header_annotations_are_a_patch():
    changed = BASE.replace('owl:versionInfo "1.0.0" .', 'owl:versionInfo "1.0.0" ;\n    owl:priorVersion <https://ex.org/m/0.9.0> .')
    deltas = _deltas(BASE, changed)
    assert deltas == [("ONTOLOGY_HEADER_CHANGED", "https://ex.org/m")]
    assert cd.required_bump(deltas) == cd.BUMP_PATCH


def test_a_version_bump_alone_is_not_a_header_change():
    assert _deltas(BASE, BASE.replace('"1.0.0"', '"1.0.1"')) == []  # the release cut owns the version


def test_changing_a_labelling_flag_on_an_existing_term_is_major():
    flag = ':A <https://w3id.org/adiro/aec_drawing_metadata#isComputerVisionLabel> "%s"^^xsd:boolean .\n'
    off, on = BASE + flag % "false", BASE + flag % "true"
    assert _deltas(off, on) == [("LABELLING_CHANGED", "https://ex.org/m#A")]
    assert cd.required_bump(_deltas(off, on)) == cd.BUMP_MAJOR
    assert [d for d, _ in _deltas(BASE, on)] == ["LABELLING_CHANGED"]  # adding the flag to a term that had none counts too
    assert _deltas(on, on) == []
    other = ':A <https://ex.org/other#flag> "true"^^xsd:boolean .\n'  # a flag from another namespace is not tracked
    assert _deltas(BASE, BASE + other) == []


def test_changing_the_example_images_of_a_term_is_an_annotation_change():
    image = ':A <https://w3id.org/adiro/aec_drawing_metadata#exampleImage> <https://w3id.org/adiro/m/exampleImage/A_0%d.png> .\n'
    one, two = BASE + image % 1, BASE + image % 2
    assert _deltas(one, two) == [("ANNOTATION_CHANGED", "https://ex.org/m#A")]
    assert cd.required_bump(_deltas(one, two)) == cd.BUMP_PATCH
    assert [d for d, _ in _deltas(BASE, one)] == ["ANNOTATION_CHANGED"]
    assert _deltas(one, one) == []


def test_the_range_of_an_annotation_property_is_documentation_not_a_breaking_change():
    plain = BASE + ":ap a owl:AnnotationProperty .\n"
    ranged = BASE + ":ap a owl:AnnotationProperty ; rdfs:range xsd:anyURI .\n"
    assert _deltas(plain, ranged) == [("ANNOTATION_CHANGED", "https://ex.org/m#ap")]
    assert cd.required_bump(_deltas(plain, ranged)) == cd.BUMP_PATCH
    # the same change on an object property is still potentially breaking
    obj = BASE + ":q a owl:ObjectProperty .\n"
    obj_ranged = BASE + ":q a owl:ObjectProperty ; rdfs:range :A .\n"
    assert _deltas(obj, obj_ranged) == [("RANGE_CHANGED", "https://ex.org/m#q")]


def test_the_superproperty_of_an_annotation_property_is_documentation_not_a_breaking_change():
    plain = BASE + ":ap a owl:AnnotationProperty .\n:parent a owl:AnnotationProperty .\n"
    sub = BASE + ":ap a owl:AnnotationProperty ; rdfs:subPropertyOf :parent .\n:parent a owl:AnnotationProperty .\n"
    assert _deltas(plain, sub) == [("ANNOTATION_CHANGED", "https://ex.org/m#ap")]
    assert cd.required_bump(_deltas(plain, sub)) == cd.BUMP_PATCH
    obj = BASE + ":q a owl:ObjectProperty .\n:r a owl:ObjectProperty .\n"
    obj_sub = BASE + ":q a owl:ObjectProperty ; rdfs:subPropertyOf :r .\n:r a owl:ObjectProperty .\n"
    assert _deltas(obj, obj_sub) == [("SUPERPROPERTY_CHANGED", "https://ex.org/m#q")]  # still breaking on an object property


def test_an_added_or_removed_import_is_a_patch_and_not_a_header_change():
    with_import = BASE.replace('owl:versionInfo "1.0.0" .', 'owl:versionInfo "1.0.0" ; owl:imports <https://ex.org/other> .')
    added = _deltas(BASE, with_import)
    assert added == [("IMPORTS_CHANGED", "https://ex.org/m")]
    assert cd.required_bump(added) == cd.BUMP_PATCH
    assert _deltas(with_import, BASE) == [("IMPORTS_CHANGED", "https://ex.org/m")]  # removal is the same delta
    assert _deltas(with_import, with_import) == []


# --- what changed and where (#181) --------------------------------------------
def _syms(ttl):
    g = Graph()
    g.parse(data=ttl, format="turtle")
    return cd.build_symbols(g)


def _described(comment):
    return BASE.replace(":A a owl:Class .\n", ':A a owl:Class ;\n    rdfs:label "A" ;\n    rdfs:comment "%s" .\n' % comment)


COMMENTED, RECOMMENDED = _described("one"), _described("two")


def test_the_changed_annotation_is_named():
    assert cd.annotation_details(_syms(COMMENTED), _syms(RECOMMENDED)) == {"https://ex.org/m#A": ["rdfs:comment"]}
    relabelled = COMMENTED.replace('rdfs:label "A"', 'rdfs:label "B"')
    assert cd.annotation_details(_syms(COMMENTED), _syms(relabelled)) == {"https://ex.org/m#A": ["rdfs:label"]}
    assert cd.annotation_details(_syms(COMMENTED), _syms(COMMENTED)) == {}


def test_a_line_is_found_for_the_term_and_for_each_annotation():
    text = RECOMMENDED
    subject, found = cd.locate_lines(text, "https://ex.org/m#A", ["rdfs:comment", "rdfs:label"])
    assert text.splitlines()[subject - 1].startswith(':A a owl:Class')
    assert text.splitlines()[found["rdfs:comment"] - 1].strip().startswith("rdfs:comment")
    assert found["rdfs:label"] == subject + 1  # the line after the first one of the block
    assert cd.locate_lines(text, "https://ex.org/m#Missing", ["rdfs:comment"]) == (None, {})


def test_a_line_is_found_for_a_term_written_over_several_lines():
    text = BASE + ":Z a owl:Class ;\n    rdfs:comment \"x\" ;\n    rdfs:label \"Z\" .\n\n:Y a owl:Class .\n"
    subject, found = cd.locate_lines(text, "https://ex.org/m#Z", ["rdfs:label", "rdfs:comment"])
    lines = text.splitlines()
    assert lines[subject - 1].startswith(":Z a owl:Class")
    assert lines[found["rdfs:label"] - 1].strip().startswith("rdfs:label")
    assert found["rdfs:comment"] == found["rdfs:label"] - 1  # the block ends at the next term, not before


def test_the_markdown_names_the_annotation_and_links_its_line():
    sha = "a" * 40
    links = {"repo": "o/r", "sha": sha, "read": lambda module: RECOMMENDED, "pr": "", "base_repo": "o/r"}
    pr = [{"module": "m", "deltas": [("ANNOTATION_CHANGED", "https://ex.org/m#A")], "required_bump": cd.BUMP_PATCH,
           "details": {"https://ex.org/m#A": ["rdfs:comment"]}}]
    line = cd.locate_lines(RECOMMENDED, "https://ex.org/m#A", ["rdfs:comment"])[1]["rdfs:comment"]
    md = cd.to_markdown([], pr, links)
    assert "ANNOTATION_CHANGED — `A`: `rdfs:comment` (line %d: [file](https://github.com/o/r/blob/%s/src/m.ttl#L%d))" % (line, sha, line) in md
    assert "[diff]" not in md  # no pull request number: only the file link
    # without a link context the annotation is still named, and nothing is linked
    plain = cd.to_markdown([], pr)
    assert "ANNOTATION_CHANGED — `A`: `rdfs:comment`" in plain and "github.com/o/r" not in plain


def test_the_markdown_links_the_line_in_the_pr_diff():
    import hashlib

    sha = "a" * 40
    links = {"repo": "fork/r", "sha": sha, "read": lambda module: RECOMMENDED, "pr": "42", "base_repo": "o/r"}
    pr = [{"module": "m", "deltas": [("ANNOTATION_CHANGED", "https://ex.org/m#A")], "required_bump": cd.BUMP_PATCH,
           "details": {"https://ex.org/m#A": ["rdfs:comment"]}}]
    line = cd.locate_lines(RECOMMENDED, "https://ex.org/m#A", ["rdfs:comment"])[1]["rdfs:comment"]
    md = cd.to_markdown([], pr, links)
    anchor = hashlib.sha256(b"src/m.ttl").hexdigest()  # GitHub's anchor of a file in a PR diff: the SHA-256 of its path
    # the diff is in the base repository's pull request; the file is in the head repository (a fork)
    assert "[diff](https://github.com/o/r/pull/42/changes#diff-%sR%d)" % (anchor, line) in md
    assert "[file](https://github.com/fork/r/blob/%s/src/m.ttl#L%d)" % (sha, line) in md


def test_a_removed_term_links_to_the_old_side_of_the_diff_only():
    import hashlib

    base_text = BASE + ":Gone a owl:Class .\n"
    links = {"repo": "o/r", "sha": "b" * 40, "read": lambda m: BASE, "pr": "7", "base_repo": "o/r",
             "read_base": lambda m: base_text}
    pr = [{"module": "m", "deltas": [("TERM_REMOVED", "https://ex.org/m#Gone")], "required_bump": cd.BUMP_MAJOR}]
    md = cd.to_markdown([], pr, links)
    line = cd.locate_lines(base_text, "https://ex.org/m#Gone")[0]
    assert "TERM_REMOVED — `Gone` (line %d: [diff](https://github.com/o/r/pull/7/changes#diff-%sL%d))" % (
        line, hashlib.sha256(b"src/m.ttl").hexdigest(), line) in md
    assert "[file]" not in md  # no such line in the head commit
    # without the base file, or without a pull request number, a removed term is listed unlinked
    assert "TERM_REMOVED — `Gone`\n" in cd.to_markdown([], pr, {**links, "read_base": None})
    assert "TERM_REMOVED — `Gone`\n" in cd.to_markdown([], pr, {**links, "pr": ""})


def test_a_removed_term_is_not_linked_and_an_unreadable_file_does_not_fail_the_report():
    def broken(module):
        raise OSError("no file")

    pr = [{"module": "m", "deltas": [("TERM_REMOVED", "https://ex.org/m#A"), ("TERM_ADDED", "https://ex.org/m#B")],
           "required_bump": cd.BUMP_MAJOR}]
    md = cd.to_markdown([], pr, {"repo": "o/r", "sha": "b" * 40, "read": broken})
    assert "TERM_REMOVED — `A`" in md and "TERM_ADDED — `B`" in md and "github.com/o/r" not in md
    linked = cd.to_markdown([], pr, {"repo": "o/r", "sha": "b" * 40, "read": lambda m: BASE + ":B a owl:Class .\n"})
    assert "TERM_REMOVED — `A`" in linked  # a removed term has no line in the PR head, and no old file was given
    assert "TERM_ADDED — `B` (line " in linked and "[file](https://github.com/o/r/blob/" + "b" * 40 + "/src/m.ttl#L" in linked


def test_links_come_from_the_environment_only_when_both_values_are_valid(monkeypatch, tmp_path):
    monkeypatch.delenv("COMPAT_LINK_REPO", raising=False)
    monkeypatch.delenv("COMPAT_LINK_SHA", raising=False)
    assert cd.links_from_env(tmp_path) is None
    monkeypatch.setenv("COMPAT_LINK_REPO", "o/r")
    monkeypatch.setenv("COMPAT_LINK_SHA", "not-a-sha")
    assert cd.links_from_env(tmp_path) is None
    monkeypatch.setenv("COMPAT_LINK_SHA", "c" * 40)
    ctx = cd.links_from_env(tmp_path)
    assert ctx["repo"] == "o/r" and ctx["sha"] == "c" * 40
    monkeypatch.setenv("COMPAT_LINK_REPO", "o/r/../x")
    assert cd.links_from_env(tmp_path) is None


def test_the_pull_request_number_and_base_repository_are_taken_only_when_valid(monkeypatch, tmp_path):
    monkeypatch.setenv("COMPAT_LINK_REPO", "fork/r")
    monkeypatch.setenv("COMPAT_LINK_SHA", "d" * 40)
    for name in ("COMPAT_LINK_PR", "COMPAT_LINK_BASE_REPO"):
        monkeypatch.delenv(name, raising=False)
    ctx = cd.links_from_env(tmp_path)
    assert ctx["pr"] == "" and ctx["base_repo"] == "fork/r"  # no number: only the file links
    monkeypatch.setenv("COMPAT_LINK_PR", "180")
    monkeypatch.setenv("COMPAT_LINK_BASE_REPO", "o/r")
    ctx = cd.links_from_env(tmp_path)
    assert ctx["pr"] == "180" and ctx["base_repo"] == "o/r"
    monkeypatch.setenv("COMPAT_LINK_PR", "1; rm -rf")
    assert cd.links_from_env(tmp_path)["pr"] == ""  # not a number: ignored
    monkeypatch.setenv("COMPAT_LINK_PR", "180")
    monkeypatch.setenv("COMPAT_LINK_BASE_REPO", "../x")
    assert cd.links_from_env(tmp_path)["pr"] == ""  # not a repository: the diff links are dropped, not guessed
    (tmp_path / "m.ttl").write_text("x", encoding="utf-8")
    monkeypatch.setenv("COMPAT_LINK_BASE_REPO", "o/r")
    assert cd.links_from_env(tmp_path, tmp_path)["read_base"]("m") == "x"
