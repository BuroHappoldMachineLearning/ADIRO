"""The pyLODE pages link the names of terms in a definition to their documentation, like the Markdown pages (#252)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import generate_docs as gd  # noqa: E402

MODULE = """@prefix : <https://w3id.org/adiro/adiro_x#> .
@prefix aprov: <https://w3id.org/adiro/adiro_provenance#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
<https://w3id.org/adiro/adiro_x> a owl:Ontology .
:Box a owl:Class ; rdfs:comment "A Box, an InferredEntity in a Frame, made by a prov:Activity." .
:Frame a owl:Class ; rdfs:comment "Where a Box is." .
prov:Activity a owl:Class .
"""

PROVENANCE = """@prefix : <https://w3id.org/adiro/adiro_provenance#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
<https://w3id.org/adiro/adiro_provenance> a owl:Ontology .
:InferredEntity a owl:Class .
:Failed a owl:NamedIndividual .
"""


def entity(name, description):
    return (f'<div class="property entity" id="{name}">\n<table><tr><th><a class="hover_property" '
            f'href="http://purl.org/dc/terms/description" title="">Description</a></th>\n<td><p>{description}</p></td></tr></table>\n</div>\n')


PAGE = ("<html>" + entity("Box", "A Box, an InferredEntity in a Frame, made by a prov:Activity.")
        + entity("Frame", "Where a Box is.") + entity("Activity", "Local typing stub.") + "</html>")


def files(tmp_path):
    (tmp_path / "adiro_x.ttl").write_text(MODULE, encoding="utf-8")
    (tmp_path / "adiro_provenance.ttl").write_text(PROVENANCE, encoding="utf-8")
    return tmp_path / "adiro_x.ttl", tmp_path / "adiro_provenance.ttl"


def test_suite_terms_lists_each_modules_own_terms_and_which_are_individuals(tmp_path):
    suite = gd.suite_terms(list(files(tmp_path)))
    assert suite["https://w3id.org/adiro/adiro_provenance#Failed"] == ("adiro_provenance", "Failed", True)
    assert suite["https://w3id.org/adiro/adiro_x#Box"] == ("adiro_x", "Box", False)
    assert "http://www.w3.org/ns/prov#Activity" not in suite  # a stub is not the module's own term


def test_definitions_link_to_this_page_and_to_another_modules_latest_page(tmp_path):
    module, provenance = files(tmp_path)
    page = gd.link_html_definitions(PAGE, module, "adiro_x", "", gd.suite_terms([module, provenance]))
    assert ('<td><p>A Box, an <a href="adiro_provenance.html#InferredEntity">InferredEntity</a> in a '
            '<a href="#Frame">Frame</a>, made by a <a href="#Activity">prov:Activity</a>.</p></td>') in page
    assert '<td><p>Where a <a href="#Box">Box</a> is.</p></td>' in page
    assert gd.link_html_definitions(page, module, "adiro_x", "", gd.suite_terms([module, provenance])) == page


def test_an_earlier_releases_page_links_two_levels_up(tmp_path):
    module, provenance = files(tmp_path)
    page = gd.link_html_definitions(PAGE, module, "adiro_x", "../../", gd.suite_terms([module, provenance]))
    assert '<a href="../../adiro_provenance.html#InferredEntity">' in page


def test_the_page_of_a_deprecated_module_links_only_within_itself(tmp_path):
    module, provenance = files(tmp_path)
    module.write_text(MODULE.replace("a owl:Ontology .", "a owl:Ontology ; owl:deprecated true ."), encoding="utf-8")
    page = gd.link_html_definitions(PAGE, module, "adiro_x", "", gd.suite_terms([module, provenance]))
    assert "adiro_provenance.html" not in page and '<a href="#Frame">Frame</a>' in page


def test_the_published_pages_link_the_example_of_the_issue():
    md = (ROOT / "docs" / "ontologies" / "adiro_provenance.md").read_text(encoding="utf-8")
    assert "each recorded as a [FieldAssertion](#FieldAssertion)." in md
    html = (ROOT / "docs" / "adiro_provenance.html").read_text(encoding="utf-8")
    assert 'region detection used' in html and '<a href="#errorMessage">errorMessage</a>' in html
