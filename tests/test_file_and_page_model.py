"""The file, the page and the agents (#192): the structure of the three modules and the alignment rules that were decided."""
from pathlib import Path

import pytest

pytest.importorskip("rdflib")
from rdflib import BNode, Graph, Namespace, URIRef  # noqa: E402
from rdflib.collection import Collection  # noqa: E402
from rdflib.namespace import OWL, RDF, RDFS, SKOS, XSD  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
APROV = Namespace("https://w3id.org/adiro/aec_provenance#")
GEOM = Namespace("https://w3id.org/adiro/aec_geometry#")
META = Namespace("https://w3id.org/adiro/aec_drawing_metadata#")
CT = Namespace("https://standards.iso.org/iso/21597/-1/ed-1/en/Container#")
PROV = Namespace("http://www.w3.org/ns/prov#")


def load(module):
    return Graph().parse(str(ROOT / "src" / f"{module}.ttl"), format="turtle")


PROVENANCE, GEOMETRY, METADATA = load("aec_provenance"), load("aec_geometry"), load("aec_drawing_metadata")


def test_the_classes_are_subclasses_of_the_iso_21597_terms_and_of_prov():
    supers = lambda s: set(PROVENANCE.objects(s, RDFS.subClassOf))
    assert {PROV.Entity, CT.Document} <= supers(APROV.DrawingFile)
    assert PROV.Entity in supers(APROV.FilePage)
    assert {PROV.Agent, CT.Party} <= supers(APROV.Party)
    assert {APROV.Party, CT.Person} <= supers(APROV.Person)
    assert {APROV.Party, CT.Organisation} <= supers(APROV.Organisation)


def test_party_is_the_disjoint_union_of_person_and_organisation():
    listing = PROVENANCE.value(APROV.Party, OWL.disjointUnionOf)
    assert set(Collection(PROVENANCE, listing)) == {APROV.Person, APROV.Organisation}


def test_the_iso_stubs_name_the_standard_and_carry_none_of_its_axioms():
    for stub in (CT.Document, CT.Party, CT.Person, CT.Organisation):
        assert PROVENANCE.value(stub, RDFS.isDefinedBy) == URIRef("https://standards.iso.org/iso/21597/-1/ed-1/en/Container.rdf")
        axioms = [p for p, _ in PROVENANCE.predicate_objects(stub) if p in (RDFS.subClassOf, RDFS.domain, RDFS.range, OWL.disjointWith, OWL.equivalentClass)]
        assert axioms == [], f"{stub} is a stub: it carries {axioms}"


def test_a_file_property_is_related_to_the_standards_by_close_match_and_never_as_a_subproperty():
    file_properties = [p for p in PROVENANCE.subjects(RDFS.domain, APROV.DrawingFile)]
    assert len(file_properties) >= 10
    for prop in file_properties:
        assert list(PROVENANCE.objects(prop, SKOS.closeMatch)), f"{prop} has no skos:closeMatch"
        external = [o for o in PROVENANCE.objects(prop, RDFS.subPropertyOf)]
        assert external == [], f"{prop} is a subproperty of {external}: ICDD's properties are functional, so only skos:closeMatch is used"


def test_a_page_is_counted_from_one_and_belongs_to_a_file():
    assert PROVENANCE.value(APROV.pageNumber, RDFS.range) == XSD.positiveInteger
    assert PROVENANCE.value(APROV.belongsToFile, RDFS.domain) == APROV.FilePage
    assert PROVENANCE.value(APROV.belongsToFile, RDFS.range) == APROV.DrawingFile


def test_what_is_true_of_a_page_is_on_the_page_and_the_frame_keeps_only_its_convention():
    for moved in ("displayWidthPt", "displayHeightPt", "pdfRotationDeg"):
        assert PROVENANCE.value(APROV[moved], RDFS.domain) == APROV.FilePage
    frame_properties = {str(p).rsplit("#", 1)[-1] for p in GEOMETRY.subjects(RDFS.domain, GEOM.CoordinateFrame)}
    assert frame_properties == {"describesPage", "coordinateSpace", "unit", "profileRef"}
    assert GEOMETRY.value(GEOM.describesPage, RDFS.range) == APROV.FilePage
    for gone in ("pageIndex", "frameArtifactRef"):
        assert (GEOM[gone], None, None) not in GEOMETRY


def test_a_drawing_is_linked_to_its_page_and_no_longer_to_its_frame():
    assert METADATA.value(META.isOnPage, RDFS.domain) == META.DrawingSheet
    assert METADATA.value(META.isOnPage, RDFS.range) == APROV.FilePage
    assert (META.hasCoordinateFrame, None, None) not in METADATA
    imports = {str(o) for o in METADATA.objects(None, OWL.imports)}
    assert "https://w3id.org/adiro/aec_geometry" in imports, "a title block's region is located with the geometry module"


def test_every_metadata_container_may_carry_a_bounding_box_and_that_use_is_stated_in_the_module():
    def box_restrictions(cls):
        return [r for r in METADATA.objects(cls, RDFS.subClassOf)
                if isinstance(r, BNode) and METADATA.value(r, OWL.onProperty) == GEOM.hasBoundingBox]

    restrictions = box_restrictions(META.MetadataContainer)
    assert len(restrictions) == 1, "MetadataContainer has one restriction on geom:hasBoundingBox"
    assert METADATA.value(restrictions[0], OWL.onClass) == GEOM.BoundingBox
    assert METADATA.value(restrictions[0], OWL.minQualifiedCardinality) is not None
    children = {"Titleblock", "RevisionTable", "Legend", "KeyPlan", "Note"}
    assert {str(c).rsplit("#", 1)[-1] for c in METADATA.subjects(RDFS.subClassOf, META.MetadataContainer)} == children
    assert box_restrictions(META.Titleblock) == [], "the children inherit it: it is not repeated on the title block"
    layout = box_restrictions(META.Layout)
    assert len(layout) == 1 and METADATA.value(layout[0], OWL.onClass) == GEOM.BoundingBox, "a Layout may carry a bounding box too"
    element = box_restrictions(META.DrawingElement)
    assert len(element) == 1 and METADATA.value(element[0], OWL.onClass) == GEOM.BoundingBox, "so may every drawing element"
    # the property itself stays free of a domain: a domain is an inference, and geometry sits below the drawing module
    assert (GEOM.hasBoundingBox, RDFS.domain, None) not in GEOMETRY


def test_a_human_annotation_is_described_as_an_inference_step_performed_by_a_person():
    for term, text in ((APROV.InferredEntity, "a person"), (APROV.inferredBy, "aprov:Person")):
        comment = str(PROVENANCE.value(term, RDFS.comment))
        assert text in comment, f"{term}'s comment should say that a person can be the producer"
    assert "person marked it" in str(GEOMETRY.value(GEOM.BoundingBox, RDFS.comment)), "a bounding box is not only detected"


def test_the_agents_live_in_the_provenance_module_and_the_drawing_module_uses_them():
    for gone in ("Person", "Organisation"):
        assert (META[gone], RDF.type, OWL.Class) not in METADATA
    for role in ("isAuthoredBy", "isCheckedBy", "isApprovedBy"):
        assert METADATA.value(META[role], RDFS.range) == APROV.Person
    for role in ("assertsClient", "assertsOriginator"):
        assert METADATA.value(META[role], RDFS.range) == APROV.Organisation
