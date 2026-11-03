"""SKOS concept schemes and concepts are documented in a Concepts section, grouped by scheme."""

from __future__ import annotations

import textwrap

from rdflib import Graph

from ttl2md import convert_graph

TURTLE = """
@prefix : <https://example.org/onto#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix ext: <https://example.org/ext#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
<https://example.org/onto> a owl:Ontology .
:hasScale a owl:DatatypeProperty ; rdfs:comment "The scale." .
:Fields a skos:ConceptScheme ; rdfs:label "Field Scheme" ; rdfs:comment "The fields." ;
    skos:scopeNote "Generic names only." ; skos:note "A kind called Other is not a member." .
:ScaleField a skos:Concept , ext:FieldKind ; rdfs:label "Scale Field" ;
    skos:definition "The scale of the drawing, read into hasScale."@en ; rdfs:comment "A note on the scale." ;
    skos:prefLabel "Scale"@en , "Massstab"@de ; skos:altLabel "NTS"@en ; skos:example "1:50" ;
    skos:inScheme :Fields ; ext:mapsTo :hasScale ; ext:expected xsd:string .
:Alpha a skos:Concept ; rdfs:label "Alpha Field" ; skos:inScheme :Fields .
:Other a skos:Concept , owl:NamedIndividual ; rdfs:label "Other" ; skos:definition "None of the Fields."@en .
:plain a owl:NamedIndividual ; rdfs:label "Plain" .
"""


def md(**kwargs) -> str:
    graph = Graph().parse(data=textwrap.dedent(TURTLE), format="turtle")
    return convert_graph(graph, **kwargs)


def test_each_scheme_is_followed_by_its_concepts_sorted_by_label_then_the_concepts_in_no_scheme():
    page = md()
    order = [page.index(s) for s in ("## Concepts", "### Field Scheme {#Fields}", "#### Alpha Field {#Alpha}",
                                     "#### Scale Field {#ScaleField}", "### Concepts in no scheme", "#### Other {#Other}")]
    assert order == sorted(order)


def test_a_concept_shows_its_definition_names_examples_scheme_and_other_statements():
    page = md(external_links={"https://example.org/ext#FieldKind": "ext.md#FieldKind"})
    entry = page[page.index("#### Scale Field"):page.index("### Concepts in no scheme")]
    assert "The scale of the drawing, read into [hasScale](#hasScale)." in entry
    assert "- **Comment:** A note on the scale." in entry
    assert "- **Type:** [`ext:FieldKind`](ext.md#FieldKind)" in entry  # a class on another page is linked
    assert "- **In scheme:** [Field Scheme](#Fields)" in entry
    assert '- **Preferred labels:** "Scale" (en), "Massstab" (de)' in entry
    assert '- **Alternative labels:** "NTS" (en)' in entry
    assert '- **Examples:** "1:50"' in entry
    assert "- **mapsTo:** [hasScale](#hasScale)" in entry
    assert "- **expected:** `xsd:string`" in entry


def test_a_scheme_shows_its_notes_with_the_names_of_terms_linked():
    page = md()
    assert "- **Scope note:** Generic names only." in page
    assert "- **Note:** A kind called [Other](#Other) is not a member." in page


def test_a_concept_declared_a_named_individual_is_listed_once_among_the_concepts():
    page = md()
    assert page.count("{#Other}") == 1 and "## Named Individuals" in page and "### Plain {#plain}" in page
    assert page.index("{#Other}") > page.index("## Concepts")


def test_no_concepts_no_section():
    graph = Graph().parse(data="@prefix owl: <http://www.w3.org/2002/07/owl#> .\n<https://e.org/o> a owl:Ontology .", format="turtle")
    assert "## Concepts" not in convert_graph(graph)
