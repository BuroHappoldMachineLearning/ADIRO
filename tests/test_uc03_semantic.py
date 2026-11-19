"""Check UC-03 reference roles and the published accepted-target query."""

from pathlib import Path
import re

import pytest
from rdflib import DCTERMS, Graph, Literal, Namespace, RDF, RDFS, OWL


ROOT = Path(__file__).resolve().parents[1]
MD = Namespace("https://w3id.org/adiro/adiro_drawing_metadata#")
CS = Namespace("https://w3id.org/adiro/adiro_drawing_symbology#")
EX = Namespace("https://example.org/adiro/uc03-check#")


def load_semantic_modules() -> Graph:
    graph = Graph()
    graph.parse(ROOT / "src/adiro_drawing_metadata.ttl", format="turtle")
    graph.parse(ROOT / "src/adiro_drawing_symbology.ttl", format="turtle")
    return graph


def test_reference_forms_keep_symbol_and_inline_domains_distinct() -> None:
    graph = load_semantic_modules()

    assert CS.ReferenceExpression in graph.transitive_objects(
        CS.ReferenceSymbol, RDFS.subClassOf
    )
    assert CS.DrawingIdentifierMention in graph.transitive_objects(
        CS.StandaloneDrawingReference, RDFS.subClassOf
    )
    assert CS.ReferenceExpression in graph.transitive_objects(
        CS.StandaloneDrawingReference, RDFS.subClassOf
    )
    assert CS.ReferenceSymbol not in graph.transitive_objects(
        CS.InlineLayoutDrawingReference, RDFS.subClassOf
    )
    assert (CS.inlineReferencesLayout, RDFS.domain, CS.InlineLayoutDrawingReference) in graph
    assert (CS.referencesLayout, RDFS.domain, CS.ReferenceSymbol) in graph


def test_the_reference_terms_released_in_drawing_metadata_are_deprecated_and_equivalent_to_those_of_drawing_symbology() -> None:
    """The family moved to adiro_drawing_symbology (#277); the released IRIs stay, and the two sheet names became drawing names (#271)."""
    graph = load_semantic_modules()

    classes = {"ReferenceExpression": "ReferenceExpression", "DrawingIdentifierMention": "DrawingIdentifierMention",
               "LayoutIdentifierMention": "LayoutIdentifierMention", "InlineLayoutSheetReference": "InlineLayoutDrawingReference",
               "StandaloneSheetReference": "StandaloneDrawingReference"}
    properties = {"denotesDrawingSheet": "denotesDrawingSheet", "inlineReferencesLayout": "inlineReferencesLayout"}
    for old, new in {**classes, **properties}.items():
        assert (MD[old], OWL.deprecated, Literal(True)) in graph
        assert (MD[old], DCTERMS.isReplacedBy, CS[new]) in graph
        assert (MD[old], MD.isComputerVisionLabel, None) not in graph
        assert (MD[old], MD.exampleImage, None) not in graph
    for old, new in classes.items():
        assert (MD[old], OWL.equivalentClass, CS[new]) in graph
        assert (CS[new], RDF.type, OWL.Class) in graph
    for old, new in properties.items():
        assert (MD[old], OWL.equivalentProperty, CS[new]) in graph
        assert (CS[new], RDF.type, OWL.ObjectProperty) in graph
    # the two names that never were released are defined once, in the new module
    assert (MD.InlineLayoutDrawingReference, None, None) not in graph
    assert (MD.StandaloneDrawingReference, None, None) not in graph


def test_every_reference_class_is_defined_in_the_module_that_holds_the_reference_symbol() -> None:
    graph = load_semantic_modules()
    family = {CS.ReferenceExpression, CS.DrawingIdentifierMention, CS.LayoutIdentifierMention,
              CS.InlineLayoutDrawingReference, CS.StandaloneDrawingReference, CS.ReferenceSymbol}
    for term in family:
        assert (term, RDF.type, OWL.Class) in graph
        assert (term, MD.isComputerVisionLabel, Literal(True)) in graph
    assert (CS.ReferenceExpression, RDFS.subClassOf, MD.DrawingElement) in graph
    # a mention is a component, not a complete reference
    assert CS.ReferenceExpression not in set(graph.transitive_objects(CS.DrawingIdentifierMention, RDFS.subClassOf))
    assert CS.ReferenceExpression not in set(graph.transitive_objects(CS.LayoutIdentifierMention, RDFS.subClassOf))


