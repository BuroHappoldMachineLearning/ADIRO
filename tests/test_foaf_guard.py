"""exampleImage is a sub-property of foaf:depiction, and FOAF's own definition must never join it (#157)."""
import sys
from pathlib import Path

import pytest

pytest.importorskip("rdflib")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from rdflib import Graph  # noqa: E402
from rdflib.namespace import OWL, RDFS, URIRef  # noqa: E402

import validate_ontology as vo  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PREFIXES = ("@prefix owl: <http://www.w3.org/2002/07/owl#> . @prefix foaf: <http://xmlns.com/foaf/0.1/> .\n"
            "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n")


def graph(body):
    return Graph().parse(data=PREFIXES + body, format="turtle")


def test_the_modules_declare_depiction_as_an_annotation_property_and_import_no_foaf():
    for ttl in sorted((ROOT / "src").glob("*.ttl")):
        assert vo.find_foaf_problems(Graph().parse(str(ttl), format="turtle")) == [], ttl.name


def test_example_image_is_a_subproperty_of_the_standard_depiction():
    metadata = Graph().parse(str(ROOT / "src" / "aec_drawing_metadata.ttl"), format="turtle")
    example = URIRef("https://w3id.org/adiro/aec_drawing_metadata#exampleImage")
    depiction = URIRef("http://xmlns.com/foaf/0.1/depiction")
    assert (example, RDFS.subPropertyOf, depiction) in metadata
    assert (depiction, URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"), OWL.AnnotationProperty) in metadata


def test_a_foaf_import_is_reported():
    found = vo.find_foaf_problems(graph("<https://example.org/m> a owl:Ontology ; owl:imports <http://xmlns.com/foaf/0.1/> ."))
    assert len(found) == 1 and "imports FOAF" in found[0]


def test_depiction_declared_as_an_object_property_is_reported():
    found = vo.find_foaf_problems(graph("foaf:depiction a owl:ObjectProperty ."))
    assert len(found) == 1 and "owl:AnnotationProperty only" in found[0]
    both = vo.find_foaf_problems(graph("foaf:depiction a owl:AnnotationProperty, owl:ObjectProperty ."))
    assert len(both) == 1  # the annotation declaration is fine, the other is not


def test_an_annotation_declaration_and_other_imports_are_fine():
    body = "<https://example.org/m> a owl:Ontology ; owl:imports <https://w3id.org/adiro/aec_provenance> .\nfoaf:depiction a owl:AnnotationProperty ."
    assert vo.find_foaf_problems(graph(body)) == []


def test_the_validator_makes_it_an_error(tmp_path):
    ttl = tmp_path / "aec_x.ttl"
    ttl.write_text(PREFIXES + "<https://w3id.org/adiro/aec_x> a owl:Ontology ; owl:versionInfo \"1.0.0\" ; "
                   "owl:versionIRI <https://w3id.org/adiro/aec_x/1.0.0> ; owl:imports <http://xmlns.com/foaf/0.1/> .\n", encoding="utf-8")
    ok, errors, _ = vo.validate_ontology(ttl)
    assert not ok and any("imports FOAF" in e for e in errors)
