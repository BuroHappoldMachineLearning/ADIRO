"""The 'Ontology reasoning & QC' PR comment (scripts/qc_comment.py, #130)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import qc_comment as qc  # noqa: E402

HEADER = "Level\tRule Name\tSubject\tProperty\tValue\n"
INFO_ROWS = "".join(
    f"INFO\tmissing_superclass\thttps://w3id.org/adiro/aec_x#C{i}\trdfs:subClassOf\t\n" for i in range(3))
PASSING = HEADER + INFO_ROWS + "INFO\tmissing_superclass\tprov:Agent\trdfs:subClassOf\t\n"
VALIDATE = "### 🧪 Repo-specific checks (`scripts/validate_ontology.py`)\n\nALL-PASS-LINE\n"


def test_report_rows_are_parsed_with_blank_trailing_values():
    rows = qc.parse_report(PASSING)
    assert len(rows) == 4 and rows[0] == {"level": "INFO", "rule": "missing_superclass",
                                           "subject": "https://w3id.org/adiro/aec_x#C0", "property": "rdfs:subClassOf", "value": ""}
    assert qc.parse_report("") == [] and qc.parse_report(HEADER) == []


def test_an_adiro_iri_is_shown_as_module_and_term_and_anything_else_is_left_alone():
    assert qc.short_subject("https://w3id.org/adiro/aec_domain_common#Discipline") == "aec_domain_common:Discipline"
    assert qc.short_subject("prov:Agent") == "prov:Agent"
    assert qc.short_subject("http://www.opengis.net/ont/geosparql#Geometry") == "http://www.opengis.net/ont/geosparql#Geometry"


def test_findings_are_counted_by_level_and_by_rule_with_errors_first():
    rows = qc.parse_report(HEADER + "INFO\tr_info\ts\tp\tv\nWARN\tw_rule\ts\tp\tv\nERROR\te_rule\ts\tp\tv\nWARN\tw_rule\ts2\tp\tv\n")
    assert qc.counts(rows) == {"ERROR": 1, "WARN": 2, "INFO": 1}
    assert qc.by_rule(rows) == [("ERROR", "e_rule", 1), ("WARN", "w_rule", 2), ("INFO", "r_info", 1)]
    assert qc.counts([]) == {"ERROR": 0, "WARN": 0, "INFO": 0}  # a missing level reads 0, not absent


def test_a_passing_run_summarises_info_by_rule_instead_of_dumping_rows():
    text = qc.render("0", "", PASSING, VALIDATE, "https://example.org/run/1")
    assert "✅ **Consistent**" in text
    assert "**0 error(s), 0 warning(s), 4 info.**" in text
    assert "| INFO | `missing_superclass` | 4 |" in text
    assert "https://w3id.org/adiro/aec_x#C0" not in text  # the raw INFO rows are not dumped
    assert "INFO findings are only counted here." in text
    assert "[workflow run](https://example.org/run/1)" in text and "`reasoning-out` artifact" in text
    assert "ALL-PASS-LINE" in text  # the repo-specific section is embedded as it is
    assert "<summary>Reasoner output</summary>" not in text


def test_the_comment_carries_no_internal_tracker_id_or_link():
    text = qc.render("0", "", PASSING, VALIDATE)
    assert "RES-" not in text and "youtrack" not in text.lower()


def test_error_and_warn_rows_are_listed_readably_escaped_and_capped():
    rows = HEADER + "".join(f"WARN\tduplicate_label\thttps://w3id.org/adiro/aec_x#T{i}\trdfs:label\tbad | label <x>\n" for i in range(30))
    text = qc.render("0", "", rows, None)
    assert "<summary>ERROR and WARN rows (30)</summary>" in text
    assert "aec_x:T0" in text and "aec_x:T24" in text and "aec_x:T25" not in text  # capped at 25
    assert "… and 5 more." in text
    assert "bad &#124; label &lt;x&gt;" in text  # a pipe or an IRI-like value cannot break the table


def test_a_failing_reasoner_shows_its_output_and_says_the_check_fails():
    out = "\n".join(f"line {i}" for i in range(100))
    text = qc.render("1", out, PASSING, None)
    assert "⛔ **Reasoner failed**" in text and "fails the check" in text
    assert "<summary>Reasoner output</summary>" in text
    assert "line 99" in text and "line 40" in text and "line 39" not in text  # the last 60 lines


def test_a_run_with_no_report_says_so_instead_of_inventing_counts():
    text = qc.render("1", "boom", None, None)
    assert "The ROBOT report did not run" in text and "0 error(s)" not in text


def test_main_reads_the_output_directory(tmp_path, capsysbinary, monkeypatch):
    (tmp_path / "reason.rc").write_text("0\n", encoding="utf-8")
    (tmp_path / "report.tsv").write_text(PASSING, encoding="utf-8")
    (tmp_path / "validate.md").write_text(VALIDATE, encoding="utf-8")
    monkeypatch.setenv("RUN_URL", "https://example.org/run/2")
    qc.main(["--out-dir", str(tmp_path)])
    text = capsysbinary.readouterr().out.decode("utf-8")
    assert "✅ **Consistent**" in text and "https://example.org/run/2" in text and "ALL-PASS-LINE" in text


def test_main_treats_a_missing_reasoner_result_as_a_failure(tmp_path, capsysbinary):
    qc.main(["--out-dir", str(tmp_path)])  # nothing was written: the reasoner step did not complete
    assert "Reasoner failed" in capsysbinary.readouterr().out.decode("utf-8")
