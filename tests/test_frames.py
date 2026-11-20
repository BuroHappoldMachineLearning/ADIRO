"""The images a model saw (#239): frames at a resolution, crops of a region, kept images; CQ 10.4 of the UC-01 ORSD."""
import sys
from pathlib import Path

import pytest

pytest.importorskip("rdflib")
from rdflib import Graph, Namespace  # noqa: E402
from rdflib.namespace import OWL, RDF, RDFS, XSD  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_uc01_competency_queries import PREFIXES, recorded_query  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
GEOM = Namespace("https://w3id.org/adiro/adiro_geometry#")
APROV = Namespace("https://w3id.org/adiro/adiro_provenance#")
GEOMETRY = Graph().parse(ROOT / "src" / "adiro_geometry.ttl", format="turtle")


@pytest.mark.parametrize("term, kind, domain, range_", [
    (GEOM.resolutionDpi, OWL.DatatypeProperty, GEOM.CoordinateFrame, XSD.decimal),
    (GEOM.coversRegion, OWL.ObjectProperty, GEOM.CoordinateFrame, GEOM.BoundingBox),
    (GEOM.imageOf, OWL.ObjectProperty, APROV.DrawingFile, GEOM.CoordinateFrame),
])
def test_the_frame_terms(term, kind, domain, range_):
    assert (term, RDF.type, kind) in GEOMETRY
    assert GEOMETRY.value(term, RDFS.domain) == domain and GEOMETRY.value(term, RDFS.range) == range_


def test_no_crop_class_and_no_transform_term():
    # a crop is a frame limited to a region, and the only change between frames is a uniform scale (#235)
    names = {str(s).rsplit("#", 1)[-1].lower() for s in GEOMETRY.subjects(RDF.type, None) if str(s).startswith(str(GEOM))}
    assert not [n for n in names if "crop" in n or "transform" in n]


# One page rendered at 300 dpi; the detector saw it scaled so that its shorter side is 1200 px; the reader saw a crop of the
# title block at 300 dpi, which was kept next to the data; a hand-typed value saw nothing.
SEEN = """@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix adgeom: <https://w3id.org/adiro/adiro_geometry#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
:d a admeta:DrawingSheet ; admeta:drawingIdentifier "ST-101" ; admeta:isOnPage :p1 ; admeta:contains :tb .
:p1 a adprov:FilePage ; adprov:pageNumber 1 .
:pt a adgeom:CoordinateFrame ; adgeom:describesPage :p1 ; adgeom:coordinateSpace "page_display_pt" ; adgeom:unit "pt" .
:full a adgeom:CoordinateFrame ; adgeom:describesPage :p1 ; adgeom:unit "px" ; adgeom:resolutionDpi 300 .
:small a adgeom:CoordinateFrame ; adgeom:describesPage :p1 ; adgeom:unit "px" ; adgeom:resolutionDpi 51.31 .
:tbBox a adgeom:BoundingBox ; adgeom:bboxXYXY "[1900, 1400, 2360, 1660]" ; adgeom:inCoordinateFrame :pt ; adprov:hasInferenceMeta :detect .
:tb a admeta:Titleblock ; adgeom:hasBoundingBox :tbBox .
:crop a adgeom:CoordinateFrame ; adgeom:describesPage :p1 ; adgeom:unit "px" ; adgeom:resolutionDpi 300.0 ; adgeom:coversRegion :tbBox .
:cropImage a adprov:DrawingFile ; adgeom:imageOf :crop ; adprov:mediaType "image/png" ;
    adprov:storageLocation "crops/ST-101-titleblock.png"^^xsd:anyURI .
:detect a adprov:InferenceMeta ; adprov:hasStepKind adprov:RegionDetection ; prov:used :small , :p1 .
:read a adprov:InferenceMeta ; adprov:hasStepKind adprov:FieldExtraction ; adprov:inferredWith :llm ; prov:used :crop , :p1 , :prompt .
:prompt a adprov:Configuration ; adprov:configurationContent "Read the title block." .
:a1 a adprov:FieldAssertion ; adprov:assertedAbout :d ; adprov:assertsFieldKind admeta:DrawingTitleField ;
    adprov:hasLiteralValue "Ground floor plan" ; adprov:hasInferenceMeta :read .
:byHand a adprov:InferenceMeta ; adprov:inferredBy :reviewer .
:a2 a adprov:FieldAssertion ; adprov:assertedAbout :d ; adprov:assertsFieldKind admeta:DrawingTitleField ;
    adprov:hasLiteralValue "Ground Floor Plan" ; adprov:hasInferenceMeta :byHand .
"""


def cq_10_4(data):
    graph = Graph().parse(data=PREFIXES + data, format="turtle")
    local = lambda v: None if v is None else str(v).rsplit("#", 1)[-1]  # noqa: E731
    return {(local(r.assertion), local(r.frame), None if r.dpi is None else float(r.dpi), local(r.region),
             None if r.box is None else str(r.box), local(r.image), None if r.location is None else str(r.location))
            for r in graph.query(recorded_query("# CQ 10.4"))}


def test_cq_10_4_gives_the_crop_the_reader_saw_with_its_resolution_region_and_kept_image():
    assert cq_10_4(SEEN) == {
        # the page, the prompt and the model the step also used are not frames
        ("a1", "crop", 300.0, "tbBox", "[1900, 1400, 2360, 1660]", "cropImage", "crops/ST-101-titleblock.png"),
        # a hand-typed value saw no image, and is listed with the frame columns empty
        ("a2", None, None, None, None, None, None),
    }


def test_cq_10_4_records_what_was_seen_when_the_image_was_not_kept_and_the_whole_page_was_seen():
    whole_page = SEEN.replace("prov:used :crop , :p1 , :prompt", "prov:used :small , :p1 , :prompt")
    assert ("a1", "small", 51.31, None, None, None, None) in cq_10_4(whole_page)
