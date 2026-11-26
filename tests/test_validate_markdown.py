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
    assert text.startswith("### Important checks\n\n| Module |")  # the table follows the heading directly
    assert "Executed via" not in text and "blocks too" not in text  # the note lives in the collapsed About section
    assert "error(s)" not in text and "Errors block" not in text  # the table already says it


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
    (msg,) = [w for w in warnings if "have no skos:definition" in w]
    assert "[#87](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/87)" in msg
    assert "`LIST_UNDESCRIBED=1 uv run python scripts/validate_ontology.py` lists every term." in msg


MODULE = (
    "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
    "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n"
    "@prefix skos: <http://www.w3.org/2004/02/skos/core#> .\n"
    "<https://w3id.org/adiro/aec_x> a owl:Ontology ;\n"
    "    owl:versionIRI <https://w3id.org/adiro/aec_x/1.0.0> ;\n"
    '    owl:versionInfo "1.0.0" .\n'
)


def _module(tmp_path, terms):
    (tmp_path / "src").mkdir(exist_ok=True)
    ttl = tmp_path / "src" / "aec_x.ttl"
    ttl.write_text(MODULE + terms, encoding="utf-8")
    return ttl


def test_a_term_that_defines_itself_in_rdfs_comment_is_reported_as_not_yet_split_and_is_not_undescribed(tmp_path):
    ttl = _module(tmp_path, '<https://w3id.org/adiro/aec_x#A> a owl:Class ; rdfs:comment "Old style." .\n')
    _, errors, warnings = vo.validate_ontology(ttl)
    (msg,) = [w for w in warnings if "no skos:definition: A" in w]
    assert "[#273](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/273)" in msg
    assert not any("have no skos:definition (nor" in w for w in warnings) and not errors


def test_a_term_with_a_skos_definition_is_split_whatever_commentary_it_also_carries(tmp_path):
    ttl = _module(tmp_path, '<https://w3id.org/adiro/aec_x#A> a owl:Class ; skos:definition "What A is." ; rdfs:comment "Why." .\n')
    _, errors, warnings = vo.validate_ontology(ttl)
    assert not any("still carry their definition" in w or "have no skos:definition" in w for w in warnings) and not errors


def test_enforce_definitions_makes_the_unsplit_terms_an_error(tmp_path, monkeypatch):
    ttl = _module(tmp_path, '<https://w3id.org/adiro/aec_x#A> a owl:Class ; rdfs:comment "Old style." .\n')
    monkeypatch.setenv("ENFORCE_DEFINITIONS", "1")
    ok, errors, _ = vo.validate_ontology(ttl)
    assert not ok and any("still carry their definition in rdfs:comment" in e for e in errors)


def test_a_declaration_of_another_modules_term_is_not_a_term_to_define_here(tmp_path):
    ttl = _module(tmp_path, '<https://w3id.org/adiro/adiro_y#P> a owl:ObjectProperty .\n'
                            '<https://w3id.org/adiro/aec_x#A> a owl:Class .\n')
    _, _, warnings = vo.validate_ontology(ttl)
    (msg,) = [w for w in warnings if "have no skos:definition (nor" in w]
    assert msg.startswith("1 term(s)") and "A" in msg and "P" not in msg.split(":")[1]


# #298: a deprecated term or module cannot be fixed without releasing it again, so the definition checks skip it

DEPRECATED_MODULE = MODULE.replace('    owl:versionInfo "1.0.0" .\n', '    owl:versionInfo "1.0.0" ;\n    owl:deprecated true .\n')


def test_a_deprecated_stub_that_points_to_its_replacement_is_not_reported_as_unsplit(tmp_path):
    ttl = _module(tmp_path, '<https://w3id.org/adiro/aec_x#Old> a owl:Class ; rdfs:comment "Deprecated: use New." ;\n'
                            '    owl:deprecated true .\n'
                            '<https://w3id.org/adiro/aec_x#Live> a owl:Class ; rdfs:comment "Old style." .\n')
    _, _, warnings = vo.validate_ontology(ttl)
    (msg,) = [w for w in warnings if "still carry their definition" in w]
    assert msg.startswith("1 term(s)") and "Live" in msg and "Old" not in msg


def test_a_deprecated_stub_with_no_text_at_all_is_still_reported_as_undescribed(tmp_path):
    ttl = _module(tmp_path, '<https://w3id.org/adiro/aec_x#Old> a owl:Class ; owl:deprecated true .\n')
    _, _, warnings = vo.validate_ontology(ttl)
    (msg,) = [w for w in warnings if "have no skos:definition (nor" in w]
    assert "Old" in msg


