"""An extraction run, its steps and their configuration (#237): the terms, and CQ 10.1 of the UC-01 ORSD."""
import sys
from pathlib import Path

import pytest

pytest.importorskip("rdflib")
from rdflib import Graph, Namespace, URIRef  # noqa: E402
from rdflib.namespace import OWL, RDF, RDFS, XSD  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_uc01_competency_queries import PREFIXES, recorded_query  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
APROV = Namespace("https://w3id.org/adiro/adiro_provenance#")
PROV = Namespace("http://www.w3.org/ns/prov#")
DCTERMS = Namespace("http://purl.org/dc/terms/")
PROVENANCE = Graph().parse(ROOT / "src" / "adiro_provenance.ttl", format="turtle")


def test_a_configuration_is_an_entity_holding_its_content_as_text():
    assert (APROV.Configuration, RDFS.subClassOf, PROV.Entity) in PROVENANCE
    assert (APROV.configurationContent, RDF.type, OWL.DatatypeProperty) in PROVENANCE
    assert PROVENANCE.value(APROV.configurationContent, RDFS.domain) == APROV.Configuration
    assert PROVENANCE.value(APROV.configurationContent, RDFS.range) == XSD.string


@pytest.mark.parametrize("stub, kind, source", [
    (DCTERMS.isPartOf, OWL.ObjectProperty, "http://purl.org/dc/terms/"),
    (PROV.startedAtTime, OWL.DatatypeProperty, "http://www.w3.org/ns/prov#"),
])
def test_the_run_stubs_name_their_source_and_carry_no_axioms(stub, kind, source):
    assert (stub, RDF.type, kind) in PROVENANCE
    assert PROVENANCE.value(stub, RDFS.isDefinedBy) == URIRef(source)
    assert not [p for p, _ in PROVENANCE.predicate_objects(stub) if p in (RDFS.domain, RDFS.range, RDFS.subPropertyOf)]


RUN = """@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
:d a metadata:DrawingSheet ; metadata:drawingIdentifier "ST-101" .
:run1 a prov:Activity ; prov:startedAtTime "2026-10-28T09:00:00Z"^^xsd:dateTime ;
    prov:used <https://w3id.org/adiro/adiro_provenance/2.1.0> .
:read1 a aprov:InferenceMeta ; dcterms:isPartOf :run1 ; aprov:inferredWith :llm ; prov:used :prompt .
:prompt a aprov:Configuration ; aprov:configurationContent "Read the title block and return each field." .
:a1 a aprov:FieldAssertion ; aprov:assertedAbout :d ; aprov:assertsFieldKind metadata:DrawingTitleField ;
    aprov:hasLiteralValue "Ground floor plan" ; aprov:hasInferenceMeta :read1 .
:byHand a aprov:InferenceMeta ; aprov:inferredBy :reviewer .
:a2 a aprov:FieldAssertion ; aprov:assertedAbout :d ; aprov:assertsFieldKind metadata:DrawingTitleField ;
    aprov:hasLiteralValue "Ground Floor Plan" ; aprov:hasInferenceMeta :byHand ; aprov:supersedes :a1 .
:a3 a aprov:FieldAssertion ; aprov:assertedAbout :d ; aprov:assertsFieldKind metadata:DrawnByField ;
    aprov:hasLiteralValue "J. Smith" ; aprov:hasInferenceMeta :read1 .
"""


def cq_10_1(data):
    rows = Graph().parse(data=PREFIXES + data, format="turtle").query(recorded_query("# CQ 10.1"))
    short = lambda v: None if v is None else str(v).rsplit("#", 1)[-1]  # noqa: E731
    return {(short(r.assertion), str(r.value), short(r.run), r.started.toPython().isoformat() if r.started else None,
             short(r.step), short(r.model), short(r.configuration)) for r in rows}


def test_cq_10_1_traces_each_value_of_a_field_to_its_run_step_model_and_configuration():
    assert cq_10_1(RUN) == {
        ("a1", "Ground floor plan", "run1", "2026-10-28T09:00:00+00:00", "read1", "llm", "prompt"),
        # a value typed by a person has a step with no model, no run and no configuration
        ("a2", "Ground Floor Plan", None, None, "byHand", None, None),
    }


def test_cq_10_1_does_not_take_the_model_or_the_ontology_version_for_a_configuration():
    # inferredWith is a sub-property of prov:used, and the run used an ontology version: neither is a Configuration
    rows = cq_10_1(RUN.replace(" ; prov:used :prompt .", " ; prov:used :llm ."))
    assert ("a1", "Ground floor plan", "run1", "2026-10-28T09:00:00+00:00", "read1", "llm", None) in rows
