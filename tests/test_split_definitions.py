"""Splitting an rdfs:comment into a skos:definition and its commentary (#273): nothing retyped, nothing lost."""
import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("rdflib")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from rdflib import Graph, URIRef  # noqa: E402
from rdflib.namespace import RDFS, SKOS  # noqa: E402

import split_definitions as sd  # noqa: E402

NS = "https://w3id.org/adiro/adiro_x#"
MODULE = '''@prefix : <https://w3id.org/adiro/adiro_x#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<https://w3id.org/adiro/adiro_x> rdf:type owl:Ontology ;
    rdfs:comment "The module." .

:Box rdf:type owl:Class ;
    rdfs:label "Box" ;
    rdfs:comment "A box on a page. It holds a \\"value\\" and a unit. Read it with the frame." ;
    rdfs:subClassOf :Thing .

:Thing rdf:type owl:Class ;
    rdfs:label "Thing" ;
    rdfs:comment "Just one sentence about a thing." .

:Other rdf:type owl:Class ;
    rdfs:label "Other" ;
    rdfs:comment "Left alone." .
'''
BOX = "A box on a page."


def write(tmp_path, text=MODULE, crlf=False):
    path = tmp_path / "adiro_x.ttl"
    path.write_bytes((text.replace("\n", "\r\n") if crlf else text).encode("utf-8"))
    return path


def values(path, name, prop):
    return [str(o) for o in Graph().parse(str(path), format="turtle").objects(URIRef(NS + name), prop)]


def test_the_definition_becomes_a_skos_definition_and_the_rest_stays_as_the_comment(tmp_path):
    path = write(tmp_path)
    assert sd.split_file(path, {"Box": BOX}) == ["Box"]
    assert values(path, "Box", SKOS.definition) == [BOX]
    assert values(path, "Box", RDFS.comment) == ['It holds a "value" and a unit. Read it with the frame.']
    assert Graph().parse(str(path), format="turtle").value(URIRef(NS + "Box"), SKOS.definition).language == "en"


def test_a_comment_that_is_only_a_definition_moves_whole_and_leaves_no_comment(tmp_path):
    path = write(tmp_path)
    sd.split_file(path, {"Thing": "Just one sentence about a thing."})
    assert values(path, "Thing", SKOS.definition) == ["Just one sentence about a thing."]
    assert values(path, "Thing", RDFS.comment) == []


def test_nothing_else_changes_and_the_skos_prefix_is_added_once(tmp_path):
    path = write(tmp_path)
    before = Graph().parse(str(path), format="turtle")
    sd.split_file(path, {"Box": BOX})
    after = Graph().parse(str(path), format="turtle")
    assert {s for s, _, _ in (set(before) ^ set(after))} == {URIRef(NS + "Box")}
    assert path.read_text(encoding="utf-8").count("@prefix skos:") == 1
    sd.split_file(path, {"Thing": "Just one sentence about a thing."})
    assert path.read_text(encoding="utf-8").count("@prefix skos:") == 1


def test_line_endings_are_kept(tmp_path):
    path = write(tmp_path, crlf=True)
    sd.split_file(path, {"Box": BOX})
    data = path.read_bytes()
    assert b"\r\n" in data and b"\n" not in data.replace(b"\r\n", b"")


@pytest.mark.parametrize("bad", ["It holds a value.", "A box on  a page.", "a box on a page."])
def test_a_definition_that_is_not_the_start_of_the_comment_word_for_word_is_refused_and_nothing_is_written(tmp_path, bad):
    path = write(tmp_path)
    with pytest.raises(sd.SplitError, match="word for word"):
        sd.split_file(path, {"Box": bad})
    assert path.read_text(encoding="utf-8") == MODULE


def test_a_definition_that_stops_before_the_end_of_its_sentence_is_refused_and_nothing_is_written(tmp_path):
    path = write(tmp_path)
    with pytest.raises(sd.SplitError, match="does not give back the original comment"):
        sd.split_file(path, {"Box": "A box on a page"})  # the full stop would start the commentary
    assert path.read_text(encoding="utf-8") == MODULE


def test_a_term_that_is_unknown_or_split_already_is_refused(tmp_path):
    path = write(tmp_path)
    with pytest.raises(sd.SplitError, match="not a term of this module"):
        sd.split_file(path, {"Missing": "x"})
    sd.split_file(path, {"Box": BOX})
    with pytest.raises(sd.SplitError, match="skos:definition already"):
        sd.split_file(path, {"Box": BOX})


def test_the_terms_still_to_split_are_listed(tmp_path):
    path = write(tmp_path)
    assert sd.terms_without_definition(Graph().parse(str(path), format="turtle")) == ["Box", "Other", "Thing"]
    sd.split_file(path, {"Box": BOX})
    assert sd.terms_without_definition(Graph().parse(str(path), format="turtle")) == ["Other", "Thing"]


def test_the_command_line_checks_without_writing_and_reports_an_error(tmp_path, capsys):
    path = write(tmp_path)
    mapping = tmp_path / "map.json"
    mapping.write_text(json.dumps({"Box": BOX}), encoding="utf-8")
    assert sd.main([str(path), str(mapping), "--check"]) == 0
    assert path.read_text(encoding="utf-8") == MODULE and "Checked 1 term" in capsys.readouterr().out
    mapping.write_text(json.dumps({"Box": "Nope."}), encoding="utf-8")
    assert sd.main([str(path), str(mapping)]) == 1 and "[ERROR]" in capsys.readouterr().err
