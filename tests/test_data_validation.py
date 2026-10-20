"""The data-validation shapes (#168): each rule is shown to accept a conforming graph and to reject a violating one."""
import sys
from pathlib import Path

import pytest

pytest.importorskip("rdflib")
pytest.importorskip("pyshacl")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from rdflib import Graph, URIRef  # noqa: E402
from rdflib.namespace import RDF  # noqa: E402

import validate_data as vd  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PREFIXES = """@prefix : <https://ex.org/d#> .
@prefix metadata: <https://w3id.org/adiro/aec_drawing_metadata#> .
@prefix csymbol: <https://w3id.org/adiro/aec_common_symbols#> .
"""


def check(body):
    return vd.validate(Graph().parse(data=PREFIXES + body, format="turtle"), ROOT)


def messages(body):
    return [r["message"] for r in check(body)]


# --- the inline reference: one drawing identifier, at least one layout identifier -----------------------------------
INLINE_OK = """:ref a metadata:InlineLayoutSheetReference ; metadata:contains :sheet , :l1 , :l3 .
:sheet a metadata:DrawingIdentifierMention .
:l1 a metadata:LayoutIdentifierMention . :l3 a metadata:LayoutIdentifierMention .
"""


def test_a_complete_inline_reference_conforms():
    assert check(INLINE_OK) == []


def test_an_inline_reference_with_two_drawing_identifiers_is_reported():
    two = INLINE_OK + ":other a metadata:DrawingIdentifierMention . :ref metadata:contains :other .\n"
    assert messages(two) == ["An inline layout and sheet reference contains exactly one drawing identifier mention."]


def test_an_inline_reference_with_no_drawing_identifier_is_reported():
    none = """:ref a metadata:InlineLayoutSheetReference ; metadata:contains :l1 .
:l1 a metadata:LayoutIdentifierMention .
"""
    assert messages(none) == ["An inline layout and sheet reference contains exactly one drawing identifier mention."]


def test_an_inline_reference_with_no_layout_identifier_is_reported():
    none = """:ref a metadata:InlineLayoutSheetReference ; metadata:contains :sheet .
:sheet a metadata:DrawingIdentifierMention .
"""
    assert messages(none) == ["An inline layout and sheet reference contains at least one layout identifier mention."]


def test_a_standalone_reference_counts_as_a_drawing_identifier_mention():
    # StandaloneSheetReference is a subclass of DrawingIdentifierMention: the ontology is read as background.
    nested = """:ref a metadata:InlineLayoutSheetReference ; metadata:contains :sheet , :l1 .
:sheet a metadata:StandaloneSheetReference . :l1 a metadata:LayoutIdentifierMention .
"""
    assert check(nested) == []


# --- the reference symbol: at most one drawing identifier ------------------------------------------------------------
def test_a_reference_symbol_with_at_most_one_drawing_identifier_conforms():
    assert check(":s a csymbol:ReferenceSymbol .\n") == []
    assert check(":s a csymbol:ReferenceSymbol ; metadata:contains :m . :m a metadata:DrawingIdentifierMention .\n") == []


def test_a_reference_symbol_with_two_drawing_identifiers_is_reported():
    two = ":s a csymbol:ReferenceSymbol ; metadata:contains :a , :b . :a a metadata:DrawingIdentifierMention . :b a metadata:DrawingIdentifierMention .\n"
    assert messages(two) == ["A reference symbol contains at most one drawing identifier mention."]


# --- a mention has at most one accepted target -----------------------------------------------------------------------
def test_a_mention_with_one_target_conforms_and_with_two_is_reported():
    one = ":m a metadata:DrawingIdentifierMention ; metadata:denotesDrawingSheet :s1 .\n"
    two = one + ":m metadata:denotesDrawingSheet :s2 .\n"
    assert check(one) == []
    assert messages(two) == ["A drawing identifier mention has at most one accepted denotesDrawingSheet target."]


def test_the_rule_reaches_a_standalone_reference_through_its_superclass():
    two = ":m a metadata:StandaloneSheetReference ; metadata:denotesDrawingSheet :s1 , :s2 .\n"
    assert messages(two) == ["A drawing identifier mention has at most one accepted denotesDrawingSheet target."]


def test_a_violation_is_reported_with_its_severity_and_focus():
    result = check(":m a metadata:DrawingIdentifierMention ; metadata:denotesDrawingSheet :s1 , :s2 .\n")[0]
    assert result["severity"] == "Violation" and result["focus"] == "https://ex.org/d#m"
    assert result["path"].endswith("denotesDrawingSheet")