def test_the_terms_of_a_deprecated_module_are_not_terms_to_define(tmp_path):
    (tmp_path / "src").mkdir()
    ttl = tmp_path / "src" / "aec_x.ttl"
    ttl.write_text(DEPRECATED_MODULE + '<https://w3id.org/adiro/aec_x#A> a owl:Class ; rdfs:comment "Old style." .\n'
                   '<https://w3id.org/adiro/aec_x#B> a owl:Class .\n', encoding="utf-8")
    _, errors, warnings = vo.validate_ontology(ttl)
    assert not any("still carry their definition" in w or "have no skos:definition" in w for w in warnings) and not errors


# --- compared with the base branch (#311) ---------------------------------------------------------------------------

def against(tmp_path, results, base, renames=None):
    out = tmp_path / "validate.md"
    vo.write_markdown(results, out, base=base, renames=renames or {})
    return out.read_text(encoding="utf-8")


def table_rows(text):
    """The main table's module rows (the backlog block's rows come after its <summary>)."""
    main = text.split("<details><summary>Backlog")[0]
    return [line for line in main.splitlines() if line.startswith("| ") and "`" in line]


def test_an_unchanged_module_has_no_row_and_its_warnings_go_to_the_collapsed_backlog(tmp_path):
    text = against(tmp_path, [("adiro_a", [], ["w1", "w2"]), ("adiro_b", [], [])],
                   {"adiro_a": ([], ["w1", "w2"]), "adiro_b": ([], [])})
    assert table_rows(text) == [] and "This pull request changes no finding" in text
    assert "<details><summary>Backlog, unchanged by this pull request: 2 warning(s) in 1 module(s)</summary>" in text
    assert "`adiro_a` | 2 | <details><summary>Show</summary>⚠️ w1<br>⚠️ w2</details> |" in text
    assert "adiro_b" not in text, "a clean, unchanged module is not listed"


def test_a_new_warning_gets_a_row_naming_it_and_the_rest_stays_in_the_backlog(tmp_path):
    text = against(tmp_path, [("adiro_a", [], ["old", "new"])], {"adiro_a": ([], ["old"])})
    (row,) = table_rows(text)
    assert row.startswith("| ⚠️&nbsp;`adiro_a` | 0 | 1 → 2 |")
    assert "⚠️ 🆕 new" in row and "🆕 old" not in row and "and 1 unchanged warning(s), in the backlog below" in row
    assert "1 warning(s) in 1 module(s)" in text


def test_a_resolved_warning_is_shown_and_counted(tmp_path):
    text = against(tmp_path, [("adiro_a", [], ["kept"])], {"adiro_a": ([], ["kept", "fixed"])})
    (row,) = table_rows(text)
    assert row.startswith("| ✅&nbsp;`adiro_a` | 0 | 2 → 1 |") and "✔️ resolved: fixed" in row


def test_an_error_is_shown_even_when_the_base_had_it(tmp_path):
    text = against(tmp_path, [("adiro_a", ["broken"], [])], {"adiro_a": (["broken"], [])})
    (row,) = table_rows(text)
    assert row.startswith("| ⛔&nbsp;`adiro_a` | 1 | 0 |") and "⛔ broken" in row and "🆕" not in row


def test_a_renamed_module_is_compared_with_its_predecessor(tmp_path):
    base = {"adiro_old": ([], ["https://w3id.org/adiro/adiro_old#A has no definition", "changelogs/adiro_old.md was not changed"])}
    renames = {"adiro_new": "adiro_old"}
    text = against(tmp_path, [("adiro_new", [], ["https://w3id.org/adiro/adiro_new#A has no definition"])], base, renames)
    (row,) = table_rows(text)
    assert "✔️ resolved: changelogs/adiro_new.md was not changed" in row, "only what the pull request changed"
    assert "🆕" not in row, "the inherited finding is not new"


def test_a_new_module_has_no_base_and_shows_everything(tmp_path):
    text = against(tmp_path, [("adiro_new", [], ["w"])], {})
    (row,) = table_rows(text)
    assert "⚠️ 🆕 w" in row


def test_no_base_findings_gives_today_s_table_and_says_the_comparison_did_not_run(tmp_path):
    missing = tmp_path / "none.json"
    assert vo.read_base_findings(missing) is None
    (tmp_path / "bad.json").write_text("not json", encoding="utf-8")
    assert vo.read_base_findings(tmp_path / "bad.json") is None
    out = tmp_path / "validate.md"
    vo.write_markdown([("adiro_a", [], ["w"])], out, base=None, base_missing=True)
    text = out.read_text(encoding="utf-8")
    assert "The comparison with the base branch did not run" in text and "`adiro_a` | 0 | 1 |" in text


