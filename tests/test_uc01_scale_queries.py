"""The scale competency questions CQ 1.3 to CQ 1.7 of the UC-01 ORSD, on the example §5 describes (#240)."""
import sys
from pathlib import Path

import pytest

pytest.importorskip("rdflib")
from rdflib import Graph  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_uc01_competency_queries import PREFIXES, recorded_query  # noqa: E402

# A drawing with a title-block scale and three layouts (one with its own scale, one with none, one marked "NTS"), a drawing
# whose scale was written with hasScale, a drawing with no scale, and a drawing with no scale and a single detected layout
# whose caption gives one.
EXAMPLE = """:s1 a metadata:DrawingSheet ; metadata:drawingScale "1:50" ; metadata:contains :l1 , :l2 , :l3 .
:l1 a metadata:Layout ; metadata:layoutScale "1:20" .
:l2 a metadata:Layout .
:l3 a metadata:Layout ; metadata:layoutScale "NTS" .
:s2 a metadata:DrawingSheet ; metadata:hasScale "1:50" .
:s3 a metadata:DrawingSheet ; metadata:contains :l4 .
:l4 a metadata:Layout .
:s4 a metadata:DrawingSheet ; metadata:contains :l5 .
:l5 a metadata:Layout ; metadata:layoutScale "1:50" .
"""


def answer(marker, *names):
    graph = Graph().parse(data=PREFIXES + EXAMPLE, format="turtle")
    local = lambda v: None if v is None else str(v).rsplit("#", 1)[-1]  # noqa: E731
    return {tuple(local(row[n]) for n in names) for row in graph.query(recorded_query(marker))}


def test_cq_1_3_finds_a_drawing_by_its_own_scale_written_either_way_and_not_by_a_layouts():
    assert answer("# CQ 1.3", "sheet") == {("s1",), ("s2",)}  # s4's 1:50 is its layout's, never copied to it


def test_cq_1_4_gives_a_layout_its_own_scale_or_else_its_drawings():
    assert answer("# CQ 1.4", "layout", "scale", "basis") == {
        ("l1", "1:20", "own"), ("l2", "1:50", "assumed from sheet"), ("l3", "NTS", "own"),
        ("l4", None, "none"), ("l5", "1:50", "own"),
    }


def test_cq_1_5_lists_the_drawings_that_state_no_scale():
    assert answer("# CQ 1.5", "sheet") == {("s3",), ("s4",)}


def test_cq_1_6_lists_the_layouts_whose_scale_cannot_be_determined():
    assert answer("# CQ 1.6", "layout") == {("l4",)}


def test_cq_1_7_lists_the_layouts_at_another_scale_than_their_drawing():
    assert answer("# CQ 1.7", "layout", "own", "nominal") == {("l1", "1:20", "1:50"), ("l3", "NTS", "1:50")}
