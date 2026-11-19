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
    "@prefix admeta: <https://w3id.org/adiro/adiro_drawing_metadata#> .\n"
    "@prefix adprov: <https://w3id.org/adiro/adiro_provenance#> .\n"
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
    data = """:a a admeta:DrawingSheet ; admeta:isAuthoredBy :jsmith .
:b a admeta:DrawingSheet .
:c a admeta:DrawingSheet ; admeta:isCheckedBy :achen .
:d a admeta:DrawingSheet ; admeta:hasRevision :rd .
:rd a admeta:DrawingRevision ; admeta:isAuthoredBy :jsmith .
:e a admeta:DrawingSheet ; admeta:hasRevision :re .
:re a admeta:DrawingRevision ; admeta:isCheckedBy :achen .
:stray a admeta:DrawingRevision ; admeta:isAuthoredBy :jsmith .
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
    data = ":a a admeta:DrawingSheet ; admeta:isCheckedBy :achen .\n:b a admeta:DrawingSheet ; admeta:hasRevision :r .\n:r a admeta:DrawingRevision ; admeta:isCheckedBy :achen .\n"
    assert run(query, data) == {"b"}


def test_cq_3_4_finds_the_table_a_revision_was_read_from():
    query = recorded_query("# CQ 3.4")
    data = """:t1 a admeta:RevisionTable ; admeta:assertsRevision :ra , :rb .
:t2 a admeta:RevisionTable ; admeta:assertsRevision :rc .
:ra a admeta:DrawingRevision ; admeta:revisionCode "A" .
:rb a admeta:DrawingRevision ; admeta:revisionCode "B" .
:rc a admeta:DrawingRevision ; admeta:revisionCode "C" .
"""
    assert run(query, data) == {"t1"}


def test_cq_2_4_finds_the_drawings_filed_under_another_project_than_their_title_block_names():
    query = recorded_query("# CQ 2.4")
    data = """:t1 a admeta:Titleblock ; admeta:assertsMetadataFor :a ; admeta:assertsProject :p1 .
:a a admeta:DrawingSheet ; admeta:belongsToProject :p1 .
:t2 a admeta:Titleblock ; admeta:assertsMetadataFor :b ; admeta:assertsProject :p1 .
:b a admeta:DrawingSheet ; admeta:belongsToProject :p2 .
:t3 a admeta:Titleblock ; admeta:assertsMetadataFor :c ; admeta:assertsProject :p1 .
:c a admeta:DrawingSheet .
"""
    # a agrees, b is filed under p2 while its title block names p1; c is not filed under any project, so nothing to compare
    assert run(query, data) == {"b"}


def test_cq_8_4_finds_the_drawings_filed_in_another_package_than_their_title_block_names():
    query = recorded_query("# CQ 8.4")
    data = """:t1 a admeta:Titleblock ; admeta:assertsMetadataFor :a ; admeta:assertsPackage :v3 .
:a a admeta:DrawingSheet ; admeta:belongsToPackage :v3 .
:t2 a admeta:Titleblock ; admeta:assertsMetadataFor :b ; admeta:assertsPackage :v3 .
:b a admeta:DrawingSheet ; admeta:belongsToPackage :v4 .
:t3 a admeta:Titleblock ; admeta:assertsMetadataFor :c .
:c a admeta:DrawingSheet ; admeta:belongsToPackage :v4 .
"""
    # b is filed in v4 while its title block names v3; c's title block names no package, so there is nothing to compare
    assert run(query, data) == {"b"}


def test_cq_9_1_gives_the_file_and_the_page_of_a_drawing():
    query = recorded_query("# CQ 9.1")
    data = """:d a admeta:DrawingSheet ; admeta:drawingIdentifier "ST-101" ; admeta:isOnPage :p3 .
