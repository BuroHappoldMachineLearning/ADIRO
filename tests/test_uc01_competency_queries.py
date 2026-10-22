"""The UC-01 competency queries that the ORSD records (#179, #69): each runs against small data and gives the answer it claims."""
import re
import sys
from pathlib import Path

import pytest

pytest.importorskip("rdflib")
from rdflib import Graph  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ORSD = ROOT / "docs" / "specification" / "use-cases" / "UC-01" / "UC-01-Titleblock-Based Drawing Search.md"
PREFIXES = (
    "@prefix : <https://ex.org/d#> .\n"
    "@prefix metadata: <https://w3id.org/adiro/adiro_drawing_metadata#> .\n"
    "@prefix aprov: <https://w3id.org/adiro/adiro_provenance#> .\n"
)


def recorded_query(marker):
    """The fenced SPARQL block of the ORSD that contains `marker`."""
    for block in re.findall(r"```sparql\n(.*?)```", ORSD.read_text(encoding="utf-8"), re.S):
        if marker in block:
            return block
    raise AssertionError(f"the ORSD records no SPARQL block with {marker!r}")


def run(query, data):
    graph = Graph().parse(data=PREFIXES + data, format="turtle")
    return {str(row[0]).rsplit("#", 1)[-1] for row in graph.query(query)}


def test_cq_4_4_lists_the_drawings_with_no_recorded_author():
    query = recorded_query("# CQ 4.4")
    data = """:a a metadata:DrawingSheet ; metadata:isAuthoredBy :jsmith .
:b a metadata:DrawingSheet .
:c a metadata:DrawingSheet ; metadata:isCheckedBy :achen .
:d a metadata:DrawingSheet ; metadata:hasRevision :rd .
:rd a metadata:DrawingRevision ; metadata:isAuthoredBy :jsmith .
:e a metadata:DrawingSheet ; metadata:hasRevision :re .
:re a metadata:DrawingRevision ; metadata:isCheckedBy :achen .
:stray a metadata:DrawingRevision ; metadata:isAuthoredBy :jsmith .
"""
    # b has nobody, c has a checker but no author, e has a revision with a checker but no author; d has no author of its own
    # but a revision's author counts; a revision is not a drawing, and one not linked to a drawing counts for none
    assert run(query, data) == {"b", "c", "e"}


def test_cq_4_5_is_cq_4_4_with_the_checker_or_the_approver():
    query = """SELECT ?drawing WHERE {
  ?drawing a <https://w3id.org/adiro/adiro_drawing_metadata#DrawingSheet> .
  FILTER NOT EXISTS { ?drawing <https://w3id.org/adiro/adiro_drawing_metadata#isCheckedBy> ?person }
}"""
    # the revision fallback is for the author only: a checker on a revision does not make the drawing checked
    data = ":a a metadata:DrawingSheet ; metadata:isCheckedBy :achen .\n:b a metadata:DrawingSheet ; metadata:hasRevision :r .\n:r a metadata:DrawingRevision ; metadata:isCheckedBy :achen .\n"
    assert run(query, data) == {"b"}


def test_cq_3_4_finds_the_table_a_revision_was_read_from():
    query = recorded_query("# CQ 3.4")
    data = """:t1 a metadata:RevisionTable ; metadata:assertsRevision :ra , :rb .
:t2 a metadata:RevisionTable ; metadata:assertsRevision :rc .
:ra a metadata:DrawingRevision ; metadata:revisionCode "A" .
:rb a metadata:DrawingRevision ; metadata:revisionCode "B" .
:rc a metadata:DrawingRevision ; metadata:revisionCode "C" .
"""
    assert run(query, data) == {"t1"}


def test_cq_2_4_finds_the_drawings_filed_under_another_project_than_their_title_block_names():
    query = recorded_query("# CQ 2.4")
    data = """:t1 a metadata:Titleblock ; metadata:assertsMetadataFor :a ; metadata:assertsProject :p1 .
:a a metadata:DrawingSheet ; metadata:belongsToProject :p1 .
:t2 a metadata:Titleblock ; metadata:assertsMetadataFor :b ; metadata:assertsProject :p1 .
:b a metadata:DrawingSheet ; metadata:belongsToProject :p2 .
:t3 a metadata:Titleblock ; metadata:assertsMetadataFor :c ; metadata:assertsProject :p1 .
:c a metadata:DrawingSheet .
"""
    # a agrees, b is filed under p2 while its title block names p1; c is not filed under any project, so nothing to compare
    assert run(query, data) == {"b"}


