"""A documentation page per ontology version (scripts/generate_docs.py, #124)."""
import sys
import types
from pathlib import Path

import pytest

pytest.importorskip("rdflib")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

# generate_docs imports pyLODE at module level (the CI test job does not install it); the page generation under
# test never calls it, so a stand-in is enough when the real package is absent.
for _name in ("pylode", "pylode.profiles", "pylode.profiles.ontpub"):
    sys.modules.setdefault(_name, types.ModuleType(_name))
sys.modules["pylode.profiles.ontpub"].__dict__.setdefault("OntPub", object)

import generate_docs as gd  # noqa: E402

TTL = """@prefix : <https://w3id.org/adiro/aec_x#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
<https://w3id.org/adiro/aec_x> a owl:Ontology ;
    rdfs:label "X" ;
    owl:versionIRI <https://w3id.org/adiro/aec_x/{v}> ;
    owl:versionInfo "{v}" .
:A a owl:Class ; rdfs:label "A" ; rdfs:comment "Thing A, as of {v}." .
"""


def make_repo(tmp_path, declared, archived):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "aec_x.ttl").write_text(TTL.format(v=declared), encoding="utf-8")
    for v in archived:
        folder = tmp_path / "versions" / "aec_x" / v
        folder.mkdir(parents=True)
        (folder / "aec_x.ttl").write_text(TTL.format(v=v), encoding="utf-8")
    return tmp_path


def generate(repo):
    docs = repo / "docs"
    gd.generate_ontology_markdown_pages([repo / "src" / "aec_x.ttl"], docs, repo)
    return docs / "ontologies"


def test_the_latest_page_stays_where_it_was_and_gets_a_selector(tmp_path):
    pages = generate(make_repo(tmp_path, "2.0.0", ["1.0.0", "2.0.0"]))
    latest = (pages / "aec_x.md").read_text(encoding="utf-8")
    assert "Version 2.0.0 (latest)" in latest and '<a href="1.0.0/">1.0.0</a>' in latest
    assert not latest.startswith("---")  # the latest page is searchable
    assert "- **Versioned IRI:** `https://w3id.org/adiro/aec_x/2.0.0`" in latest
    assert "**Version:**" not in latest  # the versioned IRI carries the version
    assert "# Aec X\n" in latest and "Thing A, as of 2.0.0." in latest
    assert not (pages / "aec_x" / "2.0.0.md").exists()  # the version the latest page documents gets no duplicate


def test_an_earlier_release_gets_its_own_page_that_is_wholly_that_version(tmp_path):
    pages = generate(make_repo(tmp_path, "2.0.0", ["1.0.0", "2.0.0"]))
    earlier = (pages / "aec_x" / "1.0.0.md").read_text(encoding="utf-8")
    assert earlier.startswith("---\nsearch:\n  exclude: true\n---\n")
    assert "# Aec X 1.0.0\n" in earlier
    assert "- **Versioned IRI:** `https://w3id.org/adiro/aec_x/1.0.0`" in earlier and "**Version:**" not in earlier
    # the dropdown and the three buttons are one row: a single wrapper holds the selector, then the buttons
    row = earlier[earlier.index('<div class="adiro-actions" markdown="span">'):earlier.index("</div>")]
    assert row.index('<details class="adiro-version">') < row.index("Open in OntoCanvas") < row.index("TTL source") < row.index("pyLODE HTML")
    assert "Version 1.0.0 (2.0.0 available)" in earlier and '<a href="../">2.0.0 (latest)</a>' in earlier
    assert "Thing A, as of 1.0.0." in earlier and "as of 2.0.0" not in earlier  # the terms are that version's
    assert "https://w3id.org/adiro/aec_x/1.0.0/aec_x.ttl" in earlier  # TTL source: the version IRI
    assert "https://w3id.org/adiro/aec_x/1.0.0/aec_x.html" in earlier  # pyLODE view: that version's
    assert "?onto=https://w3id.org/adiro/aec_x/1.0.0" in earlier  # OntoCanvas opens that version
    assert 'click aec_x "../../aec_x/"' in earlier  # one directory deeper than the latest page


def test_a_release_cut_whose_snapshot_is_not_taken_yet_is_the_latest(tmp_path):
    pages = generate(make_repo(tmp_path, "2.0.1", ["1.0.0", "2.0.0"]))
    assert "Version 2.0.1 (latest)" in (pages / "aec_x.md").read_text(encoding="utf-8")
    assert "Version 2.0.0 (2.0.1 available)" in (pages / "aec_x" / "2.0.0.md").read_text(encoding="utf-8")
    assert (pages / "aec_x" / "1.0.0.md").is_file()


def test_pages_of_versions_that_no_longer_need_one_are_removed(tmp_path):
    repo = make_repo(tmp_path, "2.0.0", ["1.0.0", "2.0.0"])
    stale = repo / "docs" / "ontologies" / "aec_x" / "9.9.9.md"
    stale.parent.mkdir(parents=True)
    stale.write_text("old", encoding="utf-8")
    generate(repo)
    assert not stale.exists() and (stale.parent / "1.0.0.md").is_file()


def test_the_version_pages_stay_out_of_the_navigation_and_the_index(tmp_path):
    pages = generate(make_repo(tmp_path, "2.0.0", ["1.0.0", "2.0.0"]))
    assert (pages / ".pages").read_text(encoding="utf-8") == "nav:\n  - index.md\n  - aec_x.md\n"
    assert "1.0.0" not in (pages / "index.md").read_text(encoding="utf-8")


def test_pyLODE_pages_are_made_for_earlier_releases_only_and_stale_ones_dropped(tmp_path, monkeypatch):
    repo = make_repo(tmp_path, "2.0.0", ["1.0.0", "2.0.0"])
    stale = repo / "docs" / "aec_x" / "0.5.0"
    stale.mkdir(parents=True)
    calls = []
    monkeypatch.setattr(gd, "generate_documentation", lambda ttl, out, copy_ttl=True: calls.append((ttl, out, copy_ttl)) or True)
    failures = gd.generate_version_documentation([repo / "src" / "aec_x.ttl"], repo, repo / "docs")
    assert failures == 0 and not stale.exists()
    assert calls == [(repo / "versions" / "aec_x" / "1.0.0" / "aec_x.ttl", repo / "docs" / "aec_x" / "1.0.0", False)]


def test_a_failing_pyLODE_run_is_counted(tmp_path, monkeypatch):
    repo = make_repo(tmp_path, "2.0.0", ["1.0.0", "2.0.0"])
    monkeypatch.setattr(gd, "generate_documentation", lambda ttl, out, copy_ttl=True: False)
    assert gd.generate_version_documentation([repo / "src" / "aec_x.ttl"], repo, repo / "docs") == 1
