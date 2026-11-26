"""The licence of ADIRO's resources is declared the same way everywhere (#276)."""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CC_BY = "https://creativecommons.org/licenses/by/4.0/"


def live_modules():
    rdflib = pytest.importorskip("rdflib")
    for path in sorted((ROOT / "src").glob("*.ttl")):
        graph = rdflib.Graph().parse(str(path), format="turtle")
        ontology = next(graph.subjects(rdflib.RDF.type, rdflib.OWL.Ontology))
        if (ontology, rdflib.OWL.deprecated, None) not in graph:  # a deprecated module is not released again
            yield path.stem, graph, ontology


def test_every_live_module_is_licensed_cc_by_4():
    rdflib = pytest.importorskip("rdflib")
    for module, graph, ontology in live_modules():
        licences = {str(o) for o in graph.objects(ontology, rdflib.DCTERMS.license)}
        assert licences == {CC_BY}, f"{module}: {licences}"


def test_the_licence_texts_and_the_map_exist():
    assert (ROOT / "LICENSES" / "CC-BY-4.0.txt").read_text(encoding="utf-8").startswith("Attribution 4.0 International")
    assert "GNU GENERAL PUBLIC LICENSE" in (ROOT / "LICENSE").read_text(encoding="utf-8")
    licensing = (ROOT / "LICENSING.md").read_text(encoding="utf-8")
    for path in ("src/", "docs/", "data-validation/", "migration/", "assets/", "changelogs/", "scripts/", "ttl2md/", "tests/",
                 ".github/", "docs/javascripts/", "docs/stylesheets/", "config/"):
        assert f"`{path}" in licensing, path
    assert "Anything not listed is GPL-3.0" in licensing, "a default for what the map does not name"


def test_the_citation_file_names_both_licences():
    text = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    block = re.search(r"(?m)^license:\n((?:  - .*\n)+)", text)
    assert block and set(re.findall(r"- (\S+)", block.group(1))) == {"CC-BY-4.0", "GPL-3.0-only"}


def test_the_grant_for_earlier_releases_is_stated():
    """#333: every earlier release is also CC BY 4.0; its file is not edited, so the grant must be stated."""
    licensing = (ROOT / "LICENSING.md").read_text(encoding="utf-8")
    assert "Every release of every ADIRO module published before 2026-11-26" in licensing
    assert "is also licensed CC BY 4.0" in licensing and "either" in licensing