def test_cq_8_4_finds_the_drawings_filed_in_another_package_than_their_title_block_names():
    query = recorded_query("# CQ 8.4")
    data = """:t1 a metadata:Titleblock ; metadata:assertsMetadataFor :a ; metadata:assertsPackage :v3 .
:a a metadata:DrawingSheet ; metadata:belongsToPackage :v3 .
:t2 a metadata:Titleblock ; metadata:assertsMetadataFor :b ; metadata:assertsPackage :v3 .
:b a metadata:DrawingSheet ; metadata:belongsToPackage :v4 .
:t3 a metadata:Titleblock ; metadata:assertsMetadataFor :c .
:c a metadata:DrawingSheet ; metadata:belongsToPackage :v4 .
"""
    # b is filed in v4 while its title block names v3; c's title block names no package, so there is nothing to compare
    assert run(query, data) == {"b"}


def test_cq_9_1_gives_the_file_and_the_page_of_a_drawing():
    query = recorded_query("# CQ 9.1")
    data = """:d a metadata:DrawingSheet ; metadata:drawingIdentifier "ST-101" ; metadata:isOnPage :p3 .
:p3 a aprov:FilePage ; aprov:pageNumber 3 ; aprov:belongsToFile :f .
:f a aprov:DrawingFile ; aprov:fileName "A101-ground-floor.pdf" .
:other a metadata:DrawingSheet ; metadata:drawingIdentifier "ST-102" ; metadata:isOnPage :p4 .
:p4 a aprov:FilePage ; aprov:pageNumber 4 ; aprov:belongsToFile :f .
"""
    graph = Graph().parse(data=PREFIXES + data, format="turtle")
    assert {(str(r[0]), int(r[1])) for r in graph.query(query)} == {("A101-ground-floor.pdf", 3)}


def test_cq_9_3_lists_the_files_that_hold_more_than_one_drawing():
    query = recorded_query("# CQ 9.3")
    data = """:a a metadata:DrawingSheet ; metadata:isOnPage :pa .
:b a metadata:DrawingSheet ; metadata:isOnPage :pb .
:c a metadata:DrawingSheet ; metadata:isOnPage :pc .
:pa a aprov:FilePage ; aprov:belongsToFile :many .
:pb a aprov:FilePage ; aprov:belongsToFile :many .
:pc a aprov:FilePage ; aprov:belongsToFile :single .
"""
    graph = Graph().parse(data=PREFIXES + data, format="turtle")
    assert {(str(r[0]).rsplit("#", 1)[-1], int(r[1])) for r in graph.query(query)} == {("many", 2)}


def test_cq_4_6_says_why_a_drawing_has_no_author():
    data = """:printed a metadata:DrawingSheet .
:a1 a aprov:FieldAssertion ; aprov:assertedAbout :printed ; aprov:assertsFieldKind metadata:DrawnByField ; aprov:hasOutcome aprov:NotPrinted .
:blank a metadata:DrawingSheet .
:a2 a aprov:FieldAssertion ; aprov:assertedAbout :blank ; aprov:assertsFieldKind metadata:DrawnByField ; aprov:hasOutcome aprov:Empty .
:waiting a metadata:DrawingSheet .
:a3 a aprov:FieldAssertion ; aprov:assertedAbout :waiting ; aprov:assertsFieldKind metadata:DrawnByField ; aprov:hasLiteralValue "J. Smith" .
:unseen a metadata:DrawingSheet .
:retried a metadata:DrawingSheet .
:old a aprov:FieldAssertion ; aprov:assertedAbout :retried ; aprov:assertsFieldKind metadata:DrawnByField ; aprov:hasOutcome aprov:NotFound .
:newer a aprov:FieldAssertion ; aprov:assertedAbout :retried ; aprov:assertsFieldKind metadata:DrawnByField ; aprov:hasOutcome aprov:Illegible ; aprov:supersedes :old .
:done a metadata:DrawingSheet ; metadata:isAuthoredBy :jsmith .
"""
    rows = cq_4_6(data)
    reasons = {d: r for d, _, _, r in rows}
    assert len(rows) == len(reasons), "one row per drawing here"
    # the latest assertion decides (a superseded one is not read), a value awaiting acceptance is Pending, no assertion is NotProcessed
    assert reasons == {"printed": "NotPrinted", "blank": "Empty", "waiting": "Pending", "unseen": "NotProcessed", "retried": "Illegible"}


