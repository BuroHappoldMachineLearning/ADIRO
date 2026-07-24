"""Edge-case tests for the ttl2md converter.

Each test parses a small inline Turtle snippet and asserts on the rendered
Markdown, focusing on the behaviours that matter for real ontologies:
restrictions, class expressions, example-image annotations, cross-references,
label fallbacks and deterministic ordering.
"""

from __future__ import annotations

import textwrap

import pytest
from rdflib import Graph

from ttl2md import MarkdownConverter, convert_file, convert_graph, local_name

PREFIXES = """
@prefix : <https://example.org/onto#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
"""


def to_md(turtle: str, **kwargs) -> str:
    graph = Graph()
    graph.parse(data=PREFIXES + textwrap.dedent(turtle), format="turtle")
    return convert_graph(graph, **kwargs)


# --------------------------------------------------------------------------
# Basic structure & ontology metadata
# --------------------------------------------------------------------------


def test_minimal_ontology_has_title_and_iri_but_no_sections():
    md = to_md(
        """
        <https://example.org/onto> a owl:Ontology ;
            rdfs:label "My Ontology" ;
            rdfs:comment "A tiny ontology." .
        """
    )
    assert md.startswith("# My Ontology\n")
    assert "A tiny ontology." in md
    assert "- **IRI:** `https://example.org/onto`" in md
    # No terms -> no section headings.
    assert "## Classes" not in md
    assert "## Object Properties" not in md
    assert md.endswith("\n") and not md.endswith("\n\n")


def test_title_override_wins_over_label():
    md = to_md(
        """<https://example.org/onto> a owl:Ontology ; rdfs:label "Label" .""",
        title="Explicit Title",
    )
    assert md.startswith("# Explicit Title\n")


def test_version_and_imports_rendered():
    md = to_md(
        """
        <https://example.org/onto> a owl:Ontology ;
            owl:versionInfo "2.1.0" ;
            owl:imports <http://www.w3.org/2004/02/skos/core> .
        """
    )
    assert "- **Version:** 2.1.0" in md
    assert "- **Imports:**" in md
    assert "`<" not in md  # imports rendered as CURIE/local name, never raw IRI


# --------------------------------------------------------------------------
# Classes: comments, sub-class-of, labels, ordering
# --------------------------------------------------------------------------


def test_class_comment_and_named_superclass_link():
    md = to_md(
        """
        :Animal a owl:Class ; rdfs:label "Animal" .
        :Dog a owl:Class ; rdfs:label "Dog" ;
            rdfs:comment "A domestic dog." ;
            rdfs:subClassOf :Animal .
        """
    )
    assert "### Dog {#Dog}" in md
    assert "A domestic dog." in md
    # Intra-ontology reference becomes an anchor link using the target's label.
    assert "- **Sub class of:** [Animal](#Animal)" in md


def test_label_falls_back_to_local_name():
    md = to_md(""":Widget a owl:Class .""")
    assert "### Widget {#Widget}" in md


def test_classes_sorted_deterministically():
    md = to_md(
        """
        :Zebra a owl:Class ; rdfs:label "Zebra" .
        :Aardvark a owl:Class ; rdfs:label "Aardvark" .
        """
    )
    assert md.index("### Aardvark") < md.index("### Zebra")


def test_heading_anchor_uses_local_name_not_label():
    md = to_md(""":DrawingSheet a owl:Class ; rdfs:label "Drawing Sheet" .""")
    assert "### Drawing Sheet {#DrawingSheet}" in md


# --------------------------------------------------------------------------
# Example images (the behaviour mirrored from the pyLODE post-processing)
# --------------------------------------------------------------------------


def test_example_images_detected_by_local_name_without_declaration():
    # exampleImage is *not* declared as an AnnotationProperty here; detection is
    # purely by local name, matching the historical HTML post-processing. String
    # literals are used so the paths are not absolutised against a base IRI.
    md = to_md(
        """
        :Titleblock a owl:Class ; rdfs:label "Titleblock" ;
            :exampleImage "img/tb_01.png" ;
            :exampleImage "img/tb_02.png" .
        """
    )
    assert "*Example images:*" in md
    assert "![Titleblock — example](img/tb_01.png)" in md
    assert "![Titleblock — example](img/tb_02.png)" in md


