"""Text readings, the failed outcome and the kind of a step (#238): the terms, and CQ Group 11 of the UC-01 ORSD."""
import sys
from pathlib import Path

import pytest

pytest.importorskip("rdflib")
from rdflib import Graph, Namespace  # noqa: E402
from rdflib.namespace import OWL, RDF, RDFS  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_uc01_competency_queries import PREFIXES, recorded_query  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
APROV = Namespace("https://w3id.org/adiro/adiro_provenance#")
PROVENANCE = Graph().parse(ROOT / "src" / "adiro_provenance.ttl", format="turtle")


def test_a_reading_is_an_inferred_entity_with_its_own_outcome_property():
    assert (APROV.TextReading, RDFS.subClassOf, APROV.InferredEntity) in PROVENANCE
    assert PROVENANCE.value(APROV.hasReadingOutcome, RDFS.domain) == APROV.TextReading
    assert PROVENANCE.value(APROV.hasReadingOutcome, RDFS.range) == APROV.AssertionOutcome
    # hasOutcome keeps its domain: a reading is not a field assertion
    assert PROVENANCE.value(APROV.hasOutcome, RDFS.domain) == APROV.FieldAssertion
    assert PROVENANCE.value(APROV.isReadingOf, RDFS.range) is None


def test_the_step_kind_is_a_property_of_a_step_with_a_closed_list_of_values():
    assert PROVENANCE.value(APROV.hasStepKind, RDFS.domain) == APROV.InferenceMeta
    assert (APROV.StepKind, OWL.oneOf, None) in PROVENANCE
    for kind in (APROV.RegionDetection, APROV.TextRecognition, APROV.FieldExtraction):
        assert (kind, RDF.type, APROV.StepKind) in PROVENANCE


RUNS = """@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
:file a aprov:DrawingFile ; aprov:fileName "A101-ground-floor.pdf" .
:p1 a aprov:FilePage ; aprov:belongsToFile :file ; aprov:pageNumber 1 .
:p2 a aprov:FilePage ; aprov:belongsToFile :file ; aprov:pageNumber 2 .
:p3 a aprov:FilePage ; aprov:belongsToFile :file ; aprov:pageNumber 3 .
:d1 a metadata:DrawingSheet ; metadata:drawingIdentifier "ST-101" ; metadata:isOnPage :p1 ; metadata:contains :tb1 , :legend1 .
:tb1 a metadata:Titleblock .
:legend1 a metadata:Legend .

:run1 a prov:Activity ; prov:startedAtTime "2026-10-01T09:00:00Z"^^xsd:dateTime .
:detect1 a aprov:InferenceMeta ; aprov:hasStepKind aprov:RegionDetection ; dcterms:isPartOf :run1 ; prov:used :p1 , :p2 .
:ocr1 a aprov:InferenceMeta ; aprov:hasStepKind aprov:TextRecognition ; dcterms:isPartOf :run1 ; aprov:inferredFrom :p1 .
:r1 a aprov:TextReading ; aprov:isReadingOf :tb1 ; aprov:readText "GROUND FLOOR PLAN  ST-101"@en ; aprov:hasInferenceMeta :ocr1 .
:r2 a aprov:TextReading ; aprov:isReadingOf :p1 ; aprov:hasReadingOutcome aprov:Failed ;
    aprov:errorMessage "timeout after 60 s" ; aprov:hasInferenceMeta :ocr1 .
:r3 a aprov:TextReading ; aprov:isReadingOf :legend1 ; aprov:readText "Ground floor slab" ; aprov:hasInferenceMeta :ocr1 .

:run2 a prov:Activity ; prov:startedAtTime "2026-10-20T09:00:00Z"^^xsd:dateTime .
:ocr2 a aprov:InferenceMeta ; aprov:hasStepKind aprov:TextRecognition ; dcterms:isPartOf :run2 ; prov:used :p1 .
:r4 a aprov:TextReading ; aprov:isReadingOf :p1 ; aprov:readText "Erdgeschoss Grundriss"@de ; aprov:hasInferenceMeta :ocr2 .
"""


