"""The outcome and the acceptance of a field assertion (#187, decided in #85 and #179)."""
from pathlib import Path

import pytest

pytest.importorskip("rdflib")
from rdflib import Graph, Namespace  # noqa: E402
from rdflib.collection import Collection  # noqa: E402
from rdflib.namespace import OWL, RDF, RDFS, XSD  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
APROV = Namespace("https://w3id.org/adiro/aec_provenance#")
PROV = Namespace("http://www.w3.org/ns/prov#")
G = Graph().parse(str(ROOT / "src" / "aec_provenance.ttl"), format="turtle")


def members(cls):
    return set(Collection(G, G.value(cls, OWL.oneOf)))


def test_the_outcome_is_a_closed_list_that_follows_the_ground_truth_statuses():
    # present is a value; empty, illegible and absent are the ground-truth observation statuses; not found is a model's
    assert members(APROV.AssertionOutcome) == {APROV.Empty, APROV.Illegible, APROV.NotPrinted, APROV.NotFound}
    assert (APROV.Present, None, None) not in G, "a value is its own outcome: there is no 'present' individual"


def test_the_acceptance_is_a_closed_list_of_three():
    assert members(APROV.AcceptanceStatus) == {APROV.Pending, APROV.Accepted, APROV.Rejected}


def test_every_individual_is_typed_labelled_and_described():
    for cls in (APROV.AssertionOutcome, APROV.AcceptanceStatus):
        for individual in members(cls):
            assert (individual, RDF.type, OWL.NamedIndividual) in G and (individual, RDF.type, cls) in G
            assert G.value(individual, RDFS.label) and G.value(individual, RDFS.comment), individual


def test_the_properties_belong_to_a_field_assertion_and_are_per_assertion():
    expected = {
        "hasOutcome": APROV.AssertionOutcome, "hasAcceptance": APROV.AcceptanceStatus, "acceptedBy": PROV.Agent,
        "acceptedAt": XSD.dateTime, "acceptedUnder": XSD.anyURI, "supersedes": APROV.FieldAssertion,
    }
    for name, rng in expected.items():
        assert G.value(APROV[name], RDFS.domain) == APROV.FieldAssertion, name
        assert G.value(APROV[name], RDFS.range) == rng, name


def test_the_promotion_comment_says_it_is_for_an_accepted_assertion_with_a_value():
    comment = str(G.value(APROV.mapsToFieldProperty, RDFS.comment))
    assert "accepted" in comment and "has a value" in comment
    assert "supersedes" in str(G.value(APROV.FieldAssertion, RDFS.comment))


def test_supersedes_is_related_to_prov_by_annotation_only():
    assert (APROV.supersedes, RDFS.subPropertyOf, None) not in G
