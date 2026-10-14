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
    assert pg.render([], [], "o/r") == ""


def test_render_lists_findings_and_previews():
    url = pg.preview_url("o/r", "feat/x", "aec_x")
    text = pg.render([("undescribed", "`B` (`aec_x`)"), ("closing", "[#7](https://github.com/o/r/issues/7)")], [("aec_x", url)], "o/r")
    assert text.startswith(pg.MARKER)
    assert "**No `rdfs:comment` on 1 term.** Add a short definition in your own words" in text
    assert "- `B` (`aec_x`)" in text
    assert "[ ]" not in text and "recomputes" not in text
    assert "[#7](https://github.com/o/r/issues/7)" in text and "closing keyword that GitHub did not link" in text
    assert "https://alelom.github.io/OntoCanvas/?onto=https%3A%2F%2Fraw.githubusercontent.com%2Fo%2Fr%2Ffeat%2Fx%2Fdocs%2Faec_x.ttl" in text


def test_render_with_only_a_preview_posts_no_comment():
    assert pg.render([], [("aec_x", "https://example.org/p")], "o/r") == ""


def test_render_with_a_finding_lists_it_under_the_title_and_keeps_the_previews():
    text = pg.render([("undescribed", "`B` (`aec_x`)")], [("aec_x", "https://example.org/p")], "o/r")
    assert text.index("## Required improvements") < text.index("- `B` (`aec_x`)") < text.index("### Previews")
    assert "### To do" not in text


def test_findings_of_one_type_share_one_heading_and_the_advice_is_said_once():
    items = [f"`T{i}` (`aec_x`)" for i in range(3)]
    text = pg.render([("undescribed", i) for i in items], [], "o/r")
    assert text.count("Add a short definition in your own words") == 1
    assert "No `rdfs:comment` on 3 terms." in text
    assert "<details>" not in text and all(f"- {i}" in text for i in items)  # 5 or fewer stay in the open


def test_more_than_five_findings_of_a_type_are_collapsed():
    items = [f"`T{i}` (`aec_x`)" for i in range(6)]
    text = pg.render([("undescribed", i) for i in items], [], "o/r")
    assert text.count("<details>") == 1 and "<summary>Show the 6 terms</summary>" in text
    assert text.index("No `rdfs:comment` on 6 terms.") < text.index("<details>") < text.index("- `T0`") < text.index("</details>")
    five = pg.render([("undescribed", i) for i in items[:5]], [], "o/r")
    assert "<details>" not in five


def test_each_issue_type_gets_its_own_group_in_a_fixed_order():
    text = pg.render([("changelog", "`changelogs/aec_x.md`"), ("undescribed", "`A` (`aec_x`)"), ("changelog", "`changelogs/aec_y.md`")],
                     [], "o/r")
    assert text.index("No `rdfs:comment`") < text.index("The ontology changed but 2 changelogs did not")


def test_a_finding_of_an_unregistered_type_is_an_error_not_silently_dropped():
    with pytest.raises(AssertionError):
        pg.render([("no-such-kind", "x")], [], "o/r")


def test_every_issue_type_can_render():
    for kind in pg.kinds("o/r"):
        assert kind.heading(1) and kind.heading(2)
        assert pg.render([(kind.key, "item")], [], "o/r").count("- item") == 1


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


def test_base_edits_made_after_the_branch_point_are_not_attributed_to_the_pr(tmp_path):
    import subprocess

    def git(*args):
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.org", *args], cwd=tmp_path, check=True,
                       capture_output=True)

    (tmp_path / "src").mkdir()
    ttl = tmp_path / "src" / "aec_x.ttl"
    legacy = ':Legacy a owl:Class ; rdfs:label "Legacy" .\n'  # undescribed backlog the PR does not touch
    ttl.write_text(BASE + legacy, encoding="utf-8")
    git("init", "-q", "-b", "main")
    git("add", "-A")
    git("commit", "-q", "-m", "base")
    git("checkout", "-q", "-b", "pr")
    ttl.write_text(BASE + legacy + ':PrTerm a owl:Class ; rdfs:label "Pr term" .\n', encoding="utf-8")
    git("commit", "-q", "-am", "pr adds a term")
    git("checkout", "-q", "main")  # the base moves on after the PR branched
    ttl.write_text(BASE + legacy.replace('"Legacy"', '"Legacy renamed"'), encoding="utf-8")
    git("commit", "-q", "-am", "main adds another term")
    git("checkout", "-q", "pr")

    script = Path(__file__).resolve().parent.parent / "scripts" / "pr_guidance.py"
    out = subprocess.run([sys.executable, str(script), "--root", str(tmp_path), "--base-ref", "main", "--repo", "o/r",
                          "--head-ref", "pr", "--head-sha", "abc"], capture_output=True, text=True, encoding="utf-8").stdout
    assert "PrTerm" in out and "Legacy" not in out  # the base's rename of Legacy is not the PR's change


