"""The checks a consumer pins (#240): every shape file and every recorded UC-01 query, exported as they are written."""
import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("rdflib")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import export_checks as ec  # noqa: E402
from test_uc01_competency_queries import recorded_query  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def test_every_recorded_query_is_exported_under_its_own_name_and_unchanged():
    queries = ec.recorded_queries()
    assert "promotion.rq" in queries and "cq-10-1.rq" in queries and "cq-11-4.rq" in queries
    assert queries["cq-10-1.rq"] == recorded_query("# CQ 10.1:")
    assert queries["promotion.rq"] == recorded_query("# Promotion:")


def test_an_illustration_without_a_name_is_not_a_recorded_query():
    exported = set(ec.recorded_queries().values())
    assert not [q for q in exported if not ec.MARKER.search(q)]


def test_two_queries_with_one_name_are_refused(tmp_path):
    orsd = tmp_path / ec.ORSD
    orsd.parent.mkdir(parents=True)
    block = "```sparql\n# CQ 1.1: one\nSELECT * WHERE { ?s ?p ?o }\n```\n"
    orsd.write_text(block + block, encoding="utf-8")
    with pytest.raises(ValueError, match="cq-1-1.rq"):
        ec.recorded_queries(tmp_path)


def test_the_export_holds_every_shape_query_and_the_module_versions(tmp_path):
    manifest = ec.export(tmp_path / "out", version="1.0.0")
    out = tmp_path / "out"
    assert json.loads((out / "manifest.json").read_text(encoding="utf-8")) == manifest
    assert manifest["version"] == "1.0.0"
    shapes = sorted(p.relative_to(ROOT / "data-validation").as_posix() for p in (ROOT / "data-validation").rglob("*.shacl.ttl"))
    assert manifest["shapes"] == [f"shapes/{s}" for s in shapes] and "shapes/release/public-locations.shacl.ttl" in manifest["shapes"]
    for path in manifest["shapes"] + manifest["queries"]:
        assert (out / path).is_file(), path
    assert (out / "shapes" / "configuration.shacl.ttl").read_bytes() == (ROOT / "data-validation" / "configuration.shacl.ttl").read_bytes()
    assert set(manifest["testedWithModules"]) == {p.stem for p in (ROOT / "src").glob("*.ttl")}


def test_the_version_defaults_to_the_newest_release_in_the_changelog(tmp_path):
    (tmp_path / "changelogs").mkdir()
    (tmp_path / ec.CHANGELOG).write_text("# Changelog\n\n## [Unreleased]\n\n## [1.2.0] — 2026-11-02\n\n## [1.1.0] — 2026-11-01\n",
                                         encoding="utf-8")
    assert ec.released_version(tmp_path) == "1.2.0"
    (tmp_path / ec.CHANGELOG).write_text("# Changelog\n\n## [Unreleased]\n", encoding="utf-8")
    assert ec.released_version(tmp_path) is None


def test_the_script_needs_no_package_so_the_release_workflow_can_run_it():
    imports = [line for line in (ROOT / "scripts" / "export_checks.py").read_text(encoding="utf-8").splitlines()
               if line.startswith(("import ", "from "))]
    assert not [line for line in imports if "rdflib" in line or "pyshacl" in line], imports


def test_the_release_notes_are_the_changelog_section_and_the_addresses(tmp_path):
    (tmp_path / "changelogs").mkdir()
    (tmp_path / ec.CHANGELOG).write_text("# Changelog\n\n## [Unreleased]\n\n## [1.1.0] — 2026-11-02\n\n### Added\n- A shape.\n\n"
                                         "## [1.0.0] — 2026-11-01\n\n### Added\n- The first release.\n", encoding="utf-8")
    notes = ec.release_notes("1.1.0", tmp_path)
    assert "- A shape." in notes and "The first release." not in notes
    assert "https://w3id.org/adiro/checks/1.1.0/manifest.json" in notes
    with pytest.raises(ValueError):
        ec.release_notes("2.0.0", tmp_path)


def test_a_checks_tag_is_snapshotted_from_the_tag_and_published_whole():
    backup = (ROOT / ".github" / "workflows" / "backup-version.yml").read_text(encoding="utf-8")
    assert 'if [ "$MODULE" = "checks" ]' in backup
    assert "scripts/export_checks.py" in backup and "--root" in backup and "--notes" in backup
    deploy = (ROOT / ".github" / "workflows" / "generate-deploy-docs.yml").read_text(encoding="utf-8")
    assert "-path 'versions/checks/*'" in deploy  # the queries and the manifest, not only the .ttl files


def test_no_checks_file_looks_like_a_module_snapshot(tmp_path):
    # versions/<name>/<v>/<name>.ttl is a module snapshot to the scripts that scan versions/: the checks never write one
    ec.export(tmp_path / "1.0.0", version="1.0.0")
    assert not (tmp_path / "1.0.0" / "checks.ttl").exists()
