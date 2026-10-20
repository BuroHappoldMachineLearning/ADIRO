"""The Metadata block of a pyLODE page: the module's own IRI and title, two links, and a check (#146)."""
import sys
from pathlib import Path

import pytest

pytest.importorskip("rdflib")
pytest.importorskip("pylode")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from pylode.profiles.ontpub import OntPub  # noqa: E402

import pylode_metadata as pm  # noqa: E402

TTL = """@prefix : <https://w3id.org/adiro/aec_toy#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
<https://w3id.org/adiro/aec_toy> a owl:Ontology ; dcterms:title "AEC Toy Ontology" ; rdfs:comment "A toy." ;
    owl:versionIRI <https://w3id.org/adiro/aec_toy/1.0.0> ; owl:versionInfo "1.0.0" .
:Thing a owl:Class ; rdfs:label "Thing" ; rdfs:comment "A thing." .
:ThingScheme a skos:ConceptScheme ; dcterms:title "Thing Scheme" .
:aConcept a skos:Concept ; skos:inScheme :ThingScheme ; skos:prefLabel "A concept"@en .
"""


@pytest.fixture(scope="module")
def toy(tmp_path_factory):
    folder = tmp_path_factory.mktemp("toy")
    ttl = folder / "aec_toy.ttl"
    ttl.write_text(TTL, encoding="utf-8")
    return ttl


def page_of(source, folder):
    out = folder / "page.html"
    OntPub(ontology=source).make_html(destination=str(out))
    return out.read_text(encoding="utf-8")


def test_pylode_given_the_file_shows_the_concept_scheme_as_the_ontology(toy):
    # the bug of #146: the scheme's IRI and title, the second title in the heading, a second schema.org block
    page = page_of(str(toy), toy.parent)
    assert pm.shown(page)[0] == "https://w3id.org/adiro/aec_toy#ThingScheme"
    assert pm.check(page, toy), "the check must catch it"


def test_given_the_graph_without_the_schemes_type_it_shows_the_modules_own_iri_and_title(toy):
    page = page_of(pm.graph_for_pylode(toy), toy.parent)
    assert pm.shown(page) == ("https://w3id.org/adiro/aec_toy", "AEC Toy Ontology")
    assert pm.check(page, toy) == []
    assert page.count("DefinedTermSet") == 1
    assert "https://w3id.org/adiro/aec_toy#ThingScheme" not in page


def test_the_file_itself_keeps_its_scheme(toy):
    # only pyLODE's copy loses the type: the Turtle that is published is untouched
    from rdflib import Graph
    from rdflib.namespace import RDF, SKOS

    assert (None, RDF.type, SKOS.ConceptScheme) in Graph().parse(str(toy), format="turtle")
    assert (None, RDF.type, SKOS.ConceptScheme) not in pm.graph_for_pylode(toy)


def test_the_two_links_are_added_after_the_iri_row_once(toy):
    page = page_of(pm.graph_for_pylode(toy), toy.parent)
    with_links = pm.add_links(page, "aec_toy")
    ttl, docs = pm.links("aec_toy")
    assert ttl == "https://w3id.org/adiro/aec_toy.ttl" and docs == "https://w3id.org/adiro/ontologies/aec_toy/"
    assert f'<a href="{ttl}">' in with_links and f'<a href="{docs}">' in with_links
    assert with_links.index("TTL source") > with_links.index("<strong>IRI</strong>") and with_links.index("Documentation") > with_links.index("TTL source")
    assert pm.add_links(with_links, "aec_toy") == with_links, "idempotent"
    assert pm.check(with_links, toy) == [], "the links do not disturb the check"


def test_an_earlier_releases_links_point_at_its_own_files():
    ttl, docs = pm.links("aec_toy", "1.0.0")
    assert ttl == "https://w3id.org/adiro/aec_toy/1.0.0/aec_toy.ttl" and docs == "https://w3id.org/adiro/ontologies/aec_toy/1.0.0/"


def test_a_page_that_is_not_a_pylode_page_is_reported(toy):
    assert pm.check("<html>committed page</html>", toy) == ["no Metadata block"]
    assert pm.add_links("<html>committed page</html>", "aec_toy") == "<html>committed page</html>"


def test_module_and_version_are_read_from_the_output_folder(tmp_path):
    assert pm.module_and_version(tmp_path / "src" / "aec_x.ttl", tmp_path / "docs") == ("aec_x", None)
    assert pm.module_and_version(tmp_path / "versions" / "aec_x" / "1.2.3" / "aec_x.ttl", tmp_path / "docs" / "aec_x" / "1.2.3") == ("aec_x", "1.2.3")
