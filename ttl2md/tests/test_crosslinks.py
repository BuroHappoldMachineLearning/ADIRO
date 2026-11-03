"""The names of terms written in a definition become links to their documentation (ttl2md.crosslinks)."""

from __future__ import annotations

import textwrap

from rdflib import Graph

from ttl2md import convert_graph, html_link, link_names, targets_for

TARGETS = {
    "FieldAssertion": "#FieldAssertion",
    "errorMessage": "#errorMessage",
    "Layout": "#Layout",
    "Plan": "#Plan",
    "unit": "#unit",
    "prov:Activity": "#Activity",
}


def test_a_camel_case_name_is_linked_at_its_first_mention_only():
    text = "Each recorded as a FieldAssertion; a FieldAssertion has an errorMessage."
    assert link_names(text, TARGETS) == (
        "Each recorded as a [FieldAssertion](#FieldAssertion); a FieldAssertion has an [errorMessage](#errorMessage)."
    )


def test_a_plural_links_the_name_and_keeps_the_s():
    assert link_names("one or more FieldAssertions.", TARGETS) == "one or more [FieldAssertion](#FieldAssertion)s."


def test_a_name_inside_a_longer_word_or_a_prefixed_name_is_not_matched_by_its_bare_name():
    assert link_names("A FieldAssertionKind and ex:FieldAssertion.", TARGETS) == "A FieldAssertionKind and ex:FieldAssertion."


def test_a_prefixed_name_is_linked_and_the_bare_word_is_not_a_target():
    assert link_names("Itself a prov:Activity; an activity.", TARGETS) == "Itself a [prov:Activity](#Activity); an activity."


def test_a_single_capitalised_word_is_linked_mid_sentence():
    assert link_names("A symbol drawn on a Layout.", TARGETS) == "A symbol drawn on a [Layout](#Layout)."


def test_a_single_capitalised_word_is_not_linked_at_the_start_of_a_sentence():
    assert link_names("Layout of the page. Plan it.", TARGETS) == "Layout of the page. Plan it."


def test_the_full_stop_of_an_abbreviation_does_not_start_a_sentence():
    assert link_names("A class (e.g. Layout, i.e. Plan).", TARGETS) == "A class (e.g. [Layout](#Layout), i.e. [Plan](#Plan))."


def test_a_single_capitalised_word_is_not_linked_inside_a_capitalised_phrase():
    text = "A title such as 'Ground Floor Plan' or Plan Markers, on a Layout."
    assert link_names(text, TARGETS) == "A title such as 'Ground Floor Plan' or Plan Markers, on a [Layout](#Layout)."


def test_a_later_mention_is_linked_when_the_first_one_is_not_linkable():
    assert link_names("Plan Markers, then a Plan.", TARGETS) == "Plan Markers, then a [Plan](#Plan)."


def test_a_single_lowercase_word_is_never_linked():
    assert link_names("It fixes the unit of the page.", TARGETS) == "It fixes the unit of the page."


def test_the_term_being_defined_is_not_linked():
    assert link_names("A FieldAssertion with an errorMessage.", TARGETS, skip={"FieldAssertion"}) == (
        "A FieldAssertion with an [errorMessage](#errorMessage)."
    )


def test_urls_code_spans_and_existing_links_are_left_alone():
    text = ("See https://w3id.org/adiro/adiro_provenance#FieldAssertion, `FieldAssertion`, "
            "[FieldAssertion](#x) and <a href=\"#y\">a FieldAssertion</a>.")
    assert link_names(text, TARGETS) == text


def test_linking_twice_changes_nothing():
    once = link_names("Each recorded as a FieldAssertion.", TARGETS, html_link)
    assert once == 'Each recorded as a <a href="#FieldAssertion">FieldAssertion</a>.'
    assert link_names(once, TARGETS, html_link) == once


def test_html_entities_next_to_a_name_do_not_hide_it():
    text = "a &#x27;FieldAssertion&#x27; on a Layout"
    assert link_names(text, TARGETS, html_link) == (
        'a &#x27;<a href="#FieldAssertion">FieldAssertion</a>&#x27; on a <a href="#Layout">Layout</a>'
    )


TURTLE = """
@prefix : <https://example.org/onto#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix other: <https://example.org/other#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
<https://example.org/onto> a owl:Ontology .
:FieldAssertion a owl:Class ; rdfs:comment "A value a model found, made by a Step (a prov:Activity, not any Activity)." .
:Step a owl:Class ; rdfs:comment "A Step of a run; it records each FieldAssertion and reads a Page." .
prov:Activity a owl:Class ; rdfs:isDefinedBy <http://www.w3.org/ns/prov#> .
"""


def graph() -> Graph:
    return Graph().parse(data=textwrap.dedent(TURTLE), format="turtle")


def test_targets_name_own_terms_bare_stubs_only_by_prefix_and_other_pages_bare_and_by_prefix():
    targets = targets_for(
        graph(),
        "https://example.org/onto",
        {"https://example.org/onto#Step": "#Step", "http://www.w3.org/ns/prov#Activity": "#Activity"},
        {"https://example.org/other#Page": "other.md#Page"},
    )
    assert targets == {"Step": "#Step", "prov:Activity": "#Activity", "Page": "other.md#Page", "other:Page": "other.md#Page"}


def test_a_local_name_two_targets_share_is_not_linked_by_that_name():
    targets = targets_for(
        graph(), "https://example.org/onto", {"https://example.org/onto#Page": "#Page"}, {"https://example.org/other#Page": "o.md#Page"}
    )
    assert "Page" not in targets and targets["other:Page"] == "o.md#Page"


def test_the_markdown_page_links_definitions_within_the_page_and_to_other_pages():
    md = convert_graph(graph(), external_links={"https://example.org/other#Page": "other.md#Page"})
    assert "A value a model found, made by a [Step](#Step) (a [prov:Activity](#Activity), not any Activity)." in md
    assert "A Step of a run; it records each [FieldAssertion](#FieldAssertion) and reads a [Page](other.md#Page)." in md
