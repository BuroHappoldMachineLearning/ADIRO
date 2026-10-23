"""The ADIRO Bot merges main into a pull request whose only conflict is the worklog (#206)."""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import worklog_conflicts as wc  # noqa: E402

WORKFLOW = ROOT / ".github" / "workflows" / "worklog-conflicts.yml"
OLD = "## 2026-10-01 - An old entry\n\nOld text.\n"


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout.strip()


def commit(repo, files, message):
    for name, text in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        git(repo, "add", name)
    git(repo, "commit", "--quiet", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def make_repo(tmp_path, pr_files, main_files):
    """A repository with a worklog; `pr` and `main` each change files from the same starting point."""
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "--quiet", "-b", "main")
    git(repo, "config", "user.name", "t")
    git(repo, "config", "user.email", "t@example.com")
    git(repo, "config", "core.autocrlf", "false")
    commit(repo, {wc.WORKLOG: OLD, "a.txt": "one\n"}, "start")
    git(repo, "checkout", "--quiet", "-b", "pr")
    commit(repo, pr_files, "pr change")
    git(repo, "checkout", "--quiet", "main")
    commit(repo, main_files, "main change")
    return repo


def entry(title):
    return f"## 2026-10-21 - {title}\n\nText of {title}.\n\n"


def test_a_worklog_only_conflict_is_merged_with_both_entries_and_the_pr_entry_first(tmp_path):
    repo = make_repo(tmp_path, {wc.WORKLOG: entry("PR") + OLD}, {wc.WORKLOG: entry("Main") + OLD, "b.txt": "new\n"})
    status = wc.merge(repo, "pr", "main", "pr")
    assert status["status"] == wc.READY
    text = git(repo, "show", f"HEAD:{wc.WORKLOG}") + "\n"
    assert text == entry("PR") + entry("Main") + OLD
    parents = git(repo, "rev-list", "--parents", "-n", "1", "HEAD").split()[1:]
    assert parents == [status["head_sha"], status["base_sha"]], "the PR head first, then main: a normal merge of main into the branch"
    assert git(repo, "show", "HEAD:b.txt") == "new", "the rest of main comes in with the merge"


def test_the_same_merge_gives_the_same_tree_so_the_push_job_can_check_it(tmp_path):
    repo = make_repo(tmp_path, {wc.WORKLOG: entry("PR") + OLD}, {wc.WORKLOG: entry("Main") + OLD})
    first = wc.merge(repo, "pr", "main", "pr")
    second = wc.merge(repo, "pr", "main", "pr")
    assert first["tree"] == second["tree"]


def test_any_other_conflict_is_left_to_the_author(tmp_path):
    repo = make_repo(tmp_path, {wc.WORKLOG: entry("PR") + OLD, "a.txt": "pr\n"},
                     {wc.WORKLOG: entry("Main") + OLD, "a.txt": "main\n"})
    status = wc.merge(repo, "pr", "main", "pr")
    assert status["status"] == wc.OTHER
    assert sorted(status["files"]) == ["a.txt", wc.WORKLOG]
    assert git(repo, "status", "--porcelain") == "", "the aborted merge leaves nothing behind"


def test_a_worklog_change_that_is_not_a_pure_addition_is_left_to_the_author(tmp_path):
    repo = make_repo(tmp_path, {wc.WORKLOG: entry("PR") + OLD.replace("Old text", "Rewritten")},
                     {wc.WORKLOG: entry("Main") + OLD})
    assert wc.merge(repo, "pr", "main", "pr")["status"] == wc.EDITED


def test_no_conflict_means_nothing_to_do(tmp_path):
    repo = make_repo(tmp_path, {"c.txt": "pr\n"}, {wc.WORKLOG: entry("Main") + OLD})
    assert wc.merge(repo, "pr", "main", "pr")["status"] == wc.CLEAN


def test_a_failing_check_stops_the_push_and_names_the_check(tmp_path):
    repo = make_repo(tmp_path, {wc.WORKLOG: entry("PR") + OLD}, {wc.WORKLOG: entry("Main") + OLD})
    verify = [("validation", ["ok"]), ("tests", ["fail"])]

    def runner(command, **_):
        return subprocess.CompletedProcess(command, 0 if command == ["ok"] else 1, "", "boom")

    status = wc.merge(repo, "pr", "main", "pr", verify=verify, runner=runner)
    assert status["status"] == wc.FAILED and status["failed"] == "tests"
    assert "**tests** fails" in wc.comment(status, "https://run")
    assert wc.comment({"status": wc.READY}, "https://run") == "", "a pushed merge removes an earlier failure comment"


