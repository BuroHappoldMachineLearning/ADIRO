"""The rename of the aec_* modules to adiro_* (#171, step 3): the new modules, the migration and what follows them."""
import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("rdflib")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from rdflib import Graph, Literal, URIRef  # noqa: E402
from rdflib.compare import graph_diff, to_isomorphic  # noqa: E402
from rdflib.namespace import OWL, RDF, RDFS  # noqa: E402

import compat_diff as cd  # noqa: E402
import migrate_aec_to_adiro as mig  # noqa: E402
import module_renames as mr  # noqa: E402

W3ID = mr.BASE
RENAMES = mr.load(ROOT)
PAIRS = sorted((old, new) for new, old in RENAMES.items() if (ROOT / "src" / f"{new}.ttl").is_file())


def parse(path):
    return Graph().parse(str(path), format="turtle")


def first_release(new):
    """The new module as the rename made it: its first release once published, else src/ (the rename is not released yet).

    src/ moves on after that release (new terms, new definitions), so a test of the rename compares the first release.
    """
    import ontology_versions as ov

    released = ov.archived_versions(ROOT, new)
    if released:
        return ROOT / "versions" / new / released[0] / f"{new}.ttl"
    return ROOT / "src" / f"{new}.ttl"


@pytest.mark.parametrize("old,new", PAIRS)
def test_the_new_module_is_the_old_final_release_under_the_new_names(old, new):
    """Apart from its header and the module names its definitions mention, a new module is its predecessor's final release."""
    final = mr.rewrite_graph(parse(cd.latest_snapshot(ROOT, old)), RENAMES)
    current = parse(first_release(new))
    ontology = URIRef(W3ID + new)
    _, only_final, only_current = graph_diff(to_isomorphic(final), to_isomorphic(current))

    def unexplained(triples):
        out = set()
        for s, p, o in triples:
            if s == ontology:
                continue  # the header: title, label, version, replaces / deprecated
            if p in (RDFS.comment, OWL.versionInfo) and isinstance(o, Literal):
                continue  # a definition whose prose names a module: compared below
            out.add((s, p, o))
        return out

    assert unexplained(only_final) == set() and unexplained(only_current) == set()
    comments = lambda g: {(s, mr.rewrite_text(str(o), RENAMES).replace("aec_", "adiro_")) for s, o in g.subject_objects(RDFS.comment)
                          if s != ontology}
    assert comments(final) == comments(current), "a definition differs by more than the module names it mentions"


@pytest.mark.parametrize("old,new", PAIRS)
def test_the_new_module_continues_the_old_numbering_and_replaces_it(old, new):
    """The first release of a new module is the old final + 1 MAJOR.

    Before the release cut, src/ declares the old final (the cut bumps it, as decided on #171); after the cut, the next
    version; once released, that is the version of its first snapshot.
    """
    first = first_release(new)
    current = parse(first)
    ontology = URIRef(W3ID + new)
    final_version = cd.version_of(parse(cd.latest_snapshot(ROOT, old)))
    next_version = cd.apply_bump(final_version, cd.BUMP_MAJOR)
    declared = str(current.value(ontology, OWL.versionInfo))
    if first != ROOT / "src" / f"{new}.ttl":  # released
        assert declared == next_version, "the first release of a renamed module is the old final + 1 MAJOR"
    else:
        assert declared in (final_version, next_version), "before the cut: the old final; after it: + 1 MAJOR"
        result = cd.analyze_module(ROOT, new)
        assert result["renamed_from"] == old and result["required_bump"] == cd.BUMP_MAJOR
        assert result["prospective_version"] == next_version
    assert (ontology, URIRef("http://purl.org/dc/terms/replaces"), URIRef(W3ID + old)) in current
    assert (ontology, OWL.deprecated, None) not in current
    assert str(current.value(ontology, RDFS.label)).startswith("ADIRO ")


@pytest.mark.parametrize("old,new", PAIRS)
def test_the_new_module_names_no_old_module_except_its_history(old, new):
    text = (ROOT / "src" / f"{new}.ttl").read_text(encoding="utf-8")
    for line in text.splitlines():
        if "aec_" in line:
            assert "owl:priorVersion" in line or "dcterms:replaces" in line, line


def test_the_published_mapping_is_up_to_date_and_complete():
    committed = (ROOT / mig.MAPPING).read_text(encoding="utf-8").replace("\r\n", "\n")
    assert committed == mig.mapping_turtle(ROOT), "regenerate it: uv run python scripts/migrate_aec_to_adiro.py mapping"
    graph = Graph().parse(data=committed, format="turtle")
    replaced = {str(s): str(o) for s, _, o in graph}
    for old, new in PAIRS:
        assert replaced[W3ID + old] == W3ID + new
        current = parse(first_release(new))  # a term added after the rename has no old IRI
        defined = {str(s) for s in current.subjects(RDF.type, None) if str(s).startswith(W3ID + new + "#")}
        assert {mr.rename_iri(o, RENAMES) for o in replaced if o.startswith(W3ID + old + "#")} >= defined


