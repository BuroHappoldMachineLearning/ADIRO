"""An optional label is labellable (#141): the annotation properties carry no reasoning, so the validator checks it."""
import sys
from pathlib import Path

import pytest

pytest.importorskip("rdflib")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from rdflib import Graph  # noqa: E402

import validate_ontology as vo  # noqa: E402

HEAD = """@prefix : <https://ex.org/t#> . @prefix m: <https://w3id.org/adiro/aec_drawing_metadata#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> . @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
"""


def problems(body):
    return vo.find_label_implication_problems(Graph().parse(data=HEAD + body, format="turtle"))


def test_an_optional_label_marked_not_labellable_is_a_problem():
    found = problems(':A a owl:Class ; m:isOptionalLabel "true"^^xsd:boolean ; m:isLabellable "false"^^xsd:boolean .')
    assert len(found) == 1 and found[0].startswith("https://ex.org/t#A:")


def test_an_optional_label_with_no_labellable_mark_is_labellable_by_implication():
    assert problems(':A a owl:Class ; m:isOptionalLabel "true"^^xsd:boolean .') == []
    assert problems(':A a owl:Class ; m:isOptionalLabel "true"^^xsd:boolean ; m:isLabellable "true"^^xsd:boolean .') == []


def test_a_class_that_is_not_an_optional_label_may_be_unlabellable():
    assert problems(':A a owl:Class ; m:isLabellable "false"^^xsd:boolean .') == []
    assert problems(':A a owl:Class ; m:isOptionalLabel "false"^^xsd:boolean ; m:isLabellable "false"^^xsd:boolean .') == []


def test_the_suite_has_no_such_class():
    root = Path(__file__).resolve().parent.parent / "src"
    for ttl in sorted(root.glob("*.ttl")):
        assert vo.find_label_implication_problems(Graph().parse(str(ttl), format="turtle")) == [], ttl.name
