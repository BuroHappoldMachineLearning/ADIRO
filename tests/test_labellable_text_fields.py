"""The sheet's and each layout's text fields are labels, and are reachable from the class that owns them (#162).

A tool that derives its labels by walking the ontology from a class follows rdfs:subClassOf and restrictions, not
rdfs:domain, so a labelled datatype property must be named by an owl:onProperty restriction on its owner class.
"""
from pathlib import Path

import pytest

pytest.importorskip("rdflib")

from rdflib import Graph, Literal, Namespace  # noqa: E402
from rdflib.namespace import OWL, RDF, RDFS, XSD  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
M = Namespace("https://w3id.org/adiro/aec_drawing_metadata#")

OWNED_TEXT_FIELDS = {
    M.DrawingSheet: (M.drawingIdentifier, M.drawingTitle, M.sheetScale),
    M.Layout: (M.layoutIdentifier, M.layoutTitle, M.layoutScale),
}
TEXT_FIELDS = [(owner, prop) for owner, props in OWNED_TEXT_FIELDS.items() for prop in props]


@pytest.fixture(scope="module")
def metadata():
    return Graph().parse(str(ROOT / "src" / "aec_drawing_metadata.ttl"), format="turtle")


def _is_label(graph, term):
    return any(o.toPython() is True for o in graph.objects(term, M.isComputerVisionLabel) if isinstance(o, Literal))


def _restricted_properties(graph, cls):
    return {graph.value(r, OWL.onProperty) for r in graph.objects(cls, RDFS.subClassOf)
            if (r, RDF.type, OWL.Restriction) in graph}


@pytest.mark.parametrize("owner,prop", TEXT_FIELDS, ids=lambda t: str(t).rsplit("#", 1)[-1])
def test_each_text_field_is_a_labelled_datatype_property_of_its_owner(metadata, owner, prop):
    assert (prop, RDF.type, OWL.DatatypeProperty) in metadata
    assert _is_label(metadata, prop)
    assert (prop, RDFS.domain, owner) in metadata
    assert (prop, RDFS.range, XSD.string) in metadata


@pytest.mark.parametrize("owner,prop", TEXT_FIELDS, ids=lambda t: str(t).rsplit("#", 1)[-1])
def test_each_text_field_is_named_by_a_can_have_restriction_on_its_owner(metadata, owner, prop):
    assert prop in _restricted_properties(metadata, owner)
    for r in metadata.objects(owner, RDFS.subClassOf):
        if metadata.value(r, OWL.onProperty) == prop:
            # "can have": adds no constraint, only the class-to-property edge.
            assert metadata.value(r, OWL.minQualifiedCardinality).toPython() == 0
            assert metadata.value(r, OWL.onDataRange) == XSD.string


def test_has_scale_is_the_unlabelled_parent_of_the_two_scales(metadata):
    assert not _is_label(metadata, M.hasScale)
    assert {M.sheetScale, M.layoutScale} <= set(metadata.subjects(RDFS.subPropertyOf, M.hasScale))