def cq_4_6(data):
    """Every row of the recorded CQ 4.6 query, as (drawing, subject, acceptance, reason), local names, sorted: a list, so
    a change that multiplies the rows is seen."""
    graph = Graph().parse(data=PREFIXES + data, format="turtle")
    local = lambda term: "" if term is None else str(term).rsplit("#", 1)[-1]  # noqa: E731
    return sorted((local(r.drawing), local(r.subject), local(r.acceptance), local(r.reason)) for r in graph.query(recorded_query("# CQ 4.6")))


def test_cq_4_6_reports_a_rejected_assertion_as_rejected_with_its_value_or_outcome():
    # #219: a rejected value was reported Pending, and a rejected NotPrinted as a finding that the drawing names no author
    data = """:rejected a metadata:DrawingSheet .
:a1 a aprov:FieldAssertion ; aprov:assertedAbout :rejected ; aprov:assertsFieldKind metadata:DrawnByField ; aprov:hasValueEntity :candidate ; aprov:hasAcceptance aprov:Rejected .
:rejectedAbsence a metadata:DrawingSheet .
:a2 a aprov:FieldAssertion ; aprov:assertedAbout :rejectedAbsence ; aprov:assertsFieldKind metadata:DrawnByField ; aprov:hasOutcome aprov:NotPrinted ; aprov:hasAcceptance aprov:Rejected .
:acceptedAbsence a metadata:DrawingSheet .
:a3 a aprov:FieldAssertion ; aprov:assertedAbout :acceptedAbsence ; aprov:assertsFieldKind metadata:DrawnByField ; aprov:hasOutcome aprov:NotPrinted ; aprov:hasAcceptance aprov:Accepted .
:explicitPending a metadata:DrawingSheet .
:a4 a aprov:FieldAssertion ; aprov:assertedAbout :explicitPending ; aprov:assertsFieldKind metadata:DrawnByField ; aprov:hasLiteralValue "J. Smith" ; aprov:hasAcceptance aprov:Pending .
:notPromoted a metadata:DrawingSheet .
:a5 a aprov:FieldAssertion ; aprov:assertedAbout :notPromoted ; aprov:assertsFieldKind metadata:DrawnByField ; aprov:hasValueEntity :jsmith ; aprov:hasAcceptance aprov:Accepted .
:promoted a metadata:DrawingSheet ; metadata:isAuthoredBy :jsmith .
:a6 a aprov:FieldAssertion ; aprov:assertedAbout :promoted ; aprov:assertsFieldKind metadata:DrawnByField ; aprov:hasValueEntity :jsmith ; aprov:hasAcceptance aprov:Accepted .
"""
    graph = Graph().parse(data=PREFIXES + data, format="turtle")
    result = list(graph.query(recorded_query("# CQ 4.6")))
    rows = {str(r.drawing).rsplit("#", 1)[-1]: r for r in result}
    assert len(result) == len(rows), "one row per drawing here"
    assert {d: (str(r.acceptance), str(r.reason)) for d, r in rows.items()} == {
        "rejected": ("Rejected", "Rejected"),
        "rejectedAbsence": ("Rejected", "Rejected"),
        "acceptedAbsence": ("Accepted", "NotPrinted"),
        "explicitPending": ("Pending", "Pending"),
        "notPromoted": ("Accepted", "AcceptedNotPromoted"),
    }  # a drawing whose author is already promoted is not listed
    # the rejected value and outcome stay visible for inspection
    assert str(rows["rejected"].value).endswith("#candidate") and rows["rejected"].outcome is None
    assert str(rows["rejectedAbsence"].outcome) == "NotPrinted"


def test_cq_4_6_reads_the_assertions_about_the_revisions_one_row_each():
    # #219: an assertion about a revision was missed, and the drawing reported NotProcessed
    data = """:d a metadata:DrawingSheet ; metadata:hasRevision :rb , :rc .
:rb a metadata:DrawingRevision .
:rc a metadata:DrawingRevision .
:ab a aprov:FieldAssertion ; aprov:assertedAbout :rb ; aprov:assertsFieldKind metadata:DrawnByField ; aprov:hasOutcome aprov:Illegible .
:ac a aprov:FieldAssertion ; aprov:assertedAbout :rc ; aprov:assertsFieldKind metadata:DrawnByField ; aprov:hasLiteralValue "A. Chen" .
:own a metadata:DrawingSheet ; metadata:hasRevision :ro .
:ro a metadata:DrawingRevision .
:ao a aprov:FieldAssertion ; aprov:assertedAbout :own ; aprov:assertsFieldKind metadata:DrawnByField ; aprov:hasOutcome aprov:NotFound .
:none a metadata:DrawingSheet ; metadata:hasRevision :rn .
:rn a metadata:DrawingRevision .
"""
    assert cq_4_6(data) == [
        ("d", "rb", "Pending", "Illegible"),
        ("d", "rc", "Pending", "Pending"),
        ("none", "", "", "NotProcessed"),
        ("own", "own", "Pending", "NotFound"),
    ]


