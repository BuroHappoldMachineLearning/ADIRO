"""Regression tests for the compatibility-diff classifier (scripts/compat_diff.py, RES-67).

Covers the spec's Minimal Test Matrix. Skips cleanly where rdflib is unavailable.
"""
import sys
from pathlib import Path

import pytest

pytest.importorskip("rdflib")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from rdflib import Graph  # noqa: E402
import compat_diff as cd  # noqa: E402

BASE = """@prefix : <https://ex.org/m#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
<https://ex.org/m> a owl:Ontology ; owl:versionInfo "1.0.0" .
:A a owl:Class .
:p a owl:ObjectProperty ; rdfs:domain :A ; rdfs:range :A .
"""
R0 = BASE + ':A rdfs:subClassOf [ a owl:Restriction ; owl:onProperty :p ; owl:minCardinality "0"^^xsd:nonNegativeInteger ] .\n'
R1 = BASE + ':A rdfs:subClassOf [ a owl:Restriction ; owl:onProperty :p ; owl:minCardinality "1"^^xsd:nonNegativeInteger ] .\n'


def _deltas(old_ttl, new_ttl):
    def syms(ttl):
        g = Graph()
        g.parse(data=ttl, format="turtle")
        return cd.build_symbols(g)

    return cd.compute_deltas(syms(old_ttl), syms(new_ttl))


@pytest.mark.parametrize(
    "name,old,new,expected_type,expected_bump",
    [
        ("add-only", BASE, BASE + ":B a owl:Class .\n", "TERM_ADDED", cd.BUMP_MINOR),
        ("remove", BASE + ":B a owl:Class .\n", BASE, "TERM_REMOVED", cd.BUMP_MAJOR),
        ("type-change", BASE, BASE.replace(":p a owl:ObjectProperty", ":p a owl:DatatypeProperty"), "TYPE_CHANGED", cd.BUMP_MAJOR),
        ("annotation-only", BASE, BASE.replace(":A a owl:Class .", ':A a owl:Class ; rdfs:label "A" .'), "ANNOTATION_CHANGED", cd.BUMP_PATCH),
        ("tighten", R0, R1, "RESTRICTION_TIGHTENED", cd.BUMP_MAJOR),
        ("loosen", R1, R0, "RESTRICTION_LOOSENED", cd.BUMP_MINOR),
    ],
)
def test_matrix(name, old, new, expected_type, expected_bump):
    deltas = _deltas(old, new)
    types = {t for t, _ in deltas}
    assert expected_type in types, f"{name}: expected {expected_type} in {sorted(types)}"
    assert cd.required_bump(deltas) == expected_bump, f"{name}: bump"


def test_no_change_needs_no_bump():
    assert cd.required_bump(_deltas(BASE, BASE)) == cd.BUMP_NONE


def test_declared_bump():
    assert cd.declared_bump("1.0.0", "1.1.0") == cd.BUMP_MINOR
    assert cd.declared_bump("1.0.0", "2.0.0") == cd.BUMP_MAJOR
    assert cd.declared_bump("2.0.0", "2.0.0") == cd.BUMP_NONE
    assert cd.declared_bump("2.0.0", "1.0.0") == "decreased"


def test_apply_bump():
    assert cd.apply_bump("2.0.0", cd.BUMP_MAJOR) == "3.0.0"
    assert cd.apply_bump("1.2.3", cd.BUMP_MINOR) == "1.3.0"
    assert cd.apply_bump("1.2.3", cd.BUMP_PATCH) == "1.2.4"
    assert cd.apply_bump("1.2.3", cd.BUMP_NONE) == "1.2.3"
    assert cd.apply_bump("not-semver", cd.BUMP_MAJOR) is None


def test_prospective_version_in_markdown():
    # add-only against a baseline -> MINOR -> next version bumps the minor.
    # versionInfo not yet bumped (accumulation) -> RELEASE_PENDING, not a warning.
    results = [
        {
            "module": "m", "status": "analyzed", "old_version": "1.0.0",
            "new_version": "1.0.0", "required_bump": cd.BUMP_MINOR,
            "declared_bump": cd.BUMP_NONE, "prospective_version": "1.1.0",
            "verdict": "RELEASE_PENDING", "deltas": [("TERM_ADDED", "https://ex.org/m#B")],
        }
    ]
    md = cd.to_markdown(results)
    assert "1.1.0" in md and "MINOR" in md and "RELEASE_PENDING" in md
    # accumulation forecast must NOT raise the insufficient-bump warning
    assert "smaller than the change requires" not in md


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
