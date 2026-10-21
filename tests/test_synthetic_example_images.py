"""The synthetic example images (#149, #151): small, clean, and tied to the terms they show."""
import sys
from pathlib import Path

import pytest

pytest.importorskip("rdflib")
pytest.importorskip("matplotlib")
pytest.importorskip("PIL")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from rdflib import Graph  # noqa: E402

import example_images as ei  # noqa: E402
import synthetic_example_images as syn  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ALL = [(module, name) for module, drawings in syn.DRAWINGS.items() for name in sorted(drawings)]


def graph_of(module):
    return Graph().parse(str(ROOT / "src" / f"{module}.ttl"), format="turtle")


@pytest.mark.parametrize("module,name", ALL)
def test_each_drawing_is_small_has_no_metadata_and_is_not_oversized(module, name, tmp_path):
    data = syn.DRAWINGS[module][name]()
    path = tmp_path / name
    path.write_bytes(data)
    width, height, metadata = ei.image_info(path)
    assert len(data) <= ei.SOFT_BYTES, "the advised size"
    assert not metadata, "no embedded text, EXIF or software notes"
    assert width and height and max(width, height) <= ei.SOFT_PIXELS


def test_the_removed_placeholder_is_small_clean_and_names_the_version(tmp_path):
    data = syn.removed_placeholder("4.0.1")
    path = tmp_path / "after-v4.0.1.png"
    path.write_bytes(data)
    width, height, metadata = ei.image_info(path)
    assert len(data) <= ei.SOFT_BYTES and not metadata and width and height


@pytest.mark.parametrize("module", sorted(syn.DRAWINGS))
def test_every_takedown_version_has_a_committed_placeholder(module):
    folder = ei.module_folder(ROOT, module)
    for path, (_, version) in ei.load_takedown_entries(folder).items():
        assert version and ei.placeholder_file(folder, version).is_file(), path


def test_a_drawing_is_deterministic():
    assert syn.titleblock_strip() == syn.titleblock_strip()


@pytest.mark.parametrize("module", sorted(syn.DRAWINGS))
def test_the_drawing_names_follow_the_convention_and_name_classes_of_the_module(module):
    graph = graph_of(module)
    classes = {ei.local_name(s) for s in graph.subjects(None, None) if str(s).startswith(f"https://w3id.org/adiro/{module}#")}
    for name in syn.DRAWINGS[module]:
        match = ei.NAME_RE.match(Path(name).stem)
        assert match and name.endswith(".png") and match.group("term") in classes, name


@pytest.mark.parametrize("module", sorted(syn.DRAWINGS))
def test_every_value_in_the_ontology_has_a_drawing_and_a_committed_file(module):
    graph = graph_of(module)
    names = {ei.file_of(value, module)[1] for _, value in ei.values(graph)}
    assert names == set(syn.DRAWINGS[module])
    for name in names:
        assert (ei.module_folder(ROOT, module) / name).is_file(), name
    assert ei.problems(graph, module, ROOT) == []


def test_an_image_no_term_links_any_more_is_still_drawn_committed_and_unchanged():
    # A released version never changes (docs/contribute/example-images.md): Layout_01.png is named by earlier releases,
    # so the address keeps answering with the same picture even though `Layout` no longer links it (#177).
    for module, drawings in syn.ARCHIVED.items():
        linked = {ei.file_of(value, module)[1] for _, value in ei.values(graph_of(module))}
        for name, draw in drawings.items():
            assert name not in linked, f"{name} is linked again: move it to DRAWINGS"
            committed = ei.module_folder(ROOT, module) / name
            assert committed.is_file() and committed.read_bytes() == draw(), f"{name} differs from what the generator draws"


def test_drawing_sheet_shows_one_three_and_six_layouts_and_layout_shows_one_each():
    graph = graph_of("adiro_drawing_metadata")
    by_term = {}
    for term, value in ei.values(graph):
        by_term.setdefault(ei.local_name(term), set()).add(ei.file_of(value, "adiro_drawing_metadata")[1])
    assert by_term["DrawingSheet"] == {"DrawingSheet_01.png", "DrawingSheet_02.png", "DrawingSheet_03.png"}
    assert by_term["Layout"] == {"Layout_02.png", "Layout_03.png", "Layout_04.png"}
    # the three-layout sheet is the picture Layout_01.png has always shown
    assert syn.DRAWINGS["adiro_drawing_metadata"]["DrawingSheet_02.png"]() == syn.ARCHIVED["aec_drawing_metadata"]["Layout_01.png"]()
