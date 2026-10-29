"""Every UC-01 competency query also runs over named graphs (#241).

A pipeline writes each run's data in a named graph of its own, and corrections in another, and queries them with an engine
that does no reasoning. The UC-01 tests build one graph per case. So that each of them also proves the query works over
named graphs, a recorded UC-01 query run on a plain graph is run a second time on a dataset holding the same triples spread
over three named graphs, queried through the union default graph, and the two answers must be the same rows.
"""
import re
import warnings
import zlib
from collections import Counter
from pathlib import Path

import pytest

ORSD = Path(__file__).resolve().parent.parent / "docs" / "specification" / "use-cases" / "UC-01" / "UC-01-Titleblock-Based Drawing Search.md"
GRAPHS = 3


def recorded_queries():
    return set(re.findall(r"```sparql\n(.*?)```", ORSD.read_text(encoding="utf-8"), re.S))


def spread_over_named_graphs(graph):
    """The triples of `graph` in a dataset of named graphs, each triple placed by its subject, with a union default graph."""
    from rdflib import Dataset, URIRef

    dataset = Dataset(default_union=True)
    for prefix, namespace in graph.namespaces():
        dataset.bind(prefix, namespace)
    for s, p, o in graph:
        name = URIRef(f"https://ex.org/graph/{zlib.crc32(str(s).encode()) % GRAPHS}")
        dataset.graph(name).add((s, p, o))
    return dataset


def answer(result):
    if result.type == "ASK":
        return result.askAnswer
    return Counter(tuple(row) if result.type == "SELECT" else row for row in result)


@pytest.fixture(autouse=True)
def uc01_queries_also_run_over_named_graphs(monkeypatch):
    pytest.importorskip("rdflib")
    from rdflib import Graph

    queries = recorded_queries()
    original = Graph.query

    def query(self, query_object, *args, **kwargs):
        if type(self) is Graph and isinstance(query_object, str) and query_object in queries:
            expected = answer(original(self, query_object, *args, **kwargs))
            with warnings.catch_warnings():  # rdflib's own query code calls its deprecated Dataset.default_context
                warnings.simplefilter("ignore", DeprecationWarning)
                spread = answer(original(spread_over_named_graphs(self), query_object, *args, **kwargs))
            assert spread == expected, f"a UC-01 query answers differently over named graphs:\n{query_object}"
        return original(self, query_object, *args, **kwargs)

    monkeypatch.setattr(Graph, "query", query)