def test_push_refuses_a_merge_that_is_not_the_verified_one(tmp_path):
    repo = make_repo(tmp_path, {wc.WORKLOG: entry("PR") + OLD}, {wc.WORKLOG: entry("Main") + OLD})
    out = tmp_path / "status.json"
    args = ["--repo", str(repo), "--head", "pr", "--base", "main", "--branch", "pr", "--out", str(out)]
    out.write_text('{"status": "ready", "tree": "0000", "head_sha": "x"}', encoding="utf-8")
    assert wc.main(["push", *args]) == 1
    out.write_text('{"status": "verify-failed"}', encoding="utf-8")
    assert wc.main(["push", *args]) == 1
    good = wc.merge(repo, "pr", "main", "pr")
    out.write_text(json.dumps({k: good[k] for k in ("status", "tree", "head_sha", "base_sha")}), encoding="utf-8")
    assert wc.main(["push", *args]) == 0


def test_push_merges_the_verified_main_commit_when_main_moved_on_meanwhile(tmp_path, capsys):
    # #224: the docs deploy commits to main between the merge and the push jobs; the verified merge is still pushed
    repo = make_repo(tmp_path, {wc.WORKLOG: entry("PR") + OLD}, {wc.WORKLOG: entry("Main") + OLD})
    verified = wc.merge(repo, "pr", "main", "pr")
    git(repo, "checkout", "--quiet", "main")
    commit(repo, {"docs/generated.md": "regenerated\n"}, "docs: Auto-generate ontology documentation [skip actions]")
    out = tmp_path / "status.json"
    out.write_text(json.dumps(verified), encoding="utf-8")
    assert wc.main(["push", "--repo", str(repo), "--head", "pr", "--base", "main", "--branch", "pr", "--out", str(out)]) == 0
    assert git(repo, "rev-parse", "HEAD^{tree}") == verified["tree"], "the pushed tree is the verified one"
    assert git(repo, "rev-parse", "HEAD^2") == verified["base_sha"]
    assert "moved on since" in capsys.readouterr().out


def test_push_refuses_a_main_commit_that_is_not_on_main(tmp_path, capsys):
    # the status file comes from the job that runs the pull request's code: its main commit must be a commit of main
    repo = make_repo(tmp_path, {wc.WORKLOG: entry("PR") + OLD}, {wc.WORKLOG: entry("Main") + OLD})
    git(repo, "checkout", "--quiet", "-b", "other", "main~1")
    elsewhere = commit(repo, {wc.WORKLOG: entry("Elsewhere") + OLD}, "not on main")
    verified = wc.merge(repo, "pr", elsewhere, "pr")
    assert verified["status"] == wc.READY
    out = tmp_path / "status.json"
    args = ["push", "--repo", str(repo), "--head", "pr", "--base", "main", "--branch", "pr", "--out", str(out)]
    for base_sha in (elsewhere, "--upload-pack=x", ""):
        out.write_text(json.dumps({**verified, "base_sha": base_sha}), encoding="utf-8")
        assert wc.main(args) == 1
        assert "not a commit of main" in capsys.readouterr().out


def test_push_says_why_it_does_not_push(capsys):
    for status, words in [(wc.OTHER, "other files"), (wc.FAILED, "a check fails"), (None, "left no result")]:
        assert wc.push(Path("."), "pr", "main", "pr", Path("does-not-exist") if status is None else _status(status)) == 1
        assert words in capsys.readouterr().out


def _status(status):
    import tempfile

    path = Path(tempfile.mkdtemp()) / "status.json"
    path.write_text(json.dumps({"status": status}), encoding="utf-8")
    return path


def test_find_waits_for_github_to_compute_mergeable_and_skips_forks():
    listed = [
        {"number": 1, "headRefName": "a", "headRefOid": "s1", "baseRefName": "main", "isCrossRepository": False, "mergeable": "UNKNOWN"},
        {"number": 2, "headRefName": "b", "headRefOid": "s2", "baseRefName": "main", "isCrossRepository": True, "mergeable": "CONFLICTING"},
        {"number": 3, "headRefName": "c", "headRefOid": "s3", "baseRefName": "main", "isCrossRepository": False, "mergeable": "MERGEABLE"},
    ]

    def gh(*args):
        return listed if args[:2] == ("pr", "list") else {"mergeable": "CONFLICTING"}

    picked, forks = wc.candidates(wc.list_prs("main", None, gh=gh, sleep=lambda _: None))
    assert picked == [{"number": 1, "branch": "a", "head_sha": "s1"}]
    assert forks == [2]


