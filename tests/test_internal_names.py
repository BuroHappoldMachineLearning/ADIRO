"""The public-repository guard: hand-written files must not name an internal tool (#89)."""
import sys
from pathlib import Path

import pytest

pytest.importorskip("rdflib")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import validate_ontology as vo  # noqa: E402

NAME = "c" + "vat"  # the guard's own tests must not contain the name either
PENDING = vo._PENDING_RENAME[0]


def write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_a_name_in_hand_written_prose_is_found_with_its_line(tmp_path):
    write(tmp_path, "AGENTS.md", "fine\nthe " + NAME.upper() + " panel\n")
    findings = vo.find_internal_names(tmp_path)
    assert len(findings) == 1 and findings[0].startswith("AGENTS.md:2 ")


def test_a_name_in_a_definition_or_a_script_is_found(tmp_path):
    write(tmp_path, "src/m.ttl", ':a rdfs:comment "shown in ' + NAME + '" .\n')
    write(tmp_path, "scripts/x.sh", "# " + NAME + "\n")
    assert len(vo.find_internal_names(tmp_path)) == 2


def test_the_identifier_awaiting_rename_is_allowed_but_prose_beside_it_is_not(tmp_path):
    write(tmp_path, "src/m.ttl", ":" + PENDING + " a owl:AnnotationProperty .\n")
    assert vo.find_internal_names(tmp_path) == []
    write(tmp_path, "src/m.ttl", ":" + PENDING + " a owl:AnnotationProperty ; # " + NAME + "\n")
    assert len(vo.find_internal_names(tmp_path)) == 1


def test_released_snapshots_and_generated_pages_are_not_scanned(tmp_path):
    write(tmp_path, "versions/m/1.0.0/m.ttl", NAME + "\n")
    write(tmp_path, "docs/ontologies/m.md", NAME + "\n")
    assert vo.find_internal_names(tmp_path) == []


def test_the_repository_itself_is_clean():
    assert vo.find_internal_names(Path(__file__).resolve().parent.parent) == []