# --- example images (#145): suggestions, cautions and removed terms -----------------------------------------------

IMG = "@prefix m: <https://w3id.org/adiro/aec_drawing_metadata#> .\n"
PROP = "https://w3id.org/adiro/aec_drawing_metadata#exampleImage"


def test_a_new_class_without_an_example_image_is_suggested_one():
    head = g(BASE + IMG + ':B a owl:Class ; rdfs:label "B" .\n:C a owl:Class ; m:exampleImage <https://w3id.org/adiro/aec_x/exampleImage/C_01.png> .\n')
    assert name(pg.new_classes_without_image(g(BASE), head)) == ["B"]  # C has one, A is not new


def test_only_classes_are_suggested_not_properties():
    head = g(BASE + ":p a owl:ObjectProperty .\n")
    assert pg.new_classes_without_image(g(BASE), head) == []


def test_a_suggestion_alone_posts_a_comment_headed_suggestions_and_links_the_page():
    text = pg.render([("no-example-image", "`B` (`aec_x`)")], [], "o/r")
    assert text.startswith(pg.MARKER) and "## Suggestions" in text and "## Required improvements" not in text
    assert "a suggestion, not a requirement" in text and pg.example_images.PAGE_URL in text


def test_suggestions_come_after_the_required_improvements():
    text = pg.render([("undescribed", "`B` (`aec_x`)"), ("no-example-image", "`B` (`aec_x`)")], [], "o/r")
    assert text.index("## Required improvements") < text.index("### Suggestions")


def test_a_caution_is_a_red_alert_at_the_top_and_posts_a_comment_on_its_own():
    text = pg.render([], [], "o/r", [("exampleimage-renamed", "`aec_drawing_metadata`: removed")])
    assert text.startswith(pg.MARKER + "\n> [!CAUTION]\n> **The `exampleImage` annotation property is removed or renamed**")
    assert "> - `aec_drawing_metadata`: removed" in text and "## Required improvements" not in text
    both = pg.render([("undescribed", "`B` (`aec_x`)")], [], "o/r", [("exampleimage-renamed", "x")])
    assert both.index("[!CAUTION]") < both.index("## Required improvements")


def test_a_caution_of_an_unregistered_type_is_an_error():
    with pytest.raises(AssertionError):
        pg.render([], [], "o/r", [("no-such-caution", "x")])


def test_every_caution_renders_and_has_a_detector():
    for caution in pg.cautions():
        assert caution.title and caution.explanation and callable(caution.detect)
        assert "[!CAUTION]" in pg.render([], [], "o/r", [(caution.key, "item")])


def test_removing_or_renaming_the_example_image_property_is_detected():
    decl = f"@prefix m: <https://w3id.org/adiro/aec_drawing_metadata#> .\nm:exampleImage a owl:AnnotationProperty .\n"
    renamed = "@prefix m: <https://w3id.org/adiro/aec_drawing_metadata#> .\nm:exampleImages a owl:AnnotationProperty .\n"
    base, head = g(PREFIXES + decl), g(PREFIXES + renamed)
    (caution,) = pg.cautions()
    assert len(caution.detect([{"module": "aec_drawing_metadata", "base": base, "head": head}], None)) == 1
    assert caution.detect([{"module": "aec_drawing_metadata", "base": base, "head": base}], None) == []
    assert caution.detect([{"module": "aec_x", "base": g(BASE), "head": g(BASE)}], None) == []


def test_images_of_a_removed_term_still_in_place_are_reported_until_moved_or_taken_down(tmp_path):
    folder = tmp_path / "assets" / "aec_x" / "exampleImage"
    folder.mkdir(parents=True)
    (folder / "Gone_01.png").write_bytes(b"x")
    value = "<https://w3id.org/adiro/aec_x/exampleImage/Gone_01.png>"
    base = g(BASE + IMG + f":Gone a owl:Class ; m:exampleImage {value} .\n")
    head = g(BASE)
    assert pg.removed_term_images(base, head, "aec_x", tmp_path) == ["`Gone`: `Gone_01.png` (`aec_x`)"]
    (folder / "takedowns.txt").write_text("Gone_01.png copyright\n", encoding="utf-8")
    assert pg.removed_term_images(base, head, "aec_x", tmp_path) == []
    (folder / "takedowns.txt").unlink()
    (folder / "Gone_01.png").rename(folder / "moved.png")  # no longer in place
    assert pg.removed_term_images(base, head, "aec_x", tmp_path) == []
    assert pg.removed_term_images(base, base, "aec_x", tmp_path) == []  # the term is not removed
