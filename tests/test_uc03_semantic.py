"""Check UC-03 reference roles and the published accepted-target query."""

from pathlib import Path
import re

from rdflib import Graph, Literal, Namespace, RDF, RDFS


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
    assert MD.SheetNoMention in graph.transitive_objects(
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
    graph.add((EX.inline, MD.hasSheetNoMention, EX.sheet_mention))
    graph.add((EX.sheet_mention, MD.denotesDrawingSheet, EX.sheet))
    graph.add((EX.inline, MD.hasLayoutNoMention, EX.layout_number_1))
    graph.add((EX.inline, MD.hasLayoutNoMention, EX.layout_number_3))
    graph.add((EX.inline, MD.inlineReferencesLayout, EX.layout1))

    page = (
        ROOT
        / "docs/specification/use-cases/UC-03/UC-03-Reference Symbol Cross-Sheet Linking.md"
    ).read_text(encoding="utf-8")
    queries = re.findall(r"```sparql\n(.*?)\n```", page, re.DOTALL)
    assert len(queries) == 3

    rows = list(graph.query(queries[2]))
    assert rows == [(EX.layout1,)]
    assert (EX.inline, MD.inlineReferencesLayout, EX.layout3) not in graph
