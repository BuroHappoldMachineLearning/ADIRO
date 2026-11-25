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


def test_the_executed_via_note_lives_in_the_collapsed_about_section_without_the_confusing_too():
    text = qc.render("0", "", PASSING, VALIDATE)
    about = text[text.index("<summary>About these checks</summary>"):]
    assert "Important checks: executed via `scripts/validate_ontology.py`. The reasoner blocks: consistency, unsatisfiable classes" in about
    assert "including a root change that breaks its dependents." in about
    assert "blocks too" not in text
    important = text[text.index("### Important checks"):text.index("### Minor checks")]
    assert "Executed via" not in important and "executed via" not in important


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


# #299: the findings that only record a deprecation (a stub and the term that replaces it) are left out, counted

def _suite():
    import pytest
    pytest.importorskip("rdflib")
    from rdflib import Graph
    return Graph().parse(format="turtle", data="""
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix o: <https://w3id.org/adiro/old#> .
@prefix n: <https://w3id.org/adiro/new#> .
o:Base a owl:Class ; rdfs:label "Base" .
o:Mention a owl:Class ; rdfs:label "Mention" ; rdfs:subClassOf o:Base ; owl:equivalentClass n:Mention ;
    owl:deprecated true ; dcterms:isReplacedBy n:Mention .
o:Standalone a owl:Class ; rdfs:label "Standalone" ; rdfs:subClassOf o:Mention ;
    owl:deprecated true ; dcterms:isReplacedBy n:Standalone .
n:Mention a owl:Class ; rdfs:label "Mention" .
n:Standalone a owl:Class ; rdfs:label "Standalone" .
o:LiveUser a owl:Class ; rdfs:label "Live user" ; rdfs:subClassOf o:Mention .
o:Other a owl:Class ; rdfs:label "Base" .
""")


O, N = "https://w3id.org/adiro/old#", "https://w3id.org/adiro/new#"
CYCLE = HEADER + "".join([
    f"ERROR\tdeprecated_class_reference\t{O}Mention\trdfs:subClassOf\t{O}Base\n",          # the stub's own superclass
    f"ERROR\tdeprecated_class_reference\t{O}Mention\towl:equivalentClass\t{N}Mention\n",  # the stub and its replacement
    f"ERROR\tdeprecated_class_reference\t{O}Mention\trdfs:subClassOf\t{O}Standalone\n",    # another stub refers to it
    f"ERROR\tdeprecated_class_reference\t{O}Mention\trdfs:subClassOf\t{O}LiveUser\n",      # a LIVE class refers to it
    f"ERROR\tdeprecated_class_reference\tblank node\towl:someValuesFrom\t{O}Mention\n",    # a restriction refers to it
    f"WARN\tequivalent_pair\t{O}Mention\towl:equivalentClass\t{N}Mention\n",
    f"WARN\tduplicate_label\t{O}Mention\trdfs:label\tMention\n",
    f"WARN\tduplicate_label\t{N}Mention\trdfs:label\tMention\n",
    f"WARN\tduplicate_label\t{O}Base\trdfs:label\tBase\n",                                # a real clash: not a replacement
    f"WARN\tduplicate_label\t{O}Other\trdfs:label\tBase\n",
])


def test_a_stubs_own_axioms_and_its_replacement_are_left_out_of_the_deprecated_class_references():
    kept, left_out = qc.leave_out_deprecation_cycle(qc.parse_report(CYCLE), _suite())
    refs = [(r["subject"], r["value"]) for r in kept if r["rule"] == "deprecated_class_reference"]
    assert (f"{O}Mention", f"{O}Base") not in refs and (f"{O}Mention", f"{N}Mention") not in refs
    assert (f"{O}Mention", f"{O}Standalone") not in refs  # Standalone is itself deprecated
    assert left_out["deprecated_class_reference"] == 3


def test_a_live_class_or_a_restriction_that_refers_to_a_deprecated_class_is_still_reported():
    kept, _ = qc.leave_out_deprecation_cycle(qc.parse_report(CYCLE), _suite())
    refs = [(r["subject"], r["value"]) for r in kept if r["rule"] == "deprecated_class_reference"]
    assert refs == [(f"{O}Mention", f"{O}LiveUser"), ("blank node", f"{O}Mention")]


