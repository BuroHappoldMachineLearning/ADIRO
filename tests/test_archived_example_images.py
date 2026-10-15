"""Archived releases keep their example images (#154): a removed term's image stays, a takedown serves a placeholder."""
import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("rdflib")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import check_prior_versions as cpv  # noqa: E402
import example_images as ei  # noqa: E402
from test_example_images import M, W3ID, add, graph, kinds, png  # noqa: E402

SNAPSHOT = ("@prefix : <https://w3id.org/adiro/aec_x#> . @prefix m: <https://w3id.org/adiro/aec_drawing_metadata#> .\n"
            "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n@base <https://w3id.org/adiro/> .\n")


def folder(root):
    return Path(root) / "assets" / M / ei.FOLDER


def archive(root, version, *pairs):
    """An archived release of aec_x in which each (term, value) carries the example image `value`."""
    path = Path(root) / "versions" / M / version / f"{M}.ttl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(SNAPSHOT + "".join(f":{t} a owl:Class ; m:exampleImage {v} .\n" for t, v in pairs), encoding="utf-8")


def takedowns(root, text, placeholder_for=None):
    folder(root).mkdir(parents=True, exist_ok=True)
    (folder(root) / ei.TAKEDOWNS).write_text(text, encoding="utf-8")
    if placeholder_for:
        holder = ei.placeholder_file(folder(root), placeholder_for)
        holder.parent.mkdir(parents=True, exist_ok=True)
        holder.write_bytes(png(8, 8))


def test_a_removed_terms_image_stays_and_is_not_an_orphan_while_a_release_names_it(tmp_path):
    archive(tmp_path, "1.0.0", ("Gone", f"<{W3ID}Gone_01.png>"))
    add(tmp_path, "Gone_01.png")
    assert ei.problems(graph(), M, tmp_path) == []  # the term is gone, an archived release still names the file
    (Path(tmp_path) / "versions" / M / "1.0.0" / f"{M}.ttl").unlink()
    assert kinds(ei.problems(graph(), M, tmp_path)) == ["file-orphan"]  # no release names it: it can be deleted


def test_an_address_an_archived_release_names_must_still_be_served(tmp_path):
    archive(tmp_path, "1.0.0", ("Gone", f"<{W3ID}Gone_01.png>"))
    found = ei.problems(graph(), M, tmp_path)
    assert kinds(found) == ["archived-missing"] and found[0].blocking
    add(tmp_path, "Gone_01.png")
    assert ei.problems(graph(), M, tmp_path) == []


def test_a_renamed_image_is_still_served_under_the_name_a_release_names(tmp_path):
    archive(tmp_path, "1.0.0", ("New", f"<{W3ID}Old_01.png>"))
    add(tmp_path, "New_01.png")
    folder(tmp_path).joinpath(ei.RENAMES).write_text(json.dumps({"Old_01.png": "New_01.png"}), encoding="utf-8")
    assert ei.problems(graph(("New", f"<{W3ID}New_01.png>")), M, tmp_path) == []


def test_a_takedown_covers_the_address_and_needs_a_placeholder_for_its_version(tmp_path):
    archive(tmp_path, "1.0.0", ("Gone", f"<{W3ID}Gone_01.png>"))
    takedowns(tmp_path, "Gone_01.png copyright after=1.0.0\n")
    assert kinds(ei.problems(graph(), M, tmp_path)) == ["takedown-placeholder"]
    takedowns(tmp_path, "Gone_01.png copyright after=1.0.0\n", placeholder_for="1.0.0")
    assert ei.problems(graph(), M, tmp_path) == []
    takedowns(tmp_path, "Gone_01.png copyright\n")
    assert kinds(ei.problems(graph(), M, tmp_path)) == ["takedown-version"]  # advisory: a 404 is all it gets


def test_a_current_file_with_a_taken_down_name_is_reported(tmp_path):
    takedowns(tmp_path, "Gone_01.png copyright after=1.0.0\n", placeholder_for="1.0.0")
    add(tmp_path, "Gone_01.png")
    found = ei.problems(graph(), M, tmp_path)
    assert kinds(found) == ["takedown-reuse"] and found[0].blocking


def test_a_name_an_archived_release_gives_to_another_term_is_reserved(tmp_path):
    archive(tmp_path, "1.0.0", ("Stamp", f"<{W3ID}Stamp_01.png>"))
    add(tmp_path, "Stamp_01.png")
    assert ei.problems(graph(("Stamp", f"<{W3ID}Stamp_01.png>")), M, tmp_path) == []  # the same term keeps its image
    found = ei.problems(graph(("Stamp", f"<{W3ID}Stamp_02.png>")), M, tmp_path)
    assert "name-reused" not in kinds(found)
    add(tmp_path, "Stamp_02.png")
    archive(tmp_path, "1.0.0", ("Seal", f"<{W3ID}Stamp_02.png>"))  # now release 1.0.0 gave Stamp_02 to another term
    assert "name-reused" in kinds(ei.problems(graph(("Stamp", f"<{W3ID}Stamp_02.png>")), M, tmp_path))


