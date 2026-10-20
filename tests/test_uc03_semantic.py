"""Check UC-03 reference roles and the published accepted-target query."""

from pathlib import Path
import re

import pytest
from rdflib import Graph, Literal, Namespace, RDF, RDFS, OWL


ROOT = Path(__file__).resolve().parents[1]
MD = Namespace("https://w3id.org/adiro/aec_drawing_metadata#")
CS = Namespace("https://w3id.org/adiro/aec_common_symbols#")
EX = Namespace("https://example.org/adiro/uc03-check#")


def load_semantic_modules() -> Graph:
    graph = Graph()
    graph.parse(ROOT / "src/aec_drawing_metadata.ttl", format="turtle")
    graph.parse(ROOT / "src/aec_common_symbols.ttl", format="turtle")
    return graph


def test_reference_forms_keep_symbol_and_inline_domains_distinct() -> None:
    graph = load_semantic_modules()

    assert MD.ReferenceExpression in graph.transitive_objects(
        CS.ReferenceSymbol, RDFS.subClassOf
    )
    assert MD.DrawingIdentifierMention in graph.transitive_objects(
        MD.StandaloneSheetReference, RDFS.subClassOf
    )
    assert MD.ReferenceExpression in graph.transitive_objects(
        MD.StandaloneSheetReference, RDFS.subClassOf
    )
    assert CS.ReferenceSymbol not in graph.transitive_objects(
        MD.InlineLayoutSheetReference, RDFS.subClassOf
    )
    assert (MD.inlineReferencesLayout, RDFS.domain, MD.InlineLayoutSheetReference) in graph
    assert (CS.referencesLayout, RDFS.domain, CS.ReferenceSymbol) in graph


def test_published_inline_query_returns_only_accepted_targets() -> None:
    graph = load_semantic_modules()
    graph.add((EX.sheet, MD.drawingIdentifier, Literal("S601")))
    graph.add((EX.sheet, MD.hasLayout, EX.layout1))
    graph.add((EX.sheet, MD.hasLayout, EX.layout3))
    graph.add((EX.inline, RDF.type, MD.InlineLayoutSheetReference))
    graph.add((EX.inline, MD.contains, EX.sheet_mention))
    graph.add((EX.sheet_mention, RDF.type, MD.DrawingIdentifierMention))
    graph.add((EX.sheet_mention, MD.denotesDrawingSheet, EX.sheet))
    graph.add((EX.inline, MD.contains, EX.layout_number_1))
    graph.add((EX.inline, MD.contains, EX.layout_number_3))
    graph.add((EX.inline, MD.inlineReferencesLayout, EX.layout1))

    page = (
        ROOT
        / "docs/specification/use-cases/UC-03/UC-03-Reference Symbol Cross-Sheet Linking.md"
    ).read_text(encoding="utf-8")
    match = re.search(r"\*\*CQ 4\.2[^\n]*\n+```sparql\n(.*?)\n```", page, re.DOTALL)
    assert match, "CQ 4.2 query not found under its heading"

    rows = list(graph.query(match.group(1)))
    assert rows == [(EX.layout1,)]
    assert (EX.inline, MD.inlineReferencesLayout, EX.layout3) not in graph


def test_unrelated_symbols_keep_drawing_element_superclass() -> None:
    graph = load_semantic_modules()
    assert (CS.Dimension, RDFS.subClassOf, MD.DrawingElement) in graph
    assert (CS.Dimension, RDFS.subClassOf, MD.ReferenceExpression) not in graph


def test_sheet_mention_has_no_geometry_restriction() -> None:
    graph = load_semantic_modules()
    for value in graph.objects(MD.DrawingIdentifierMention, RDFS.subClassOf):
        assert not list(graph.objects(value, OWL.onProperty))
    graph.add((EX.unlocalised, RDF.type, MD.DrawingIdentifierMention))
    graph.add((EX.unlocalised, MD.denotesDrawingSheet, EX.sheet))
    assert list(graph.query('SELECT ?s WHERE { ?s <https://w3id.org/adiro/aec_drawing_metadata#denotesDrawingSheet> <https://example.org/adiro/uc03-check#sheet> }'))


if __name__ == '__main__':
    pytest.main([__file__])


def test_the_source_layout_of_a_reference_expression_is_contains_from_the_layout() -> None:
    """appearsOnLayout (#170) said what `contains` from the layout already says, and was removed."""
    graph = load_semantic_modules()
    assert (MD.appearsOnLayout, RDF.type, OWL.ObjectProperty) not in graph

    # a standalone sheet reference and a graphical marker are both found from their layout with `contains`, and back with ^contains
    graph.parse(
        data=f"""@prefix md: <{MD}> . @prefix cs: <{CS}> . @prefix ex: <{EX}> .
ex:layout md:contains ex:standalone , ex:marker . ex:standalone a md:StandaloneSheetReference . ex:marker a cs:ReferenceSymbol .""",
        format="turtle",
    )
    found = {
        str(r[0]).rsplit("#", 1)[-1]
        for r in graph.query(
            f"""PREFIX md: <{MD}>
SELECT ?e WHERE {{ ?e a/<{RDFS.subClassOf}>* md:ReferenceExpression . ?e ^md:contains ?layout }}"""
        )
    }
    assert found == {"standalone", "marker"}