def rows(data, marker, *names):
    graph = Graph().parse(data=PREFIXES + data, format="turtle")
    local = lambda v: None if v is None else str(v).rsplit("#", 1)[-1]  # noqa: E731
    return {tuple(local(r[n]) for n in names) for r in graph.query(recorded_query(marker))}


def test_cq_11_1_finds_a_drawing_by_any_text_of_its_title_block_and_not_of_another_region():
    assert rows(RUNS, "# CQ 11.1", "drawing", "identifier") == {("d1", "ST-101")}
    # the legend mentions it too, but a legend is not a title block
    without_titleblock_text = "\n".join(line for line in RUNS.splitlines() if not line.startswith(":r1 "))
    assert rows(without_titleblock_text, "# CQ 11.1", "drawing", "identifier") == set()


def test_cq_11_2_gives_the_latest_reading_of_the_page_and_of_its_title_block_with_language_or_outcome():
    assert rows(RUNS, "# CQ 11.2", "target", "text", "language", "outcome", "error", "run") == {
        # the title block was read by run1 only; the page by run1 (failed) and then by run2, which is the latest
        ("tb1", "GROUND FLOOR PLAN  ST-101", "en", None, None, "run1"),
        ("p1", "Erdgeschoss Grundriss", "de", None, None, "run2"),
    }
    failed_only = RUNS.split(":run2 a prov:Activity")[0]
    assert ("p1", None, None, "Failed", "timeout after 60 s", "run1") in rows(
        failed_only, "# CQ 11.2", "target", "text", "language", "outcome", "error", "run")


def test_cq_11_3_lists_each_page_with_the_runs_that_processed_it():
    assert rows(RUNS, "# CQ 11.3", "number", "run", "status") == {
        ("1", "run1", "Failed"), ("1", "run2", "Read"),
        ("2", "run1", "Processed"),   # searched for a title block, its text not read
        ("3", None, "NotProcessed"),  # no step used it
    }


def test_cq_11_4_lists_the_pages_searched_for_a_title_block_with_none_detected():
    # page 2 was searched and holds no drawing; page 1 has its title block; page 3 was never searched
    assert rows(RUNS, "# CQ 11.4", "file", "number", "run") == {("file", "2", "run1")}
    # a text recognition that used a page is not a search for a title block
    assert rows(RUNS.replace("prov:used :p1 , :p2 .", "prov:used :p1 ."), "# CQ 11.4", "file", "number", "run") == set()


HISTORY = """@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
:d a metadata:DrawingSheet ; metadata:drawingIdentifier "ST-101" .
:read1 a aprov:InferenceMeta ; aprov:inferredWith :llm ; aprov:inferredAt "2026-10-01T09:00:00Z"^^xsd:dateTime .
:a1 a aprov:FieldAssertion ; aprov:assertedAbout :d ; aprov:assertsFieldKind metadata:DrawingTitleField ;
    aprov:hasLiteralValue "Ground floor plan" ; aprov:hasInferenceMeta :read1 .
:byHand a aprov:InferenceMeta ; aprov:inferredBy :reviewer ; aprov:inferredAt "2026-10-02T10:00:00Z"^^xsd:dateTime .
:a2 a aprov:FieldAssertion ; aprov:assertedAbout :d ; aprov:assertsFieldKind metadata:DrawingTitleField ;
    aprov:hasLiteralValue "Ground Floor Plan" ; aprov:hasInferenceMeta :byHand ; aprov:supersedes :a1 ;
    aprov:hasAcceptance aprov:Accepted ; aprov:acceptedBy :reviewer .
"""


def test_cq_10_3_shows_a_models_value_then_the_accepted_correction_that_supersedes_it():
    graph = Graph().parse(data=PREFIXES + HISTORY, format="turtle")
    local = lambda v: None if v is None else str(v).rsplit("#", 1)[-1]  # noqa: E731
    result = [(local(r.assertion), str(r.value), local(r.model), local(r.agent), local(r.acceptance),
               local(r.acceptedBy), local(r.supersededBy)) for r in graph.query(recorded_query("# CQ 10.3"))]
    assert result == [
        ("a1", "Ground floor plan", "llm", None, "Pending", None, "a2"),
        ("a2", "Ground Floor Plan", None, "reviewer", "Accepted", "reviewer", None),
    ]
