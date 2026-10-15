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