def test_published_inline_query_returns_only_accepted_targets() -> None:
    graph = load_semantic_modules()
    graph.add((EX.sheet, MD.drawingIdentifier, Literal("S601")))
    graph.add((EX.sheet, MD.hasLayout, EX.layout1))
    graph.add((EX.sheet, MD.hasLayout, EX.layout3))
    graph.add((EX.inline, RDF.type, CS.InlineLayoutDrawingReference))
    graph.add((EX.inline, MD.contains, EX.sheet_mention))
    graph.add((EX.sheet_mention, RDF.type, CS.DrawingIdentifierMention))
    graph.add((EX.sheet_mention, CS.denotesDrawingSheet, EX.sheet))
    graph.add((EX.inline, MD.contains, EX.layout_number_1))
    graph.add((EX.inline, MD.contains, EX.layout_number_3))
    graph.add((EX.inline, CS.inlineReferencesLayout, EX.layout1))

    page = (
        ROOT
        / "docs/specification/use-cases/UC-03/UC-03-Reference Symbol Cross-Sheet Linking.md"
    ).read_text(encoding="utf-8")
    match = re.search(r"\*\*CQ 4\.2[^\n]*\n+```sparql\n(.*?)\n```", page, re.DOTALL)
    assert match, "CQ 4.2 query not found under its heading"

    rows = list(graph.query(match.group(1)))
    assert rows == [(EX.layout1,)]
    assert (EX.inline, CS.inlineReferencesLayout, EX.layout3) not in graph


def test_unrelated_symbols_keep_drawing_element_superclass() -> None:
    graph = load_semantic_modules()
    assert (CS.Dimension, RDFS.subClassOf, MD.DrawingElement) in graph
    assert (CS.Dimension, RDFS.subClassOf, CS.ReferenceExpression) not in graph


def test_sheet_mention_has_no_geometry_restriction() -> None:
    graph = load_semantic_modules()
    for value in graph.objects(CS.DrawingIdentifierMention, RDFS.subClassOf):
        assert not list(graph.objects(value, OWL.onProperty))
    graph.add((EX.unlocalised, RDF.type, CS.DrawingIdentifierMention))
    graph.add((EX.unlocalised, CS.denotesDrawingSheet, EX.sheet))
    assert list(graph.query('SELECT ?s WHERE { ?s <https://w3id.org/adiro/adiro_drawing_symbology#denotesDrawingSheet> <https://example.org/adiro/uc03-check#sheet> }'))


if __name__ == '__main__':
    pytest.main([__file__])


def test_the_source_layout_of_a_reference_expression_is_contains_from_the_layout() -> None:
    """appearsOnLayout (#170) said what `contains` from the layout already says, and was removed."""
    graph = load_semantic_modules()
    assert (MD.appearsOnLayout, RDF.type, OWL.ObjectProperty) not in graph

    # a standalone drawing reference and a graphical marker are both found from their layout with `contains`, and back with ^contains
    graph.parse(
        data=f"""@prefix md: <{MD}> . @prefix cs: <{CS}> . @prefix ex: <{EX}> .
ex:layout md:contains ex:standalone , ex:marker . ex:standalone a cs:StandaloneDrawingReference . ex:marker a cs:ReferenceSymbol .""",
        format="turtle",
    )
    found = {
        str(r[0]).rsplit("#", 1)[-1]
        for r in graph.query(
            f"""PREFIX md: <{MD}> PREFIX cs: <{CS}>
SELECT ?e WHERE {{ ?e a/<{RDFS.subClassOf}>* cs:ReferenceExpression . ?e ^md:contains ?layout }}"""
        )
    }
    assert found == {"standalone", "marker"}
