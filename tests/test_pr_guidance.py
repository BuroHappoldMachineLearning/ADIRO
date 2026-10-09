"""Tests for the PR guidance comment (scripts/pr_guidance.py, #106)."""
import sys
from pathlib import Path

import pytest

pytest.importorskip("rdflib")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from rdflib import Graph, URIRef  # noqa: E402

import pr_guidance as pg  # noqa: E402

PREFIXES = """@prefix : <https://w3id.org/adiro/aec_x#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
"""
BASE = PREFIXES + ':A a owl:Class ; rdfs:label "A" ; rdfs:comment "Old." .\n'
HEAD = BASE + ':B a owl:Class ; rdfs:label "B" .\n:C a owl:Class ; rdfs:label "a" ; rdfs:comment "Clash." .\n'


def g(text):
    out = Graph()
    out.parse(data=text, format="turtle")
    return out


def name(terms):
    return [pg.local_name(t) for t in terms]


def test_only_added_or_changed_terms_are_touched():
    assert name(pg.touched_terms(g(BASE), g(HEAD))) == ["B", "C"]
    assert pg.touched_terms(g(HEAD), g(HEAD)) == []
    changed = BASE.replace("Old.", "New.")
    assert name(pg.touched_terms(g(BASE), g(changed))) == ["A"]


def test_undescribed_looks_only_at_the_given_terms():
    head = g(HEAD + ":Old a owl:Class .\n")  # undescribed, but not touched by the PR
    assert name(pg.undescribed(head, pg.touched_terms(g(BASE), head))) == ["B", "Old"]  # Old is new here
    assert name(pg.undescribed(head, [t for t in pg.touched_terms(g(BASE), head) if pg.local_name(t) == "C"])) == []


def test_label_clash_is_case_insensitive_and_names_the_other_term():
    head = g(HEAD)
    clashes = pg.label_clashes(head, pg.touched_terms(g(BASE), head))
    assert {pg.local_name(t): name(o) for t, o in clashes.items()} == {"C": ["A"]}


def test_definition_line_finds_the_term_block():
    assert pg.definition_line(HEAD, URIRef("https://w3id.org/adiro/aec_x#B")) == 5
    assert pg.definition_line(HEAD, URIRef("https://w3id.org/adiro/aec_x#Missing")) is None


def test_an_edit_inside_a_blank_node_restriction_touches_the_owning_class():
    base = PREFIXES + (':A a owl:Class ; rdfs:comment "d" ; rdfs:subClassOf [ a owl:Restriction ; '
                       'owl:onProperty :p ; owl:maxCardinality 1 ] .\n')
    head = base.replace("maxCardinality 1", "maxCardinality 2")
    assert name(pg.touched_terms(g(base), g(head))) == ["A"]
    assert pg.touched_terms(g(base), g(base)) == []  # same restriction, different blank-node ids: untouched


def test_missing_changelog_modules_flags_edits_additions_and_deletions():
    from validate_ontology import missing_changelog_modules as missing
    assert missing(["src/aec_x.ttl"]) == ["aec_x"]
    assert missing(["src/aec_x.ttl", "changelogs/aec_x.md"]) == []  # the release cut moves both together
    assert missing(["src/aec_x.ttl", "changelogs/aec_y.md"]) == ["aec_x"]  # another module's changelog does not count
    assert missing(["changelogs/aec_x.md", "src/aec_x.display.json"]) == []  # not a .ttl change
    assert missing([]) == []


def test_unregistered_closing_only_reports_what_github_missed():
    body = "| Closes #1 | x |\n| Fixes #2, #3 | y |\nResolved #4"
    assert pg.unregistered_closing(body, [1, 4]) == [2]  # "#3" has no keyword of its own
    assert pg.unregistered_closing("no keywords #9", []) == []


def test_render_is_empty_when_there_is_nothing_to_say():
    assert pg.render([{"name": "aec_x", "fixes": [], "preview": None}], [], "o/r") == ""


def test_render_lists_todos_and_previews():
    mods = [{"name": "aec_x", "fixes": ["`B` has no `rdfs:comment`."], "preview": pg.preview_url("o/r", "feat/x", "aec_x")}]
    text = pg.render(mods, [7], "o/r")
    assert text.startswith(pg.MARKER)
    assert "- [ ] `aec_x`: `B` has no `rdfs:comment`." in text
    assert "[#7](https://github.com/o/r/issues/7)" in text
    assert "https://alelom.github.io/OntoCanvas/?onto=https%3A%2F%2Fraw.githubusercontent.com%2Fo%2Fr%2Ffeat%2Fx%2Fdocs%2Faec_x.ttl" in text


def test_render_with_only_a_preview_says_nothing_to_fix():
    text = pg.render([{"name": "aec_x", "fixes": [], "preview": "https://example.org/p"}], [], "o/r")
    assert "Nothing to fix" in text and "### To do" not in text and "### Previews" in text


def test_declares_classes_is_false_for_an_annotation_only_module():
    assert pg.declares_classes(g(HEAD))
    assert not pg.declares_classes(g(PREFIXES + ":p a owl:AnnotationProperty .\n"))


def test_a_failed_base_diff_is_reported_and_blocks_under_enforcement(tmp_path):
    import os
    import subprocess

    script = Path(__file__).resolve().parent.parent / "scripts" / "validate_ontology.py"
    md = tmp_path / "out.md"

    def run(enforce):
        env = {**os.environ, "BASE_REF": "origin/definitely-not-a-ref"}
        if enforce:
            env["ENFORCE_CHANGELOG"] = "1"
        return subprocess.run([sys.executable, str(script), "--markdown", str(md)], env=env, capture_output=True, text=True)

    advisory = run(False)
    assert advisory.returncode == 0 and "changelog check did not run" in md.read_text(encoding="utf-8")
    assert run(True).returncode != 0  # the future gate must not fail open