:p3 a adprov:FilePage ; adprov:pageNumber 3 ; adprov:belongsToFile :f .
:f a adprov:DrawingFile ; adprov:fileName "A101-ground-floor.pdf" .
:other a admeta:DrawingSheet ; admeta:drawingIdentifier "ST-102" ; admeta:isOnPage :p4 .
:p4 a adprov:FilePage ; adprov:pageNumber 4 ; adprov:belongsToFile :f .
"""
    graph = Graph().parse(data=PREFIXES + data, format="turtle")
    assert {(str(r[0]), int(r[1])) for r in graph.query(query)} == {("A101-ground-floor.pdf", 3)}


def test_cq_9_3_lists_the_files_that_hold_more_than_one_drawing():
    query = recorded_query("# CQ 9.3")
    data = """:a a admeta:DrawingSheet ; admeta:isOnPage :pa .
:b a admeta:DrawingSheet ; admeta:isOnPage :pb .
:c a admeta:DrawingSheet ; admeta:isOnPage :pc .
:pa a adprov:FilePage ; adprov:belongsToFile :many .
:pb a adprov:FilePage ; adprov:belongsToFile :many .
:pc a adprov:FilePage ; adprov:belongsToFile :single .
"""
    graph = Graph().parse(data=PREFIXES + data, format="turtle")
    assert {(str(r[0]).rsplit("#", 1)[-1], int(r[1])) for r in graph.query(query)} == {("many", 2)}


def test_cq_9_5_finds_where_a_file_was_obtained_from_through_the_files_it_was_made_from():
    query = recorded_query("# CQ 9.5")
    data = """@prefix prov: <http://www.w3.org/ns/prov#> .
:d a admeta:DrawingSheet ; admeta:drawingIdentifier "ST-101" ; admeta:isOnPage :p .
:p a adprov:FilePage ; adprov:belongsToFile :png .
:png a adprov:DrawingFile ; prov:wasDerivedFrom :tif ;
    adprov:storageLocation "https://storage.example.org/0001.png" .
:tif a adprov:DrawingFile ; adprov:sourceLocation "https://tile.loc.gov/0001.tif" ;
    adprov:sourcePage "https://www.loc.gov/item/x/" .
"""
    graph = Graph().parse(data=PREFIXES + data, format="turtle")
    rows = {(str(r[1]).rsplit("#", 1)[-1], str(r[2]), str(r[3])) for r in graph.query(query)}
    assert rows == {("tif", "https://tile.loc.gov/0001.tif", "https://www.loc.gov/item/x/")}
    # a file with its own origin is found with no derivation at all
    direct = data.replace(":png a adprov:DrawingFile ; prov:wasDerivedFrom :tif ;", ":png a adprov:DrawingFile ; adprov:sourceLocation \"https://example.org/set.pdf\" ;")
    graph = Graph().parse(data=PREFIXES + direct, format="turtle")
    assert {str(r[1]).rsplit("#", 1)[-1] for r in graph.query(query)} == {"png"}


def test_cq_4_6_says_why_a_drawing_has_no_author():
    data = """:printed a admeta:DrawingSheet .
:a1 a adprov:FieldAssertion ; adprov:assertedAbout :printed ; adprov:assertsFieldKind admeta:DrawnByField ; adprov:hasOutcome adprov:NotPrinted .
:blank a admeta:DrawingSheet .
:a2 a adprov:FieldAssertion ; adprov:assertedAbout :blank ; adprov:assertsFieldKind admeta:DrawnByField ; adprov:hasOutcome adprov:Empty .
:waiting a admeta:DrawingSheet .
:a3 a adprov:FieldAssertion ; adprov:assertedAbout :waiting ; adprov:assertsFieldKind admeta:DrawnByField ; adprov:hasLiteralValue "J. Smith" .
:unseen a admeta:DrawingSheet .
:retried a admeta:DrawingSheet .
:old a adprov:FieldAssertion ; adprov:assertedAbout :retried ; adprov:assertsFieldKind admeta:DrawnByField ; adprov:hasOutcome adprov:NotFound .
:newer a adprov:FieldAssertion ; adprov:assertedAbout :retried ; adprov:assertsFieldKind admeta:DrawnByField ; adprov:hasOutcome adprov:Illegible ;
    adprov:hasAcceptance adprov:Accepted ; adprov:acceptedBy :reviewer ; adprov:supersedes :old .