def test_links_are_rewritten_but_a_release_keeps_its_iri():
    text = ("<https://w3id.org/adiro/aec_geometry#BoundingBox> https://w3id.org/adiro/aec_geometry "
            "https://w3id.org/adiro/aec_geometry/2.0.0 https://w3id.org/adiro/aec_geometry/2.0.0/aec_geometry.ttl "
            "https://w3id.org/adiro/aec_drawing_metadata/exampleImage/Titleblock_01.png https://w3id.org/adiro/aec_geometry_x "
            "https://w3id.org/adiro/contribute/")
    assert mig.rewrite_text(text, ROOT).split() == [
        "<https://w3id.org/adiro/adiro_geometry#BoundingBox>", "https://w3id.org/adiro/adiro_geometry",
        "https://w3id.org/adiro/aec_geometry/2.0.0", "https://w3id.org/adiro/aec_geometry/2.0.0/aec_geometry.ttl",
        "https://w3id.org/adiro/adiro_drawing_metadata/exampleImage/Titleblock_01.png", "https://w3id.org/adiro/aec_geometry_x",
        "https://w3id.org/adiro/contribute/"]


def test_a_graph_is_rewritten_in_its_own_format(tmp_path):
    source = tmp_path / "data.ttl"
    source.write_text(
        "@prefix geom: <https://w3id.org/adiro/aec_geometry#> .\n"
        "@prefix aprov: <https://w3id.org/adiro/aec_provenance#> .\n"
        "<https://example.org/box1> a geom:BoundingBox ; aprov:hasConfidence 0.9 ;\n"
        "    <http://purl.org/dc/terms/conformsTo> <https://w3id.org/adiro/aec_geometry/2.0.0> .\n", encoding="utf-8")
    mig.main(["rewrite", str(source)])
    out = Graph().parse(str(tmp_path / "data.adiro.ttl"), format="turtle")
    box = URIRef("https://example.org/box1")
    assert (box, RDF.type, URIRef(W3ID + "adiro_geometry#BoundingBox")) in out
    assert (box, URIRef(W3ID + "adiro_provenance#hasConfidence"), None) in out
    assert (box, None, URIRef(W3ID + "aec_geometry/2.0.0")) in out  # the release the data conformed to
    assert "aec_geometry#" not in (tmp_path / "data.adiro.ttl").read_text(encoding="utf-8")


def test_the_new_shapes_and_tooling_read_the_new_namespace():
    import example_images

    assert example_images.PROPERTY_IRI == W3ID + "adiro_drawing_metadata#exampleImage"
    assert W3ID + "aec_drawing_metadata#exampleImage" in example_images.PROPERTY_IRIS  # the old releases are still checked
    for shapes in (ROOT / "data-validation").glob("*.shacl.ttl"):
        assert W3ID + "aec_" not in shapes.read_text(encoding="utf-8"), shapes.name


def test_the_import_pin_covers_the_new_modules():
    pin = json.loads((ROOT / "config" / "module_imports.json").read_text(encoding="utf-8"))
    for old, new in PAIRS:
        assert set(pin[new]) == {mr.successor(RENAMES, k) for k in pin[old]}  # the same imports, under the new names


def quads(path, fmt):
    from rdflib import Dataset

    data = Dataset()
    data.parse(str(path), format=fmt)
    # rdflib 7 yields the graph name, older versions the graph
    return {(str(s), str(p), str(o), str(getattr(c, "identifier", c))) for s, p, o, c in data.quads((None, None, None, None))}


GEOM, PROV = W3ID + "aec_geometry#BoundingBox", W3ID + "aec_provenance#FieldAssertion"
RDF_TYPE = str(RDF.type)
JSONLD_CASES = {
    # only a named graph: read as a single graph, it came out empty (#210 review)
    "named": ('{"@id":"https://example.org/evidence","@graph":[{"@id":"https://example.org/box","@type":"%s"}]}' % GEOM,
              {("https://example.org/box", RDF_TYPE, W3ID + "adiro_geometry#BoundingBox", "https://example.org/evidence")}),
    # a default graph and a named graph: the named one was lost
    "mixed": ('[{"@id":"https://example.org/a","@type":"%s"},'
              '{"@id":"https://example.org/g","@graph":[{"@id":"https://example.org/b","@type":"%s"}]}]' % (GEOM, PROV),
              {("https://example.org/a", RDF_TYPE, W3ID + "adiro_geometry#BoundingBox", "urn:x-rdflib:default"),
               ("https://example.org/b", RDF_TYPE, W3ID + "adiro_provenance#FieldAssertion", "https://example.org/g")}),
}


@pytest.mark.parametrize("case", sorted(JSONLD_CASES))
@pytest.mark.parametrize("suffix", [".jsonld", ".json"])
def test_json_ld_keeps_its_default_and_named_graphs(tmp_path, case, suffix):
    text, expected = JSONLD_CASES[case]
    source = tmp_path / f"data{suffix}"
    source.write_text(text, encoding="utf-8")
    mig.main(["rewrite", str(source)])
    assert quads(tmp_path / f"data.adiro{suffix}", "json-ld") == expected


def test_trig_rewrites_a_graph_named_by_an_old_iri(tmp_path):
    source = tmp_path / "data.trig"
    source.write_text(
        "<https://w3id.org/adiro/aec_geometry#Frames> { <https://example.org/f> a <https://w3id.org/adiro/aec_geometry#CoordinateFrame> }\n"
        "<https://example.org/x> a <https://w3id.org/adiro/aec_geometry#BoundingBox> .\n", encoding="utf-8")
    mig.main(["rewrite", str(source)])
    assert quads(tmp_path / "data.adiro.trig", "trig") == {
        ("https://example.org/f", RDF_TYPE, W3ID + "adiro_geometry#CoordinateFrame", W3ID + "adiro_geometry#Frames"),
        ("https://example.org/x", RDF_TYPE, W3ID + "adiro_geometry#BoundingBox", "urn:x-rdflib:default")}
