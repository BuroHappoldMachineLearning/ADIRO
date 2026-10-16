"""The sheet's and each layout's text fields are labels, and are reachable from the class that owns them (#162).

The class names the properties it can carry: each labelled datatype property is named by a min-0 owl:onProperty
restriction on its owner class ("can carry", like "can contain").
"""
from pathlib import Path

import pytest

pytest.importorskip("rdflib")

from rdflib import Graph, Literal, Namespace, URIRef  # noqa: E402
from rdflib.namespace import OWL, RDF, RDFS, SKOS, XSD  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
M = Namespace("https://w3id.org/adiro/aec_drawing_metadata#")
APROV = Namespace("https://w3id.org/adiro/aec_provenance#")

OWNED_TEXT_FIELDS = {
    M.DrawingSheet: (M.drawingIdentifier, M.drawingTitle, M.drawingScale),
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
    assert {M.drawingScale, M.layoutScale} <= set(metadata.subjects(RDFS.subPropertyOf, M.hasScale))


def _titleblock_promotions(graph):
    """Property that each title-block field kind is promoted to (aprov:mapsToFieldProperty)."""
    return {kind: graph.value(kind, APROV.mapsToFieldProperty)
            for kind in graph.subjects(SKOS.inScheme, M.TitleblockFieldScheme)}


def test_each_labelled_sheet_field_is_where_a_titleblock_field_kind_is_promoted(metadata):
    """A labelled sheet-level property that no title-block field kind promotes to is a label that extraction never fills."""
    labelled = {p for p in metadata.subjects(RDFS.domain, M.DrawingSheet)
                if (p, RDF.type, OWL.DatatypeProperty) in metadata and _is_label(metadata, p)}
    assert labelled, "expected labelled datatype properties on DrawingSheet"
    unpopulated = labelled - set(_titleblock_promotions(metadata).values())
    assert not unpopulated, f"no title-block field kind is promoted to: {sorted(map(str, unpopulated))}"


def test_no_titleblock_field_kind_is_promoted_to_the_unlabelled_parent_scale(metadata):
    """A title-block scale is the sheet's own: promoting it to hasScale would leave drawingScale unfilled and record one
    fact under two properties."""
    assert M.hasScale not in _titleblock_promotions(metadata).values()


def _labelled_but_not_named_by_owner(graph):
    """Datatype properties marked isComputerVisionLabel true that an owner class does not name in a restriction."""
    missing = []
    for prop in graph.subjects(RDF.type, OWL.DatatypeProperty):
        if not _is_label(graph, prop):
            continue
        owners = [o for o in graph.objects(prop, RDFS.domain) if isinstance(o, URIRef)]
        if not owners or any(prop not in _restricted_properties(graph, o) for o in owners):
            missing.append(prop)
    return missing


def test_every_labelled_datatype_property_is_named_by_a_restriction_on_its_owner(metadata):
    """The rule, found from the graph: a labelled property added without its restriction fails here."""
    assert _labelled_but_not_named_by_owner(metadata) == []


def test_the_rule_catches_a_labelled_property_its_owner_does_not_name(metadata):
    graph = Graph()
    for triple in metadata:
        graph.add(triple)
    extra = M.zzNewTextField
    graph.add((extra, RDF.type, OWL.DatatypeProperty))
    graph.add((extra, RDFS.domain, M.DrawingSheet))
    graph.add((extra, M.isComputerVisionLabel, Literal(True)))
    assert _labelled_but_not_named_by_owner(graph) == [extra]
