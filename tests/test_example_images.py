"""The example-image convention (#145): the value and file checks, and the build step that publishes the images."""
import json
import struct
import sys
import zlib
from pathlib import Path

import pytest

pytest.importorskip("rdflib")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from rdflib import Graph  # noqa: E402

import example_images as ei  # noqa: E402

M = "aec_x"
W3ID = f"https://w3id.org/adiro/{M}/exampleImage/"
PAGES = f"https://burohappoldmachinelearning.github.io/ADIRO/{M}/exampleImage/"


def graph(*triples):
    ttl = ("@prefix : <https://w3id.org/adiro/aec_x#> . @prefix m: <https://w3id.org/adiro/aec_drawing_metadata#> .\n"
           "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n")
    for term, obj in triples:
        ttl += f":{term} a owl:Class ; m:exampleImage {obj} .\n"
    return Graph().parse(data=ttl, format="turtle")


def png(width=10, height=10, text=False):
    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))
    out = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    if text:
        out += chunk(b"tEXt", b"Author\x00someone")
    return out + chunk(b"IDAT", zlib.compress(b"\x00" * 3 * width * height + b"\x00" * height)) + chunk(b"IEND", b"")


def add(root, name, data=None):
    path = Path(root) / "assets" / M / ei.FOLDER / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data if data is not None else png())
    return path


def kinds(found):
    return sorted({f.kind for f in found})


def test_a_conforming_value_and_file_raise_nothing(tmp_path):
    add(tmp_path, "Titleblock_01.png")
    assert ei.problems(graph(("Titleblock", f"<{W3ID}Titleblock_01.png>")), M, tmp_path) == []


def test_the_github_pages_form_is_the_same_file(tmp_path):
    add(tmp_path, "Titleblock_01.png")
    assert ei.problems(graph(("Titleblock", f"<{PAGES}Titleblock_01.png>")), M, tmp_path) == []


def test_a_relative_path_or_a_text_literal_is_not_an_absolute_https_iri(tmp_path):
    found = ei.problems(graph(("A", "<img/aec_x/a_01.png>"), ("B", '"https://w3id.org/x.png"'),
                              ("C", "<http://w3id.org/adiro/aec_x/exampleImage/C_01.png>")), M, tmp_path)
    assert kinds(found) == ["value-form"] and len(found) == 3 and not any(f.blocking for f in found)


def test_a_value_outside_the_modules_folder_is_in_the_wrong_place(tmp_path):
    other = "https://w3id.org/adiro/aec_y/exampleImage/A_01.png"
    nested = f"{W3ID}sub/A_01.png"
    assert kinds(ei.problems(graph(("A", f"<{other}>"), ("B", f"<{nested}>")), M, tmp_path)) == ["value-location"]


def test_the_file_name_is_the_local_name_then_a_two_digit_number_then_a_lower_case_extension(tmp_path):
    for name in ("Titleblock.png", "Titleblock_1.png", "Other_01.png", "Titleblock_01.PNG", "Titleblock_01.tif"):
        add(tmp_path, name)
        found = ei.problems(graph(("Titleblock", f"<{W3ID}{name}>")), M, tmp_path)
        assert "file-name" in kinds(found), name
    add(tmp_path, "Titleblock_02.webp")
    assert "file-name" not in kinds(ei.problems(graph(("Titleblock", f"<{W3ID}Titleblock_02.webp>")), M, tmp_path))


def test_a_value_that_names_a_missing_file_is_found(tmp_path):
    assert kinds(ei.problems(graph(("A", f"<{W3ID}A_01.png>")), M, tmp_path)) == ["file-missing"]


def test_a_file_no_term_uses_is_an_orphan_unless_it_is_in_the_takedown_list(tmp_path):
    add(tmp_path, "Lonely_01.png")
    assert kinds(ei.problems(graph(), M, tmp_path)) == ["file-orphan"]
    (Path(tmp_path) / "assets" / M / ei.FOLDER / ei.TAKEDOWNS).write_text("Lonely_01.png copyright\n", encoding="utf-8")
    assert ei.problems(graph(), M, tmp_path) == []


def test_the_deleted_after_backups_are_not_orphans(tmp_path):
    add(tmp_path, "deletedAfterV1.0.0/Gone_01.png")
    assert ei.problems(graph(), M, tmp_path) == []


def test_size_is_advised_at_250_kb_and_blocking_at_500_kb(tmp_path):
    add(tmp_path, "A_01.png", png() + b"\x00" * (300 * 1024))
    add(tmp_path, "B_01.png", png() + b"\x00" * (600 * 1024))
    found = {f.kind: f for f in ei.problems(graph(("A", f"<{W3ID}A_01.png>"), ("B", f"<{W3ID}B_01.png>")), M, tmp_path)}
    assert not found["file-size"].blocking and found["file-size-hard"].blocking


