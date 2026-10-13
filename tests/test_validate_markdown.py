"""The 'Repo-specific checks' section of the QC comment (scripts/validate_ontology.py write_markdown, #130)."""
import sys
from pathlib import Path

import pytest

pytest.importorskip("rdflib")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import validate_ontology as vo  # noqa: E402


def render(tmp_path, results):
    out = tmp_path / "validate.md"
    vo.write_markdown(results, out)
    return out.read_text(encoding="utf-8")


def test_a_clean_run_is_one_line_and_has_no_table(tmp_path):
    text = render(tmp_path, [("aec_a", [], []), ("aec_b", [], [])])
    assert "All 2 module(s) pass" in text and "| Module |" not in text


def test_findings_expand_in_their_own_column_of_the_row(tmp_path):
    text = render(tmp_path, [
        ("aec_clean", [], []),
        ("aec_warned", [], ["first warning", "second warning"]),
        ("aec_broken", ["a blocking error"], []),
    ])
    rows = {line.split("|")[1].strip(): line for line in text.splitlines() if line.startswith("| ") and "`" in line}
    assert "| Module | Errors | Warnings | Findings |" in text and "|---|--:|--:|:--|" in text  # counts right, findings left
    assert rows["✅&nbsp;`aec_clean`"].endswith("| 0 | 0 |  |")  # the icon is tied to the name with a non-breaking space
    warned = rows["⚠️&nbsp;`aec_warned`"]
    assert "| 0 | 2 | <details><summary>Show</summary>⚠️ first warning<br>⚠️ second warning</details> |" in warned
    broken = rows["⛔&nbsp;`aec_broken`"]
    assert "| 1 | 0 | <details><summary>Show</summary>⛔ a blocking error</details> |" in broken
    mixed = render(tmp_path, [("aec_both", ["an error"], ["a warning"])])
    assert "<details><summary>Show</summary>⛔ an error<br>⚠️ a warning</details>" in mixed  # errors first, one dropdown
    assert "<summary>Details</summary>" not in text  # no separate block further down
    assert "**1 error(s), 2 warning(s).** Errors block; warnings are advisory." in text


def test_an_iri_in_angle_brackets_a_pipe_and_a_newline_cannot_break_the_table(tmp_path):
    text = render(tmp_path, [("aec_x", [], ["owl:priorVersion <https://w3id.org/adiro/aec_x/1.0.0> a | b\nsecond line"])])
    row = next(line for line in text.splitlines() if "`aec_x`" in line)
    assert "&lt;https://w3id.org/adiro/aec_x/1.0.0&gt;" in row  # shown, not swallowed as an HTML tag
    assert "<https" not in row and "a &#124; b second line" in row
    assert row.count("|") == 5  # leading, three separators, trailing: the pipe in the finding did not add a cell


def test_the_undescribed_terms_warning_links_the_backlog_and_says_how_to_list_every_term(tmp_path):
    (tmp_path / "src").mkdir()
    ttl = tmp_path / "src" / "aec_x.ttl"
    ttl.write_text(
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
        "<https://w3id.org/adiro/aec_x> a owl:Ontology ;\n"
        "    owl:versionIRI <https://w3id.org/adiro/aec_x/1.0.0> ;\n"
        '    owl:versionInfo "1.0.0" .\n'
        "<https://w3id.org/adiro/aec_x#A> a owl:Class .\n",
        encoding="utf-8",
    )
    _, errors, warnings = vo.validate_ontology(ttl)
    (msg,) = [w for w in warnings if "have no rdfs:comment" in w]
    assert "[#87](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/87)" in msg
    assert "`LIST_UNDESCRIBED=1 uv run python scripts/validate_ontology.py` lists every term." in msg
