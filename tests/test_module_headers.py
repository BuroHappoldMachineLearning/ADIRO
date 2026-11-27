"""Each live module's header carries the metadata vocabulary catalogues read (#284): one description, the prefix and the
namespace (vann), and the dates of its first release and its last change."""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def live_modules():
    rdflib = pytest.importorskip("rdflib")
    for path in sorted((ROOT / "src").glob("*.ttl")):
        graph = rdflib.Graph().parse(str(path), format="turtle")
        ontology = next(graph.subjects(rdflib.RDF.type, rdflib.OWL.Ontology))
        if (ontology, rdflib.OWL.deprecated, None) not in graph:
            yield path.stem, graph, ontology


def one(graph, subject, prop):
    values = list(graph.objects(subject, prop))
    assert len(values) == 1, (subject, prop, values)
    return values[0]


def test_the_description_is_the_introduction():
    """Catalogues show dcterms:description, the documentation shows rdfs:comment: one text, so they cannot disagree."""
    rdflib = pytest.importorskip("rdflib")
    for module, graph, ontology in live_modules():
        assert str(one(graph, ontology, rdflib.DCTERMS.description)) == str(one(graph, ontology, rdflib.RDFS.comment)), module


def test_the_prefix_and_the_namespace_are_declared():
    rdflib = pytest.importorskip("rdflib")
    vann = rdflib.Namespace("http://purl.org/vocab/vann/")
    prefixes = set()
    for module, graph, ontology in live_modules():
        prefix = str(one(graph, ontology, vann.preferredNamespacePrefix))
        assert re.fullmatch(r"ad[a-z]+", prefix), (module, prefix)  # "ad" and the module's role (AGENTS.md)
        assert str(one(graph, ontology, vann.preferredNamespaceUri)) == f"{ontology}#", module
        prefixes.add(prefix)
    assert len(prefixes) == len(list(live_modules())), "each module has its own prefix"


def test_the_dates_are_declared_and_in_order():
    rdflib = pytest.importorskip("rdflib")
    for module, graph, ontology in live_modules():
        issued, modified = one(graph, ontology, rdflib.DCTERMS.issued), one(graph, ontology, rdflib.DCTERMS.modified)
        assert issued.datatype == modified.datatype == rdflib.XSD.date, module
        assert str(issued) <= str(modified), module