def test_the_verification_runs_the_same_tests_as_the_pull_request_check():
    text = (ROOT / ".github" / "workflows" / "validate-ontology.yml").read_text(encoding="utf-8")
    ci = re.search(r"run: (uv run [^\n]*pytest tests -q)", text).group(1)
    assert " ".join(dict(wc.VERIFY)["tests"]) == ci


def job(text, name):
    start = text.index(f"\n  {name}:\n", text.index("\njobs:\n"))
    following = re.search(r"\n  [a-z-]+:\n", text[start + 1:])
    return text[start:start + 1 + following.start()] if following else text[start:]


def test_the_job_that_runs_the_pull_request_code_has_no_secrets():
    text = WORKFLOW.read_text(encoding="utf-8")
    merge = job(text, "merge")
    assert "secrets." not in merge and "app-token" not in merge
    assert "persist-credentials: false" in merge


def test_the_push_is_leased_on_the_head_find_saw_and_the_bot_token_job_checks_out_main():
    text = WORKFLOW.read_text(encoding="utf-8")
    push = job(text, "push")
    assert '--force-with-lease="refs/heads/${BRANCH}:${HEAD_SHA}"' in push
    assert not re.search(r"--force(?!-with-lease=)", push) and "+HEAD" not in push, "no bare --force and no + refspec"
    assert "ref: ${{ github.event.repository.default_branch }}" in push
    assert 'git worktree add --quiet --detach "$RUNNER_TEMP/merge"' in push, "the checkout that loads the local action stays on main"


def test_the_workflow_runs_main_s_copy_of_itself_and_runs_on_a_conflicting_pull_request():
    """`pull_request` does not run while a pull request conflicts, and runs the pull request's own copy of the file."""
    triggers = WORKFLOW.read_text(encoding="utf-8").split("\npermissions:")[0]
    assert "pull_request_target:" in triggers
    assert not re.search(r"^\s+pull_request:", triggers, re.M)
    assert "workflow_dispatch" not in triggers.split("\non:")[1], "a dispatch runs the file of the branch it names"
    assert "enable-cache: false" in job(WORKFLOW.read_text(encoding="utf-8"), "merge")


def test_a_lease_rejects_a_branch_reset_to_an_earlier_commit(tmp_path):
    """A plain push fast-forwards a branch reset during the run, putting back the commits the reset dropped."""
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--quiet", "--bare", str(remote)], check=True)
    repo = make_repo(tmp_path, {wc.WORKLOG: entry("PR") + OLD}, {wc.WORKLOG: entry("Main") + OLD})
    seen = git(repo, "rev-parse", "pr")
    git(repo, "push", "--quiet", str(remote), "pr:refs/heads/pr")
    git(repo, "push", "--quiet", "--force", str(remote), "pr~1:refs/heads/pr")  # the author resets meanwhile
    wc.merge(repo, "pr", "main", "pr")
    leased = subprocess.run(["git", "-C", str(repo), "push", "--quiet", f"--force-with-lease=refs/heads/pr:{seen}",
                             str(remote), "HEAD:refs/heads/pr"], capture_output=True)
    assert leased.returncode != 0
    assert git(remote, "rev-parse", "pr") == git(repo, "rev-parse", "pr~1"), "the reset stands"


def test_a_line_that_ends_both_entries_stays_in_both(tmp_path):
    """`git merge-file` kept a shared closing line once, under the second entry."""
    pr = "## 2026-10-21 - PR\n\nPR text.\nVerified: tests passed.\n\n"
    main = "## 2026-10-21 - Main\n\nMain text.\nVerified: tests passed.\n\n"
    repo = make_repo(tmp_path, {wc.WORKLOG: pr + OLD}, {wc.WORKLOG: main + OLD})
    assert wc.merge(repo, "pr", "main", "pr")["status"] == wc.READY
    assert git(repo, "show", f"HEAD:{wc.WORKLOG}") + "\n" == pr + main + OLD