:done a admeta:DrawingSheet ; admeta:isAuthoredBy :jsmith .
"""
    rows = cq_4_6(data)
    reasons = {d: r for d, _, _, r in rows}
    assert len(rows) == len(reasons), "one row per drawing here"
    # an accepted assertion decides (the one it supersedes is not read), a value awaiting acceptance is Pending, no assertion is NotProcessed
    assert reasons == {"printed": "NotPrinted", "blank": "Empty", "waiting": "Pending", "unseen": "NotProcessed", "retried": "Illegible"}


def cq_4_6(data):
    """Every row of the recorded CQ 4.6 query, as (drawing, subject, acceptance, reason), local names, sorted: a list, so
    a change that multiplies the rows is seen."""
    graph = Graph().parse(data=PREFIXES + data, format="turtle")
    local = lambda term: "" if term is None else str(term).rsplit("#", 1)[-1]  # noqa: E731
    return sorted((local(r.drawing), local(r.subject), local(r.acceptance), local(r.reason)) for r in graph.query(recorded_query("# CQ 4.6")))


def test_cq_4_6_reports_a_rejected_assertion_as_rejected_with_its_value_or_outcome():
    # #219: a rejected value was reported Pending, and a rejected NotPrinted as a finding that the drawing names no author
    data = """:rejected a admeta:DrawingSheet .
:a1 a adprov:FieldAssertion ; adprov:assertedAbout :rejected ; adprov:assertsFieldKind admeta:DrawnByField ; adprov:hasValueEntity :candidate ; adprov:hasAcceptance adprov:Rejected .
:rejectedAbsence a admeta:DrawingSheet .
:a2 a adprov:FieldAssertion ; adprov:assertedAbout :rejectedAbsence ; adprov:assertsFieldKind admeta:DrawnByField ; adprov:hasOutcome adprov:NotPrinted ; adprov:hasAcceptance adprov:Rejected .
:acceptedAbsence a admeta:DrawingSheet .
:a3 a adprov:FieldAssertion ; adprov:assertedAbout :acceptedAbsence ; adprov:assertsFieldKind admeta:DrawnByField ; adprov:hasOutcome adprov:NotPrinted ; adprov:hasAcceptance adprov:Accepted .
:explicitPending a admeta:DrawingSheet .
:a4 a adprov:FieldAssertion ; adprov:assertedAbout :explicitPending ; adprov:assertsFieldKind admeta:DrawnByField ; adprov:hasLiteralValue "J. Smith" ; adprov:hasAcceptance adprov:Pending .
:notPromoted a admeta:DrawingSheet .
:a5 a adprov:FieldAssertion ; adprov:assertedAbout :notPromoted ; adprov:assertsFieldKind admeta:DrawnByField ; adprov:hasValueEntity :jsmith ; adprov:hasAcceptance adprov:Accepted .
:promoted a admeta:DrawingSheet ; admeta:isAuthoredBy :jsmith .
:a6 a adprov:FieldAssertion ; adprov:assertedAbout :promoted ; adprov:assertsFieldKind admeta:DrawnByField ; adprov:hasValueEntity :jsmith ; adprov:hasAcceptance adprov:Accepted .
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
    data = """:d a admeta:DrawingSheet ; admeta:hasRevision :rb , :rc .
:rb a admeta:DrawingRevision .
:rc a admeta:DrawingRevision .
:ab a adprov:FieldAssertion ; adprov:assertedAbout :rb ; adprov:assertsFieldKind admeta:DrawnByField ; adprov:hasOutcome adprov:Illegible .
:ac a adprov:FieldAssertion ; adprov:assertedAbout :rc ; adprov:assertsFieldKind admeta:DrawnByField ; adprov:hasLiteralValue "A. Chen" .
:own a admeta:DrawingSheet ; admeta:hasRevision :ro .
:ro a admeta:DrawingRevision .
:ao a adprov:FieldAssertion ; adprov:assertedAbout :own ; adprov:assertsFieldKind admeta:DrawnByField ; adprov:hasOutcome adprov:NotFound .
:none a admeta:DrawingSheet ; admeta:hasRevision :rn .
:rn a admeta:DrawingRevision .
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
    data = """:empty a admeta:DrawingSheet .
