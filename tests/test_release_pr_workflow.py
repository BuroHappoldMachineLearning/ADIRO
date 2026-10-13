"""The Release PR workflow must commit every file the release cut changes (#128).

`prepare_release.py apply` writes several files; the workflow commits only what its `git add` line names. A file the
cut changes but the workflow does not stage is changed in the bot's working tree and never reaches the Release PR,
which then ships new versions with stale files (the README badge links were missed this way).
"""
import re
import sys
from pathlib import Path

import pytest

pytest.importorskip("rdflib")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import prepare_release as pr  # noqa: E402
from test_prepare_release import ENTRY, make_repo  # noqa: E402


def staged_paths():
    text = (ROOT / ".github" / "workflows" / "release-pr.yml").read_text(encoding="utf-8")
    match = re.search(r"git add -A ([^\r\n]+)", text)
    assert match, "release-pr.yml has no `git add -A <paths>` line"
    return match.group(1).split()


def snapshot(repo):
    return {p.relative_to(repo).as_posix(): p.read_bytes() for p in repo.rglob("*") if p.is_file()}


def test_every_file_the_cut_changes_is_staged_by_the_workflow(tmp_path):
    repo = make_repo(tmp_path, ":B a owl:Class .\n", ENTRY)  # src, changelogs, CHANGELOG.md, AGENTS.md, an archive
    (repo / "README.md").write_text('<a href="https://github.com/o/r/releases/tag/aec_x-v1.0.0"><img alt="aec_x"></a>\n', encoding="utf-8")
    (repo / "config").mkdir()
    (repo / "config" / "release_overrides.json").write_text('{"aec_x": "major"}\n', encoding="utf-8")

    before = snapshot(repo)
    pr.apply_plan(repo, pr.plan(repo), "2026-10-09")
    after = snapshot(repo)

    changed = {path for path in after if before.get(path) != after[path]}
    assert {"src/aec_x.ttl", "changelogs/aec_x.md", "CHANGELOG.md", "AGENTS.md", "README.md", "config/release_overrides.json"} <= changed
    staged = staged_paths()
    unstaged = sorted(p for p in changed if not any(p == s or p.startswith(s.rstrip("/") + "/") for s in staged))
    assert not unstaged, f"the cut changes {unstaged} but .github/workflows/release-pr.yml does not stage them (git add -A {' '.join(staged)})"