def test_dimensions_and_embedded_metadata_are_found(tmp_path):
    add(tmp_path, "A_01.png", png(1700, 20))
    add(tmp_path, "B_01.png", png(text=True))
    found = ei.problems(graph(("A", f"<{W3ID}A_01.png>"), ("B", f"<{W3ID}B_01.png>")), M, tmp_path)
    assert kinds(found) == ["file-dimensions", "file-metadata"]
    assert [f.blocking for f in found if f.kind == "file-metadata"] == [True]


def test_two_files_that_differ_only_by_case_clash(tmp_path):
    add(tmp_path, "A_01.png")
    path = add(tmp_path, "a_01.png")
    if len({p.name for p in path.parent.iterdir()}) == 2:  # a case-insensitive file system keeps one
        assert "case-clash" in kinds(ei.problems(graph(("A", f"<{W3ID}A_01.png>")), M, tmp_path))


def test_a_rename_entry_must_point_at_a_file_that_exists(tmp_path):
    add(tmp_path, "New_01.png")
    folder = Path(tmp_path) / "assets" / M / ei.FOLDER
    (folder / ei.RENAMES).write_text(json.dumps({"Old_01.png": "New_01.png", "Older_01.png": "Missing_01.png"}), encoding="utf-8")
    found = ei.problems(graph(("New", f"<{W3ID}New_01.png>")), M, tmp_path)
    assert kinds(found) == ["renames"] and len(found) == 1


def test_the_budget_warns_at_100_mb_and_blocks_at_250_mb(tmp_path, monkeypatch):
    add(tmp_path, "A_01.png", png() + b"\x00" * 2048)
    monkeypatch.setattr(ei, "BUDGET_WARN", 1024)
    assert [f.blocking for f in ei.budget_findings(tmp_path)] == [False]
    monkeypatch.setattr(ei, "BUDGET_BLOCK", 2048)
    assert [f.blocking for f in ei.budget_findings(tmp_path)] == [True]


def test_messages_group_one_message_per_kind_and_link_the_page(tmp_path):
    found = ei.problems(graph(*[(f"T{i}", f"<img/t{i}.png>") for i in range(10)]), M, tmp_path)
    errors, warnings = ei.messages(found, M)
    assert errors == [] and len(warnings) == 1
    assert "10 exampleImage value(s)" in warnings[0] and "and 2 more" in warnings[0] and ei.PAGE_URL in warnings[0]
    assert ei.messages(found, M, enforce=True)[0] and not ei.messages(found, M, enforce=True)[1]


def test_blocking_findings_are_errors_even_without_enforcement(tmp_path):
    add(tmp_path, "B_01.png", png(text=True))
    errors, _ = ei.messages(ei.problems(graph(("B", f"<{W3ID}B_01.png>")), M, tmp_path), M)
    assert len(errors) == 1 and "embedded metadata" in errors[0]


def test_stage_copies_the_images_and_serves_old_names_as_copies(tmp_path):
    add(tmp_path, "New_01.png", png(5, 5))
    add(tmp_path, "deletedAfterV1.0.0/Gone_01.png", png(6, 6))
    add(tmp_path, "Taken_01.png", png(7, 7))
    folder = Path(tmp_path) / "assets" / M / ei.FOLDER
    (folder / ei.RENAMES).write_text(json.dumps({"Old_01.png": "New_01.png"}), encoding="utf-8")
    (folder / ei.TAKEDOWNS).write_text("Taken_01.png copyright\n", encoding="utf-8")
    docs = Path(tmp_path) / "docs"
    ei.stage(tmp_path, docs)
    out = docs / M / ei.FOLDER
    assert (out / "New_01.png").read_bytes() == (folder / "New_01.png").read_bytes()
    assert (out / "Old_01.png").read_bytes() == (out / "New_01.png").read_bytes()
    assert (out / "deletedAfterV1.0.0" / "Gone_01.png").is_file()
    assert not (out / "Taken_01.png").exists() and not (out / ei.RENAMES).exists() and not (out / ei.TAKEDOWNS).exists()


def test_stage_replaces_a_stale_copy_and_does_nothing_without_assets(tmp_path):
    docs = Path(tmp_path) / "docs"
    stale = docs / M / ei.FOLDER / "Stale_01.png"
    stale.parent.mkdir(parents=True)
    stale.write_bytes(b"x")
    assert ei.stage(tmp_path, docs) == [] and stale.exists()  # no assets folder: nothing to replace
    add(tmp_path, "New_01.png")
    ei.stage(tmp_path, docs)
    assert not stale.exists()