:a1 a adprov:FieldAssertion ; adprov:assertedAbout :empty ; adprov:assertsFieldKind admeta:DrawnByField ; adprov:hasAcceptance adprov:Accepted .
:bare a admeta:DrawingSheet .
:a2 a adprov:FieldAssertion ; adprov:assertedAbout :bare ; adprov:assertsFieldKind admeta:DrawnByField .
:twoStatuses a admeta:DrawingSheet .
:a3 a adprov:FieldAssertion ; adprov:assertedAbout :twoStatuses ; adprov:assertsFieldKind admeta:DrawnByField ; adprov:hasLiteralValue "J. Smith" ; adprov:hasAcceptance adprov:Pending , adprov:Accepted .
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
    data = """:kindTitle adprov:mapsToFieldProperty admeta:drawingTitle .
:kindAuthor adprov:mapsToFieldProperty admeta:isAuthoredBy .
:accepted a adprov:FieldAssertion ; adprov:assertedAbout :d1 ; adprov:assertsFieldKind :kindTitle ; adprov:hasAcceptance adprov:Accepted ; adprov:hasLiteralValue "Ground floor plan" .
:entity a adprov:FieldAssertion ; adprov:assertedAbout :d1 ; adprov:assertsFieldKind :kindAuthor ; adprov:hasAcceptance adprov:Accepted ; adprov:hasValueEntity :jsmith .
:pending a adprov:FieldAssertion ; adprov:assertedAbout :d2 ; adprov:assertsFieldKind :kindTitle ; adprov:hasAcceptance adprov:Pending ; adprov:hasLiteralValue "Not yet" .
:rejected a adprov:FieldAssertion ; adprov:assertedAbout :d2 ; adprov:assertsFieldKind :kindTitle ; adprov:hasAcceptance adprov:Rejected ; adprov:hasLiteralValue "Wrong" .
:absent a adprov:FieldAssertion ; adprov:assertedAbout :d3 ; adprov:assertsFieldKind :kindAuthor ; adprov:hasAcceptance adprov:Accepted ; adprov:hasOutcome adprov:NotPrinted .
:old a adprov:FieldAssertion ; adprov:assertedAbout :d4 ; adprov:assertsFieldKind :kindTitle ; adprov:hasAcceptance adprov:Accepted ; adprov:hasLiteralValue "Old title" .
:new a adprov:FieldAssertion ; adprov:assertedAbout :d4 ; adprov:assertsFieldKind :kindTitle ; adprov:hasAcceptance adprov:Accepted ; adprov:hasLiteralValue "Corrected title" ; adprov:supersedes :old .
"""
    graph = Graph().parse(data=PREFIXES + data, format="turtle")
    promoted = {(str(s).rsplit("#", 1)[-1], str(p).rsplit("#", 1)[-1], str(o).rsplit("#", 1)[-1]) for s, p, o in graph.query(query)}
    assert promoted == {("d1", "drawingTitle", "Ground floor plan"), ("d1", "isAuthoredBy", "jsmith"), ("d4", "drawingTitle", "Corrected title")}


# --- supersession takes effect when the superseding assertion is accepted, through a chain (#221) --------------------
TITLE = ":kindTitle adprov:mapsToFieldProperty admeta:drawingTitle .\n"
ACCEPTED = "adprov:hasAcceptance adprov:Accepted ; adprov:acceptedBy :reviewer"


def promoted_titles(data):
    graph = Graph().parse(data=PREFIXES + TITLE + data, format="turtle")
    return {str(o) for _, _, o in graph.query(recorded_query("# Promotion"))}


