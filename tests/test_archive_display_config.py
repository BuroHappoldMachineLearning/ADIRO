"""Archiving each release's display config next to its TTL (#140)."""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import archive_display_config as adc  # noqa: E402


def git(root, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=root, check=True, capture_output=True)


def commit(root, message):
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", message)


def write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def repo(tmp_path):
    git(tmp_path, "init", "-q")
    return tmp_path


def test_archive_copies_the_config_as_it_was_at_the_ref_not_the_current_one(tmp_path):
    root = repo(tmp_path)
    write(root, "src/m.display.json", '{"v": 1}')
    commit(root, "release 1")
    git(root, "tag", "m-v1.0.0")
    write(root, "src/m.display.json", '{"v": 2}')
    commit(root, "later")
    path = adc.archive(root, "m", "1.0.0", "refs/tags/m-v1.0.0")
    assert path == root / "versions" / "m" / "1.0.0" / "m.display.json"
    assert path.read_text(encoding="utf-8") == '{"v": 1}'


def test_archive_does_nothing_when_the_module_has_no_config_at_the_ref(tmp_path):
    root = repo(tmp_path)
    write(root, "src/m.ttl", "x")
    commit(root, "release")
    assert adc.archive(root, "m", "1.0.0", "HEAD") is None
    assert not (root / "versions").exists()


def test_an_archived_config_is_never_overwritten(tmp_path):
    root = repo(tmp_path)
    write(root, "src/m.display.json", '{"v": 2}')
    write(root, "versions/m/1.0.0/m.display.json", '{"v": 1}')
    commit(root, "x")
    adc.archive(root, "m", "1.0.0", "HEAD")
    assert (root / "versions/m/1.0.0/m.display.json").read_text(encoding="utf-8") == '{"v": 1}'


def test_backfill_uses_the_tag_then_the_archive_commit_then_the_current_config(tmp_path):
    root = repo(tmp_path)
    write(root, "src/m.display.json", '{"v": "tagged"}')
    write(root, "versions/m/1.0.0/m.ttl", "a")
    commit(root, "release 1.0.0")
    git(root, "tag", "m-v1.0.0")
    write(root, "src/m.display.json", '{"v": "at 1.1.0"}')
    commit(root, "edit config")
    write(root, "versions/m/1.1.0/m.ttl", "b")  # archived with no tag
    commit(root, "snapshot 1.1.0")
    write(root, "src/m.display.json", '{"v": "current"}')
    commit(root, "edit again")
    write(root, "versions/m/0.9.0/m.ttl", "c")  # archived before any config existed in its tree... but the file is untracked
    done = adc.backfill(root)
    got = {(m, v): how for m, v, how in done}
    assert got[("m", "1.0.0")] == "tag" and got[("m", "1.1.0")] == "archive commit"
    read = lambda v: (root / f"versions/m/{v}/m.display.json").read_text(encoding="utf-8")
    assert read("1.0.0") == '{"v": "tagged"}'
    assert read("1.1.0") == '{"v": "at 1.1.0"}'
    assert got[("m", "0.9.0")] == "current" and read("0.9.0") == '{"v": "current"}'


def test_backfill_leaves_releases_that_already_have_a_config_and_reports_nothing_twice(tmp_path):
    root = repo(tmp_path)
    write(root, "src/m.display.json", "{}")
    write(root, "versions/m/1.0.0/m.ttl", "a")
    commit(root, "release")
    assert len(adc.backfill(root)) == 1
    assert adc.backfill(root) == []


def test_backfill_skips_a_release_when_no_config_exists_anywhere(tmp_path):
    root = repo(tmp_path)
    write(root, "versions/m/1.0.0/m.ttl", "a")
    commit(root, "release")
    assert adc.backfill(root) == []
    assert not (root / "versions/m/1.0.0/m.display.json").exists()
