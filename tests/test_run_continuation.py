"""Interrupted runs, a run that continues another, and the time an extraction job took (#249): CQ 10.5 to CQ 10.7."""
import sys
from decimal import Decimal
from pathlib import Path

import pytest

pytest.importorskip("rdflib")
from rdflib import Graph, Namespace, URIRef  # noqa: E402
from rdflib.namespace import OWL, RDF, RDFS  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_uc01_competency_queries import PREFIXES, recorded_query  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PROV = Namespace("http://www.w3.org/ns/prov#")
PROVENANCE = Graph().parse(ROOT / "src" / "adiro_provenance.ttl", format="turtle")


def test_was_informed_by_is_a_stub_with_no_axioms():
    assert (PROV.wasInformedBy, RDF.type, OWL.ObjectProperty) in PROVENANCE
    assert PROVENANCE.value(PROV.wasInformedBy, RDFS.isDefinedBy) == URIRef("http://www.w3.org/ns/prov#")
    assert not [p for p, _ in PROVENANCE.predicate_objects(PROV.wasInformedBy) if p in (RDFS.domain, RDFS.range, RDFS.subPropertyOf)]


# Job A: one run that completed. Job B: run B was interrupted, run C continued it and completed, run D continues C and is
# still running, across the end of a month; run B's times mix two time zones. Job E: one run across 29 February.
JOBS = """@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
:runA a prov:Activity ; prov:startedAtTime "2026-10-28T09:00:00Z"^^xsd:dateTime ; prov:endedAtTime "2026-10-28T09:30:00Z"^^xsd:dateTime .
:a1 a aprov:InferenceMeta ; dcterms:isPartOf :runA ; prov:startedAtTime "2026-10-28T09:00:10Z"^^xsd:dateTime ; aprov:inferredAt "2026-10-28T09:00:40Z"^^xsd:dateTime .
:a2 a aprov:InferenceMeta ; dcterms:isPartOf :runA ; prov:startedAtTime "2026-10-28T09:10:00Z"^^xsd:dateTime ; aprov:inferredAt "2026-10-28T09:11:00Z"^^xsd:dateTime .
:a3 a aprov:InferenceMeta ; dcterms:isPartOf :runA ; aprov:inferredAt "2026-10-28T09:20:00Z"^^xsd:dateTime .

:runB a prov:Activity ; prov:startedAtTime "2026-10-28T22:00:00+01:00"^^xsd:dateTime .
:b1 a aprov:InferenceMeta ; dcterms:isPartOf :runB ; prov:startedAtTime "2026-10-28T21:00:00Z"^^xsd:dateTime ; aprov:inferredAt "2026-10-28T21:05:00Z"^^xsd:dateTime .
:b2 a aprov:InferenceMeta ; dcterms:isPartOf :runB ; prov:startedAtTime "2026-10-28T22:10:00+01:00"^^xsd:dateTime ; aprov:inferredAt "2026-10-28T21:12:00Z"^^xsd:dateTime .
:runC a prov:Activity ; prov:wasInformedBy :runB ; prov:startedAtTime "2026-10-28T23:00:00Z"^^xsd:dateTime ; prov:endedAtTime "2026-10-28T23:30:00Z"^^xsd:dateTime .
:c1 a aprov:InferenceMeta ; dcterms:isPartOf :runC ; prov:startedAtTime "2026-10-28T23:01:00Z"^^xsd:dateTime ; aprov:inferredAt "2026-10-28T23:02:00Z"^^xsd:dateTime .
:runD a prov:Activity ; prov:wasInformedBy :runC ; prov:startedAtTime "2026-10-31T23:59:30Z"^^xsd:dateTime .
:d1 a aprov:InferenceMeta ; dcterms:isPartOf :runD ; prov:startedAtTime "2026-10-31T23:59:40Z"^^xsd:dateTime ; aprov:inferredAt "2026-11-01T00:00:20Z"^^xsd:dateTime .

:runE a prov:Activity ; prov:startedAtTime "2028-02-28T23:00:00Z"^^xsd:dateTime ; prov:endedAtTime "2028-03-01T01:00:00Z"^^xsd:dateTime .
:e1 a aprov:InferenceMeta ; dcterms:isPartOf :runE ; aprov:inferredAt "2028-03-01T00:30:00Z"^^xsd:dateTime .
"""


def query(marker, data=JOBS):
    return list(Graph().parse(data=PREFIXES + data, format="turtle").query(recorded_query(marker)))


def local(value):
    return None if value is None else str(value).rsplit("#", 1)[-1]


def when(value):
    """A time as an instant in UTC, however the engine writes the time zone."""
    from datetime import timezone
    return None if value is None else value.toPython().astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def test_cq_10_5_lists_the_runs_with_no_end_their_last_work_and_who_continued_them():
    rows = {(local(r.run), when(r.lastWork), local(r.continuedBy)) for r in query("# CQ 10.5")}
    # the latest inferredAt is compared as an instant, whatever the time zone it is written in
    assert rows == {("runB", "2026-10-28T21:12:00Z", "runC"), ("runD", "2026-11-01T00:00:20Z", None)}


def test_cq_10_6_gathers_each_job_from_its_first_run_through_every_continuation():
    rows = {(local(r.job), local(r.run), when(r.end), r.completed.toPython()) for r in query("# CQ 10.6")}
    assert rows == {
        ("runA", "runA", "2026-10-28T09:30:00Z", True),
        ("runB", "runB", "2026-10-28T21:12:00Z", False),  # interrupted: measured to its last recorded step
        ("runB", "runC", "2026-10-28T23:30:00Z", True),
        ("runB", "runD", "2026-11-01T00:00:20Z", False),  # still running
        ("runE", "runE", "2028-03-01T01:00:00Z", True),
    }


def test_cq_10_7_gives_each_jobs_elapsed_and_processing_time_without_the_gaps():
    rows = {local(r.job): (int(r.runs), Decimal(str(r.elapsedSeconds)), Decimal(str(r.processingSeconds))) for r in query("# CQ 10.7")}
    assert rows == {
        "runA": (1, Decimal(1800), Decimal(90)),        # a3 records only its end, so it is not processing time
        "runB": (3, Decimal(720 + 1800 + 50), Decimal(300 + 120 + 60 + 40)),
        "runE": (1, Decimal(26 * 3600), Decimal(0)),    # across 29 February of a leap year
    }


def test_cq_10_7_does_not_count_a_run_with_no_start():
    no_start = JOBS.replace(':runC a prov:Activity ; prov:wasInformedBy :runB ; prov:startedAtTime "2026-10-28T23:00:00Z"^^xsd:dateTime ;',
                            ":runC a prov:Activity ; prov:wasInformedBy :runB ;")
    rows = {local(r.job): Decimal(str(r.elapsedSeconds)) for r in query("# CQ 10.7", no_start)}
    assert rows["runB"] == Decimal(720 + 50)


def test_a_step_is_never_taken_for_a_run_nor_a_continued_run_for_a_first_one():
    jobs = {local(r.job) for r in query("# CQ 10.6")}
    assert jobs == {"runA", "runB", "runE"}  # runC and runD continue runB; steps record a start but are not runs
