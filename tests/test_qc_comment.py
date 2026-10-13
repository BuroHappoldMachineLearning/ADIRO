"""The 'Ontology reasoning & QC' PR comment (scripts/qc_comment.py, #130)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import qc_comment as qc  # noqa: E402

HEADER = "Level\tRule Name\tSubject\tProperty\tValue\n"
SUPERCLASS = "INFO\tmissing_superclass\t{subject}\trdfs:subClassOf\t\n"
INFO_ROWS = "".join(SUPERCLASS.format(subject=f"https://w3id.org/adiro/aec_x#C{i}") for i in range(3))
PASSING = HEADER + INFO_ROWS + SUPERCLASS.format(subject="prov:Agent")
VALIDATE = "### Important checks\n\nALL-PASS-LINE\n"


def test_report_rows_are_parsed_with_blank_trailing_values():
    rows = qc.parse_report(PASSING)
    assert len(rows) == 4 and rows[0] == {"level": "INFO", "rule": "missing_superclass",
                                           "subject": "https://w3id.org/adiro/aec_x#C0", "property": "rdfs:subClassOf", "value": ""}
    assert qc.parse_report("") == [] and qc.parse_report(HEADER) == []


def test_an_adiro_iri_is_shown_as_module_and_term_and_anything_else_is_left_alone():
    assert qc.short_subject("https://w3id.org/adiro/aec_domain_common#Discipline") == "aec_domain_common:Discipline"
    assert qc.short_subject("prov:Agent") == "prov:Agent"
    assert qc.short_subject("http://www.opengis.net/ont/geosparql#Geometry") == "http://www.opengis.net/ont/geosparql#Geometry"


def test_a_subject_is_split_into_the_module_or_vocabulary_and_its_term():
    assert qc.split_subject("https://w3id.org/adiro/aec_domain_common#Discipline") == ("aec_domain_common", "Discipline")
    assert qc.split_subject("prov:Agent") == ("prov", "Agent")
    assert qc.split_subject("http://www.opengis.net/ont/geosparql#Geometry") == ("geosparql", "Geometry")
    assert qc.split_subject("something") == ("other", "something")


def test_findings_are_grouped_by_level_and_rule_with_errors_first():
    rows = qc.parse_report(HEADER + "INFO\tr_info\ts\tp\tv\nWARN\tw_rule\ts\tp\tv\nERROR\te_rule\ts\tp\tv\nWARN\tw_rule\ts2\tp\tv\n")
    assert [(lv, rule, len(rs)) for lv, rule, rs in qc.by_rule(rows)] == [("ERROR", "e_rule", 1), ("WARN", "w_rule", 2), ("INFO", "r_info", 1)]


def test_near_duplicate_rows_are_grouped_by_module_and_long_lists_are_cut():
    subjects = [f"https://w3id.org/adiro/aec_x#Class{i:02d}" for i in range(12)] + ["https://w3id.org/adiro/aec_y#Only", "prov:Agent", "prov:Activity"]
    rows = qc.parse_report(HEADER + "".join(SUPERCLASS.format(subject=s) for s in subjects + subjects[:2]))  # two exact duplicates
    lines = qc.preview_lines("missing_superclass", rows)
    assert lines[0].startswith("<i>A class with no asserted superclass")  # what the rule means comes first
    assert "<b>aec_x</b> (12): Class00, Class01, Class02, Class03, Class04, Class05, Class06, Class07 +4 more" in lines
    assert "<b>aec_y</b> (1): Only" in lines
    assert "<b>prov</b> (2): Activity, Agent" in lines
    assert len(lines) == 4  # 17 rows became one line per module plus the explanation


def test_findings_that_carry_a_value_are_listed_one_per_row_and_capped():
    rows = qc.parse_report(HEADER + "".join(f"WARN\tduplicate_label\thttps://w3id.org/adiro/aec_x#T{i}\trdfs:label\tbad | label <x>\n" for i in range(13)))
    lines = qc.preview_lines("duplicate_label", rows)
    assert lines[1] == "aec_x:T0: bad &#124; label &lt;x&gt;"  # an IRI-like value or a pipe cannot break the table
    assert lines[-1] == "+3 more" and len(lines) == 1 + qc.ROWS_PER_RULE + 1


def test_a_rule_without_a_known_explanation_has_none():
    assert qc.preview_lines("some_new_rule", qc.parse_report(HEADER + SUPERCLASS.format(subject="prov:Agent")))[0].startswith("<b>prov</b>")


def test_the_minor_checks_are_one_row_per_rule_with_a_preview():
    text = qc.render("0", "", PASSING, VALIDATE)
    assert "### Minor checks" in text and "Executed via ROBOT for logical and structural QC; the ROBOT report stays advisory." in text
    assert "| Level | Rule | Count | Findings |" in text and "|---|---|--:|:--|" in text
    row = next(line for line in text.splitlines() if line.startswith("| INFO | `missing_superclass`"))
    assert "| 4 | <details><summary>Show</summary>" in row
    assert "<b>aec_x</b> (3): C0, C1, C2" in row and "<b>prov</b> (1): Agent" in row


def test_the_comment_reads_verdict_then_important_then_minor_then_a_collapsed_about_note():
    text = qc.render("0", "", PASSING, VALIDATE, "https://example.org/run/1")
    order = [text.index(marker) for marker in ("### Consistency / satisfiability", "### Important checks", "### Minor checks", "<summary>About these checks</summary>")]
    assert order == sorted(order)
    assert "ALL-PASS-LINE" in text  # the repository's section is embedded as it is
    assert text.index("Whole-suite OWL 2 DL reasoning") > text.index("<summary>About these checks</summary>")  # the intro is collapsed at the bottom
    assert text.rstrip().endswith("</details>")
    assert "[workflow run](https://example.org/run/1)" in text and "`reasoning-out` artifact" in text


def test_the_verbose_count_lines_are_gone_because_the_tables_already_say_it():
    text = qc.render("0", "", PASSING, VALIDATE)
    assert "error(s)" not in text and "INFO findings are only counted" not in text
    assert "Errors block; warnings are advisory" not in text


def test_a_run_with_no_findings_says_so():
    text = qc.render("0", "", HEADER, VALIDATE)
    assert "✅ No findings." in text and "| Level | Rule |" not in text


def test_the_comment_carries_no_internal_tracker_id_or_link():
    text = qc.render("0", "", PASSING, VALIDATE)
    assert "RES-" not in text and "youtrack" not in text.lower()


def test_a_failing_reasoner_shows_its_output_and_says_the_check_fails():
    out = "\n".join(f"line {i}" for i in range(100))
    text = qc.render("1", out, PASSING, None)
    assert "⛔ **Reasoner failed**" in text and "fails the check" in text
    assert "<summary>Reasoner output</summary>" in text
    assert "line 99" in text and "line 40" in text and "line 39" not in text  # the last 60 lines


def test_a_run_with_no_report_says_so_instead_of_inventing_counts():
    text = qc.render("1", "boom", None, None)
    assert "The ROBOT report did not run" in text


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