def test_example_images_get_asset_prefix_when_relative():
    md = to_md(
        """:C a owl:Class ; rdfs:label "C" ; :exampleImage "img/x.png" .""",
        asset_prefix="../",
    )
    assert "![C — example](../img/x.png)" in md


def test_absolute_image_urls_not_prefixed():
    md = to_md(
        """
        :C a owl:Class ; rdfs:label "C" ;
            :exampleImage <https://cdn.example.com/x.png> .
        """,
        asset_prefix="../",
    )
    assert "![C — example](https://cdn.example.com/x.png)" in md


def test_iri_image_absolutised_against_base_is_left_untouched():
    # This mirrors the real ADIRO ontologies: an ``@base`` turns a relative IRI
    # into an absolute published URL, which must NOT receive the asset prefix.
    md = to_md(
        """
        @base <https://site.example/ADIRO/> .
        :C a owl:Class ; rdfs:label "C" ; :exampleImage <img/x.png> .
        """,
        asset_prefix="../",
    )
    assert "![C — example](https://site.example/ADIRO/img/x.png)" in md


def test_example_images_deduplicated_preserving_order():
    md = to_md(
        """
        :C a owl:Class ; rdfs:label "C" ;
            :exampleImage "img/a.png" , "img/b.png" , "img/a.png" .
        """
    )
    assert md.count("![C — example](img/a.png)") == 1
    assert md.index("img/a.png") < md.index("img/b.png")


def test_example_image_predicate_in_arbitrary_namespace():
    md = to_md(
        """
        @prefix ex: <https://other.example/ns#> .
        :C a owl:Class ; rdfs:label "C" ; ex:exampleImage "img/z.png" .
        """
    )
    assert "![C — example](img/z.png)" in md


def test_explicit_example_predicate_overrides_detection():
    graph = Graph()
    graph.parse(
        data=PREFIXES
        + ":C a owl:Class ; rdfs:label 'C' ; :exampleImage <img/x.png> .",
        format="turtle",
    )
    # Point the converter at a *different* predicate: nothing should match.
    conv = MarkdownConverter(
        example_image_predicates={"https://example.org/onto#somethingElse"}
    )
    md = conv.convert(graph)
    assert "Example images" not in md


# --------------------------------------------------------------------------
# Restrictions & cardinalities
# --------------------------------------------------------------------------


def test_min_qualified_cardinality_restriction():
    md = to_md(
        """
        :Note a owl:Class ; rdfs:label "Note" .
        :Sheet a owl:Class ; rdfs:label "Sheet" ;
            rdfs:subClassOf [ a owl:Restriction ;
                owl:onProperty :contains ;
                owl:onClass :Note ;
                owl:minQualifiedCardinality "0"^^xsd:nonNegativeInteger ] .
        :contains a owl:ObjectProperty ; rdfs:label "contains" .
        """
    )
    assert "**Restrictions:**" in md
    assert "[contains](#contains) min 0 [Note](#Note)" in md


def test_exact_qualified_cardinality_restriction():
    md = to_md(
        """
        :T a owl:Class ; rdfs:label "T" .
        :Sheet a owl:Class ; rdfs:label "Sheet" ;
            rdfs:subClassOf [ a owl:Restriction ;
                owl:onProperty :has ;
                owl:onClass :T ;
                owl:qualifiedCardinality "1"^^xsd:nonNegativeInteger ] .
        :has a owl:ObjectProperty ; rdfs:label "has" .
        """
    )
    assert "[has](#has) exactly 1 [T](#T)" in md


def test_some_values_from_restriction():
    md = to_md(
        """
        :T a owl:Class ; rdfs:label "T" .
        :Sheet a owl:Class ; rdfs:label "Sheet" ;
            rdfs:subClassOf [ a owl:Restriction ;
                owl:onProperty :has ; owl:someValuesFrom :T ] .
        :has a owl:ObjectProperty ; rdfs:label "has" .
        """
    )
    assert "[has](#has) some [T](#T)" in md


# --------------------------------------------------------------------------
# Class expressions: unions, enumerations
# --------------------------------------------------------------------------


def test_union_domain_rendered():
    md = to_md(
        """
        :A a owl:Class ; rdfs:label "A" .
        :B a owl:Class ; rdfs:label "B" .
        :p a owl:ObjectProperty ; rdfs:label "p" ;
            rdfs:domain [ a owl:Class ; owl:unionOf ( :A :B ) ] .
        """
    )
    assert "- **Domain:** ([A](#A) or [B](#B))" in md