def test_a_legacy_value_is_a_site_path_matched_to_a_takedown(tmp_path):
    archive(tmp_path, "1.0.0", ("Old", "<img/folder/old_01.png>"))
    assert [t for _, _, k, t in ei.snapshot_values(tmp_path, M) if k == "legacy"] == ["/img/folder/old_01.png"]
    assert kinds(ei.problems(graph(), M, tmp_path)) == ["archived-missing"]
    takedowns(tmp_path, "/img/folder/old_01.png copyright after=1.0.0\n", placeholder_for="1.0.0")
    assert ei.problems(graph(), M, tmp_path) == []


def test_stage_serves_a_takedown_as_the_placeholder_and_a_removed_terms_image_at_its_address(tmp_path):
    add(tmp_path, "Gone_01.png", png(6, 6))
    takedowns(tmp_path, "Taken_01.png copyright after=1.0.0\n/img/folder/old_01.png privacy after=1.0.0\nNoVersion_01.png copyright\n",
              placeholder_for="1.0.0")
    docs = Path(tmp_path) / "docs"
    ei.stage(tmp_path, docs)
    holder = ei.placeholder_file(folder(tmp_path), "1.0.0").read_bytes()
    assert (docs / M / ei.FOLDER / "Gone_01.png").read_bytes() == png(6, 6)
    assert (docs / M / ei.FOLDER / "Taken_01.png").read_bytes() == holder
    assert (docs / "img" / "folder" / "old_01.png").read_bytes() == holder
    assert not (docs / M / ei.FOLDER / "NoVersion_01.png").exists()
    assert not (docs / M / ei.FOLDER / ei.REMOVED_DIR).exists()


def test_stage_does_not_serve_a_taken_down_image_again_through_a_rename(tmp_path):
    add(tmp_path, "New_01.png", png(5, 5))
    takedowns(tmp_path, "Old_01.png copyright after=1.0.0\n", placeholder_for="1.0.0")
    folder(tmp_path).joinpath(ei.RENAMES).write_text(json.dumps({"Old_01.png": "New_01.png"}), encoding="utf-8")
    docs = Path(tmp_path) / "docs"
    ei.stage(tmp_path, docs)
    assert (docs / M / ei.FOLDER / "Old_01.png").read_bytes() == ei.placeholder_file(folder(tmp_path), "1.0.0").read_bytes()


def test_stage_ignores_a_takedown_path_that_leaves_the_site(tmp_path):
    takedowns(tmp_path, "/../escape.png copyright after=1.0.0\n", placeholder_for="1.0.0")
    ei.stage(tmp_path, Path(tmp_path) / "docs")
    assert not (Path(tmp_path) / "escape.png").exists()


# --- the post-deploy check ----------------------------------------------------------------------------------------

def repo_with_archive(tmp_path):
    archive(tmp_path, "1.0.0", ("Gone", f"<{W3ID}Gone_01.png>"), ("Old", "<img/folder/old_01.png>"))
    archive(tmp_path, "2.0.0", ("Gone", f"<{W3ID}Gone_01.png>"))
    add(tmp_path, "Gone_01.png")
    takedowns(tmp_path, "/img/folder/old_01.png copyright after=1.0.0\n", placeholder_for="1.0.0")
    return Path(tmp_path) / "versions", Path(tmp_path) / "assets"


def test_the_addresses_to_check_are_listed_once_with_the_releases_that_name_them(tmp_path):
    versions, assets = repo_with_archive(tmp_path)
    found = {url: (names, expected) for url, names, expected in cpv.archived_example_images(versions, assets)}
    assert found[f"https://w3id.org/adiro/{M}/exampleImage/Gone_01.png"] == ([f"{M} 1.0.0", f"{M} 2.0.0"], None)
    names, expected = found["https://w3id.org/adiro/img/folder/old_01.png"]
    assert names == [f"{M} 1.0.0"] and expected == ei.placeholder_file(folder(tmp_path), "1.0.0").read_bytes()


def test_an_example_image_that_is_not_served_as_it_should_is_a_problem():
    ok = lambda url: (200, "image/png", b"data")  # noqa: E731
    assert cpv.example_image_problem("u", None, ok) is None
    assert "HTTP 404" in cpv.example_image_problem("u", None, lambda url: (404, "", b""))
    assert "not an image" in cpv.example_image_problem("u", None, lambda url: (200, "text/html", b"<html>"))
    assert cpv.example_image_problem("u", b"data", ok) is None
    assert "placeholder" in cpv.example_image_problem("u", b"other", ok)


def test_the_check_retries_and_reports_what_stays_broken(tmp_path, capsys):
    versions, assets = repo_with_archive(tmp_path)
    calls = []

    def fetch(url):
        calls.append(url)
        if url.endswith("Gone_01.png"):
            return 404, "", b""
        return 200, "image/png", ei.placeholder_file(folder(tmp_path), "1.0.0").read_bytes()

    found = cpv.check_example_images(versions, assets, fetch_fn=fetch, retries=2, wait=0, sleep=lambda s: None)
    assert len(found) == 1 and "Gone_01.png" in found[0] and "2.0.0" in found[0]
    assert sum(url.endswith("Gone_01.png") for url in calls) == 3  # the first try and two retries
    assert "FAIL" in capsys.readouterr().out