def test_the_command_line_exits_one_on_a_violation_and_zero_otherwise(tmp_path):
    bad, good = tmp_path / "bad.ttl", tmp_path / "good.ttl"
    bad.write_text(PREFIXES + ":m a metadata:DrawingIdentifierMention ; metadata:denotesDrawingSheet :s1 , :s2 .\n", encoding="utf-8")
    good.write_text(PREFIXES + INLINE_OK, encoding="utf-8")
    assert vd.main([str(bad)]) == 1
    assert vd.main([str(good)]) == 0
    assert vd.main([]) == 2


# --- the shape files themselves --------------------------------------------------------------------------------------
def test_every_shape_has_a_message_and_a_severity():
    shapes = vd.load_shapes(ROOT)
    SH = vd.SH
    for shape in shapes.subjects(RDF.type, SH.NodeShape):
        assert shapes.value(shape, SH.severity) is not None, f"{shape} has no sh:severity"
        for prop in shapes.objects(shape, SH.property):
            assert shapes.value(prop, SH.message) is not None, f"a property shape of {shape} has no sh:message"
            # SHACL does not pass a node shape's severity down to its property shapes: without its own, the default
            # (Violation) applies, whatever the node shape says.
            assert shapes.value(prop, SH.severity) == shapes.value(shape, SH.severity), f"a property shape of {shape} has a different or no sh:severity"


def test_every_adiro_term_a_shape_names_exists_in_the_ontology():
    # A shape that names a term the ontology no longer has would silently match nothing.
    ontology = vd.load_ontology(ROOT)
    declared = set(ontology.subjects())
    named = {
        o for s, p, o in vd.load_shapes(ROOT)
        if isinstance(o, URIRef) and str(o).startswith("https://w3id.org/adiro/aec_")
    }
    named |= {p for _, p, _ in vd.load_shapes(ROOT) if str(p).startswith("https://w3id.org/adiro/aec_")}
    assert named, "the shapes name no ADIRO term"
    assert named - declared == set(), f"terms the ontology does not declare: {sorted(named - declared)}"


def test_the_shape_files_follow_the_naming_convention():
    files = vd.shape_files(ROOT)
    assert files, "no shape files"
    assert all(p.name.endswith(".shacl.ttl") for p in files)
    stray = [p.name for p in (ROOT / vd.SHAPES_DIR).iterdir() if p.suffix == ".ttl" and not p.name.endswith(".shacl.ttl")]
    assert stray == [], f"a .ttl in {vd.SHAPES_DIR}/ that is not *.shacl.ttl is never run: {stray}"


# --- UC-01: a drawing has an author (#179) -----------------------------------------------------------------------------
def test_a_drawing_with_an_author_conforms():
    assert check(":d a metadata:DrawingSheet ; metadata:isAuthoredBy :jsmith .\n") == []


def test_a_drawing_with_no_author_is_a_warning_and_never_fails_a_run(tmp_path):
    results = check(":d a metadata:DrawingSheet .\n")
    assert [(r["severity"], r["message"]) for r in results] == [("Warning", "A drawing has at least one recorded author.")]
    data = tmp_path / "d.ttl"
    data.write_text(PREFIXES + ":d a metadata:DrawingSheet .\n", encoding="utf-8")
    assert vd.main([str(data)]) == 0  # a warning is reported; only a violation fails the run


def test_a_drawing_with_no_author_of_its_own_is_read_as_authored_by_its_revisions_authors():
    only_revision = ":d a metadata:DrawingSheet ; metadata:hasRevision :r . :r a metadata:DrawingRevision ; metadata:isAuthoredBy :jsmith .\n"
    assert check(only_revision) == []
    # only the author has the fallback, and a revision that is not linked to the drawing counts for nothing
    checked_only = ":d a metadata:DrawingSheet ; metadata:hasRevision :r . :r a metadata:DrawingRevision ; metadata:isCheckedBy :achen .\n"
    assert [r["severity"] for r in check(checked_only)] == ["Warning"]
    unlinked = ":d a metadata:DrawingSheet . :r a metadata:DrawingRevision ; metadata:isAuthoredBy :jsmith .\n"
    assert [r["severity"] for r in check(unlinked)] == ["Warning"]


def test_the_checker_and_the_approver_are_optional():
    assert check(":d a metadata:DrawingSheet ; metadata:isAuthoredBy :jsmith .\n") == []  # no checker, no approver: no result