def test_the_json_findings_round_trip(tmp_path):
    path = tmp_path / "findings.json"
    vo.write_json([("adiro_a", ["e"], ["w"])], path)
    assert vo.read_base_findings(path) == {"adiro_a": (["e"], ["w"])}


def test_the_workflow_compares_with_the_base_branch():
    workflow = (Path(__file__).resolve().parent.parent / ".github" / "workflows" / "ontology-reasoning.yml").read_text(encoding="utf-8")
    base_step = workflow.split("the base branch's findings")[1].split("- name:")[0]
    assert "continue-on-error: true" in base_step and '--json "$RUNNER_TEMP/base-findings.json"' in base_step
    assert 'cd "$RUNNER_TEMP/base"' in base_step, "the base's own script, on the base's files"
    assert '--base-findings "$RUNNER_TEMP/base-findings.json"' in workflow


def test_a_module_the_pull_request_removes_shows_its_findings_as_gone(tmp_path):
    """Review of #312: without this row the backlog shrank without a word, and a removal alone read as 'no change'."""
    text = against(tmp_path, [("adiro_a", [], ["w"])], {"adiro_a": ([], ["w"]), "adiro_gone": ([], ["g1", "g2"])})
    (row,) = table_rows(text)
    assert row.startswith("| ✅&nbsp;`adiro_gone` | 0 → 0 | 2 → 0 |") and "✔️ gone with the module: g1" in row
    assert "This pull request changes no finding" not in text


def test_a_renamed_modules_predecessor_is_not_reported_as_removed(tmp_path):
    text = against(tmp_path, [("adiro_new", [], ["w"])], {"adiro_old": ([], ["w"])}, {"adiro_new": "adiro_old"})
    assert "adiro_old" not in text and table_rows(text) == []


# --- readability (#300) ----------------------------------------------------------------------------------------------

def test_a_check_that_is_not_a_module_is_a_line_under_the_table_not_a_row(tmp_path):
    text = render(tmp_path, [("adiro_a", [], ["w"]), ("public-repo names", [], []), ("example image budget", ["too big"], [])])
    table = [l for l in text.splitlines() if l.startswith("| ")]
    assert not any("public-repo" in l or "image budget" in l for l in table)
    assert "- ✅ Public-repo names" in text and "- ⛔ Example image budget: <details><summary>Show</summary>⛔ too big" in text


def test_against_the_base_a_check_that_is_not_a_module_shows_only_when_it_changed_or_has_an_error(tmp_path):
    quiet = against(tmp_path, [("adiro_a", [], []), ("public-repo names", [], [])], {"adiro_a": ([], []), "public-repo names": ([], [])})
    assert "Public-repo names" not in quiet
    loud = against(tmp_path, [("adiro_a", [], []), ("public-repo names", ["leak"], [])], {"adiro_a": ([], []), "public-repo names": ([], [])})
    assert "- ⛔ Public-repo names:" in loud and not any("public-repo" in l for l in table_rows(loud))


def test_every_term_is_named_and_none_is_cut(tmp_path):
    body = "".join(f'<https://w3id.org/adiro/aec_x#T{i}> a owl:Class ; rdfs:comment "Old style." .\n' for i in range(12))
    _, _, warnings = vo.validate_ontology(_module(tmp_path, body))
    (msg,) = [w for w in warnings if "still carry their definition" in w]
    assert all(f"T{i}" in msg for i in range(12)) and "more" not in msg


def test_the_modules_follow_the_suite_order_with_deprecated_ones_last(tmp_path):
    names = ["adiro_facade_discipline", "adiro_provenance", "adiro_domain_common", "adiro_drawing_metadata", "adiro_geometry"]
    for n in names:
        deprecated = "    owl:deprecated true ;\n" if n == "adiro_domain_common" else ""
        (tmp_path / f"{n}.ttl").write_text(
            "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
            f"<https://w3id.org/adiro/{n}> a owl:Ontology ;\n{deprecated}    owl:versionInfo \"1.0.0\" .\n", encoding="utf-8")
    order = [p.stem for p in vo.suite_order([tmp_path / f"{n}.ttl" for n in names])]
    assert order == ["adiro_provenance", "adiro_geometry", "adiro_drawing_metadata", "adiro_facade_discipline", "adiro_domain_common"]
