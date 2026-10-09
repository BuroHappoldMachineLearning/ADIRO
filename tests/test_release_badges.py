"""Tests for the per-module release-badge data (scripts/release_badges.py)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import release_badges as rb  # noqa: E402


def make_repo(tmp_path, versions):
    (tmp_path / "src").mkdir()
    for module, vers in versions.items():
        (tmp_path / "src" / f"{module}.ttl").write_text("# ttl", encoding="utf-8")
        for v in vers:
            d = tmp_path / "versions" / module / v
            d.mkdir(parents=True)
            (d / f"{module}.ttl").write_text("# snapshot", encoding="utf-8")
    return tmp_path


def test_latest_is_the_highest_semver_not_the_alphabetical_last(tmp_path):
    repo = make_repo(tmp_path, {"aec_x": ["2.0.0", "10.0.0", "9.1.0"]})
    assert rb.latest_released_version(repo, "aec_x") == "10.0.0"


def test_a_module_with_no_snapshot_is_unreleased(tmp_path):
    repo = make_repo(tmp_path, {"aec_new": []})
    assert rb.badge_json(repo, "aec_new") == {"schemaVersion": 1, "label": "aec_new", "message": "unreleased", "color": "lightgrey"}


def test_a_version_directory_without_the_snapshot_file_is_ignored(tmp_path):
    repo = make_repo(tmp_path, {"aec_x": ["1.0.0"]})
    (repo / "versions" / "aec_x" / "2.0.0").mkdir()
    assert rb.latest_released_version(repo, "aec_x") == "1.0.0"


def test_files_follow_the_shields_endpoint_schema(tmp_path):
    repo = make_repo(tmp_path, {"aec_x": ["1.2.3"], "aec_y": ["4.0.0"]})
    written = rb.write_release_badges(repo, repo / "docs")
    assert [p.name for p in written] == ["aec_x.json", "aec_y.json"]
    data = json.loads(written[0].read_text(encoding="utf-8"))
    assert data == {"schemaVersion": 1, "label": "aec_x", "message": "1.2.3", "color": "16305f"}  # only keys shields accepts