def test_the_equivalence_of_a_stub_and_its_replacement_is_left_out():
    kept, left_out = qc.leave_out_deprecation_cycle(qc.parse_report(CYCLE), _suite())
    assert not [r for r in kept if r["rule"] == "equivalent_pair"] and left_out["equivalent_pair"] == 1


def test_a_stub_and_its_replacement_may_share_a_label_but_another_clash_is_still_reported():
    kept, left_out = qc.leave_out_deprecation_cycle(qc.parse_report(CYCLE), _suite())
    assert sorted(r["subject"] for r in kept if r["rule"] == "duplicate_label") == [f"{O}Base", f"{O}Other"]
    assert left_out["duplicate_label"] == 2


def test_the_comment_says_how_many_findings_were_left_out_and_that_robot_errors_are_advisory():
    text = qc.render("0", None, CYCLE, VALIDATE, suite=_suite())
    minor = text[text.index("### Minor checks"):text.index("<details><summary>About")]
    assert "| ERROR | `deprecated_class_reference` | 2 |" in minor and "equivalent_pair" not in minor
    about = text[text.index("<details><summary>About"):]
    assert "6 ROBOT findings are left out" in about and "only the reasoner blocks" in about


def test_without_the_ontology_nothing_is_left_out():
    text = qc.render("0", None, CYCLE, VALIDATE)
    assert "| ERROR | `deprecated_class_reference` | 5 |" in text and "left out" not in text


def test_robot_may_report_the_equivalence_from_the_replacements_side_and_it_is_still_left_out():
    """ROBOT showed `New equivalentClass Old` for an axiom asserted as `Old equivalentClass New` (checked on ROBOT v1.9.10, the version run_reasoning.sh pins)."""
    report = HEADER + f"WARN\tequivalent_pair\t{N}Mention\towl:equivalentClass\t{O}Mention\n"
    kept, left_out = qc.leave_out_deprecation_cycle(qc.parse_report(report), _suite())
    assert kept == [] and left_out["equivalent_pair"] == 1


def test_when_every_finding_only_records_a_deprecation_the_comment_says_so_beside_no_findings():
    only_cycle = HEADER + f"WARN\tequivalent_pair\t{O}Mention\towl:equivalentClass\t{N}Mention\n"
    text = qc.render("0", None, only_cycle, VALIDATE, suite=_suite())
    assert "✅ No findings. (1 that only record a deprecation are left out; see *About these checks*.)" in text


def test_a_stubs_own_restriction_is_left_out_but_a_live_restriction_on_a_deprecated_property_is_reported():
    """A restriction on a stub gave three rows with ROBOT v1.9.10: its anonymous superclass, the restriction's value and the
    deprecated property it uses (review of #308). The first and the last are the stub's own axioms."""
    report = HEADER + "".join([
        f"ERROR\tdeprecated_class_reference\t{O}Standalone\trdfs:subClassOf\t_:genid42\n",       # the stub's own restriction
        f"ERROR\tdeprecated_property_reference\t{O}Standalone\tinlineReferences\tblank node\n",  # the same, on a deprecated property
        f"ERROR\tdeprecated_class_reference\tblank node\towl:someValuesFrom\t{O}Mention\n",      # cannot be told from a live one
        f"ERROR\tdeprecated_property_reference\t{O}LiveUser\tinlineReferences\tblank node\n",    # a LIVE class uses it
        f"ERROR\tdeprecated_property_reference\t{O}Standalone\tinlineReferences\t{O}Base\n",     # an IRI value: either direction
    ])
    kept, left_out = qc.leave_out_deprecation_cycle(qc.parse_report(report), _suite())
    assert left_out == {"deprecated_class_reference": 1, "deprecated_property_reference": 1}
    assert [(r["subject"], r["value"]) for r in kept] == [
        ("blank node", f"{O}Mention"), (f"{O}LiveUser", "blank node"), (f"{O}Standalone", f"{O}Base")]
