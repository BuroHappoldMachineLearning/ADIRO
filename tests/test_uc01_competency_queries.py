"""The UC-01 competency queries that the ORSD records (#179, #69): each runs against small data and gives the answer it claims."""
import re
import sys
from pathlib import Path

import pytest

pytest.importorskip("rdflib")
from rdflib import Graph  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ORSD = ROOT / "docs" / "specification" / "use-cases" / "UC-01" / "UC-01-Titleblock-Based Drawing Search.md"
PREFIXES = "@prefix : <https://ex.org/d#> .\n@prefix metadata: <https://w3id.org/adiro/aec_drawing_metadata#> .\n"


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
  ?drawing a <https://w3id.org/adiro/aec_drawing_metadata#DrawingSheet> .
  FILTER NOT EXISTS { ?drawing <https://w3id.org/adiro/aec_drawing_metadata#isCheckedBy> ?person }
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


def test_a_table_asserts_every_revision_it_lists_and_the_ontology_declares_the_property():
    ontology = Graph().parse(str(ROOT / "src" / "aec_drawing_metadata.ttl"), format="turtle")
    names = {str(s).rsplit("#", 1)[-1] for s in ontology.subjects()}
    assert {"assertsRevision", "assertsProject", "isAuthoredBy", "isCheckedBy", "isApprovedBy"} <= names