def test_cq_4_6_reports_an_assertion_with_nothing_to_promote_and_shows_a_disagreement():
    # review of #222: an accepted assertion with no value is NoValue, not AcceptedNotPromoted (it can never be promoted);
    # an assertion that records two values or two statuses (malformed) gives a row for each, so the disagreement is seen
    data = """:empty a metadata:DrawingSheet .
:a1 a aprov:FieldAssertion ; aprov:assertedAbout :empty ; aprov:assertsFieldKind metadata:DrawnByField ; aprov:hasAcceptance aprov:Accepted .
:bare a metadata:DrawingSheet .
:a2 a aprov:FieldAssertion ; aprov:assertedAbout :bare ; aprov:assertsFieldKind metadata:DrawnByField .
:twoStatuses a metadata:DrawingSheet .
:a3 a aprov:FieldAssertion ; aprov:assertedAbout :twoStatuses ; aprov:assertsFieldKind metadata:DrawnByField ; aprov:hasLiteralValue "J. Smith" ; aprov:hasAcceptance aprov:Pending , aprov:Accepted .
"""
    assert cq_4_6(data) == [
        ("bare", "bare", "Pending", "NoValue"),
        ("empty", "empty", "Accepted", "NoValue"),
        ("twoStatuses", "twoStatuses", "Accepted", "AcceptedNotPromoted"),
        ("twoStatuses", "twoStatuses", "Pending", "Pending"),
    ]


def test_the_promotion_gives_a_direct_statement_only_for_an_accepted_assertion_with_a_value():
    from rdflib import Namespace

    query = recorded_query("# Promotion")
    data = """:kindTitle aprov:mapsToFieldProperty metadata:drawingTitle .
:kindAuthor aprov:mapsToFieldProperty metadata:isAuthoredBy .
:accepted a aprov:FieldAssertion ; aprov:assertedAbout :d1 ; aprov:assertsFieldKind :kindTitle ; aprov:hasAcceptance aprov:Accepted ; aprov:hasLiteralValue "Ground floor plan" .
:entity a aprov:FieldAssertion ; aprov:assertedAbout :d1 ; aprov:assertsFieldKind :kindAuthor ; aprov:hasAcceptance aprov:Accepted ; aprov:hasValueEntity :jsmith .
:pending a aprov:FieldAssertion ; aprov:assertedAbout :d2 ; aprov:assertsFieldKind :kindTitle ; aprov:hasAcceptance aprov:Pending ; aprov:hasLiteralValue "Not yet" .
:rejected a aprov:FieldAssertion ; aprov:assertedAbout :d2 ; aprov:assertsFieldKind :kindTitle ; aprov:hasAcceptance aprov:Rejected ; aprov:hasLiteralValue "Wrong" .
:absent a aprov:FieldAssertion ; aprov:assertedAbout :d3 ; aprov:assertsFieldKind :kindAuthor ; aprov:hasAcceptance aprov:Accepted ; aprov:hasOutcome aprov:NotPrinted .
:old a aprov:FieldAssertion ; aprov:assertedAbout :d4 ; aprov:assertsFieldKind :kindTitle ; aprov:hasAcceptance aprov:Accepted ; aprov:hasLiteralValue "Old title" .
:new a aprov:FieldAssertion ; aprov:assertedAbout :d4 ; aprov:assertsFieldKind :kindTitle ; aprov:hasAcceptance aprov:Accepted ; aprov:hasLiteralValue "Corrected title" ; aprov:supersedes :old .
"""
    graph = Graph().parse(data=PREFIXES + data, format="turtle")
    promoted = {(str(s).rsplit("#", 1)[-1], str(p).rsplit("#", 1)[-1], str(o).rsplit("#", 1)[-1]) for s, p, o in graph.query(query)}
    assert promoted == {("d1", "drawingTitle", "Ground floor plan"), ("d1", "isAuthoredBy", "jsmith"), ("d4", "drawingTitle", "Corrected title")}


def test_a_table_asserts_every_revision_it_lists_and_the_ontology_declares_the_property():
    ontology = Graph().parse(str(ROOT / "src" / "adiro_drawing_metadata.ttl"), format="turtle")
    names = {str(s).rsplit("#", 1)[-1] for s in ontology.subjects()}
    assert {"assertsRevision", "assertsProject", "assertsPackage", "isAuthoredBy", "isCheckedBy", "isApprovedBy"} <= names