def test_one_of_enumeration_on_class():
    md = to_md(
        """
        :Orientation a owl:Class ; rdfs:label "Orientation" ;
            owl:oneOf ( :H :V ) .
        :H a owl:NamedIndividual ; rdfs:label "H" .
        :V a owl:NamedIndividual ; rdfs:label "V" .
        """
    )
    assert "**One of:**" in md
    assert "[H](#H)" in md and "[V](#V)" in md


# --------------------------------------------------------------------------
# Properties
# --------------------------------------------------------------------------


def test_object_property_domain_range_subproperty_inverse():
    md = to_md(
        """
        :A a owl:Class ; rdfs:label "A" .
        :B a owl:Class ; rdfs:label "B" .
        :contains a owl:ObjectProperty ; rdfs:label "contains" .
        :hasPart a owl:ObjectProperty ; rdfs:label "hasPart" ;
            rdfs:comment "Part relation." ;
            rdfs:subPropertyOf :contains ;
            rdfs:domain :A ; rdfs:range :B ;
            owl:inverseOf :contains .
        """
    )
    assert "## Object Properties" in md
    assert "- **Sub property of:** [contains](#contains)" in md
    assert "- **Domain:** [A](#A)" in md
    assert "- **Range:** [B](#B)" in md
    assert "- **Inverse of:** [contains](#contains)" in md


def test_datatype_property_range_is_curie():
    md = to_md(
        """
        :A a owl:Class ; rdfs:label "A" .
        :name a owl:DatatypeProperty ; rdfs:label "name" ;
            rdfs:domain :A ; rdfs:range xsd:string .
        """
    )
    assert "## Datatype Properties" in md
    assert "- **Range:** `xsd:string`" in md


def test_functional_property_characteristic():
    md = to_md(
        """
        :p a owl:ObjectProperty , owl:FunctionalProperty ; rdfs:label "p" .
        """
    )
    assert "- **Characteristics:** Functional" in md


# --------------------------------------------------------------------------
# Individuals & custom annotations
# --------------------------------------------------------------------------


def test_named_individual_with_type():
    md = to_md(
        """
        :Orientation a owl:Class ; rdfs:label "Orientation" .
        :Horizontal a owl:NamedIndividual , :Orientation ; rdfs:label "Horizontal" .
        """
    )
    assert "## Named Individuals" in md
    assert "### Horizontal {#Horizontal}" in md
    assert "- **Type:** [Orientation](#Orientation)" in md


def test_custom_annotation_surfaced():
    md = to_md(
        """
        :labellableRoot a owl:AnnotationProperty ; rdfs:label "Labellable root" .
        :C a owl:Class ; rdfs:label "C" ; :labellableRoot "true"^^xsd:boolean .
        """
    )
    assert "- **Labellable root:** true" in md


# --------------------------------------------------------------------------
# Cross-references to external ontologies
# --------------------------------------------------------------------------


def test_external_superclass_rendered_as_code_not_link():
    md = to_md(
        """
        @prefix ext: <https://external.example/vocab#> .
        :Dog a owl:Class ; rdfs:label "Dog" ; rdfs:subClassOf ext:Animal .
        """
    )
    # Not defined in this ontology -> code span, no anchor link.
    assert "- **Sub class of:** `ext:Animal`" in md
    assert "[Animal]" not in md


# --------------------------------------------------------------------------
# convert_file round-trip & helpers
# --------------------------------------------------------------------------


def test_convert_file_round_trip(tmp_path):
    ttl = tmp_path / "onto.ttl"
    ttl.write_text(
        PREFIXES + ":C a owl:Class ; rdfs:label 'C' ; rdfs:comment 'Hi.' .",
        encoding="utf-8",
    )
    md = convert_file(ttl, asset_prefix="../")
    assert "### C {#C}" in md
    assert "Hi." in md


@pytest.mark.parametrize(
    "iri,expected",
    [
        ("https://example.org/onto#Foo", "Foo"),
        ("https://example.org/onto/Bar", "Bar"),
        ("http://www.w3.org/2001/XMLSchema#string", "string"),
    ],
)
def test_local_name_helper(iri, expected):
    assert local_name(iri) == expected
