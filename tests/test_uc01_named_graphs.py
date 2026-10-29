"""The check that every UC-01 competency query also runs over named graphs (#241, tests/conftest.py) is a real check."""
import pytest

pytest.importorskip("rdflib")
from rdflib import Graph  # noqa: E402

from conftest import recorded_queries, spread_over_named_graphs  # noqa: E402

DATA = """@prefix : <https://ex.org/d#> .
@prefix metadata: <https://w3id.org/adiro/adiro_drawing_metadata#> .
:d1 a metadata:DrawingSheet ; metadata:drawingIdentifier "ST-101" .
:d2 a metadata:DrawingSheet ; metadata:drawingIdentifier "ST-102" .
:d3 a metadata:DrawingSheet ; metadata:drawingIdentifier "ST-103" .
"""


def test_the_triples_are_spread_over_several_named_graphs_and_the_union_holds_them_all():
    graph = Graph().parse(data=DATA, format="turtle")
    dataset = spread_over_named_graphs(graph)
    named = [g for g in dataset.graphs() if len(g)]
    assert len(named) > 1
    assert sum(len(g) for g in named) == len(graph)


def test_a_query_that_joins_inside_one_graph_would_be_caught():
    # a GRAPH pattern pairing two drawings finds the 6 ordered pairs only when both are in one graph: spread over
    # named graphs it finds fewer, so a recorded query written this way would answer differently and fail the check
    query = "SELECT ?d WHERE { GRAPH ?g { ?d a ?type . ?other a ?type . FILTER (?d != ?other) } }"
    graph = Graph().parse(data=DATA, format="turtle")
    assert len(list(spread_over_named_graphs(graph).query(query))) < 6


def test_every_uc01_query_has_a_test_that_runs_it():
    import re
    from pathlib import Path

    tests = "".join(p.read_text(encoding="utf-8") for p in Path(__file__).parent.glob("test_*.py"))
    markers = {re.search(r"^# (CQ [\d.]+|Promotion)", q, re.M).group(1) for q in recorded_queries() if re.search(r"^# (CQ [\d.]+|Promotion)", q, re.M)}
    untested = sorted(m for m in markers if f'"# {m}"' not in tests)
    assert untested == [], f"recorded UC-01 queries no test runs, so the named-graph check never sees them: {untested}"