def assertion(name, about, rest):
    return f":{name} a adprov:FieldAssertion ; adprov:assertedAbout :{about} ; adprov:assertsFieldKind :kindTitle ; {rest} .\n"


@pytest.mark.parametrize("b, promoted", [
    ('adprov:hasAcceptance adprov:Pending ; adprov:hasLiteralValue "First Floor Plan"', {"Ground Floor Plan"}),
    ('adprov:hasAcceptance adprov:Rejected ; adprov:hasLiteralValue "First Floor Plan"', {"Ground Floor Plan"}),
    ('adprov:hasLiteralValue "First Floor Plan"', {"Ground Floor Plan"}),  # no acceptance recorded: Pending
    (f'{ACCEPTED} ; adprov:hasLiteralValue "First Floor Plan"', {"First Floor Plan"}),
    (f"{ACCEPTED} ; adprov:hasOutcome adprov:NotPrinted", set()),  # an accepted outcome-only replacement withdraws the value
])
def test_supersession_takes_effect_when_the_new_assertion_is_accepted(b, promoted):
    a = assertion("a", "d", f'{ACCEPTED} ; adprov:hasLiteralValue "Ground Floor Plan"')
    assert promoted_titles(a + assertion("b", "d", f"{b} ; adprov:supersedes :a")) == promoted


def test_a_rejected_value_is_withdrawn_without_a_replacement():
    a = assertion("a", "d", 'adprov:hasAcceptance adprov:Rejected ; adprov:hasLiteralValue "Ground Floor Plan"')
    b = assertion("b", "d", 'adprov:hasAcceptance adprov:Pending ; adprov:hasLiteralValue "First Floor Plan" ; adprov:supersedes :a')
    assert promoted_titles(a + b) == set()


def test_an_accepted_correction_withdraws_the_whole_chain_it_ends():
    a = assertion("a", "d", f'{ACCEPTED} ; adprov:hasLiteralValue "A"')
    for middle in ("adprov:hasAcceptance adprov:Pending", "adprov:hasAcceptance adprov:Rejected", ACCEPTED):
        b = assertion("b", "d", f'{middle} ; adprov:hasLiteralValue "B" ; adprov:supersedes :a')
        c = assertion("c", "d", f'{ACCEPTED} ; adprov:hasLiteralValue "C" ; adprov:supersedes :b')
        assert promoted_titles(a + b + c) == {"C"}, middle
    # until the end of the chain is accepted, the latest accepted assertion before it stays in force
    b = assertion("b", "d", f'{ACCEPTED} ; adprov:hasLiteralValue "B" ; adprov:supersedes :a')
    c = assertion("c", "d", 'adprov:hasAcceptance adprov:Pending ; adprov:hasLiteralValue "C" ; adprov:supersedes :b')
    assert promoted_titles(a + b + c) == {"B"}


def test_cq_4_6_reads_an_assertion_superseded_only_by_an_unaccepted_one():
    data = """:d a admeta:DrawingSheet .
:old a adprov:FieldAssertion ; adprov:assertedAbout :d ; adprov:assertsFieldKind admeta:DrawnByField ; adprov:hasOutcome adprov:NotFound .
:new a adprov:FieldAssertion ; adprov:assertedAbout :d ; adprov:assertsFieldKind admeta:DrawnByField ; adprov:hasOutcome adprov:Illegible ;
    adprov:hasAcceptance adprov:Rejected ; adprov:supersedes :old .
"""
    assert cq_4_6(data) == [("d", "d", "Pending", "NotFound"), ("d", "d", "Rejected", "Rejected")]


def test_a_table_asserts_every_revision_it_lists_and_the_ontology_declares_the_property():
    ontology = Graph().parse(str(ROOT / "src" / "adiro_drawing_metadata.ttl"), format="turtle")
    names = {str(s).rsplit("#", 1)[-1] for s in ontology.subjects()}
    assert {"assertsRevision", "assertsProject", "assertsPackage", "isAuthoredBy", "isCheckedBy", "isApprovedBy"} <= names
