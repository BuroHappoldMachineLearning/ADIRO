"""Tests for the Release-notes generator (scripts/release_notes.py); the git/gh lookups are not exercised."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import release_notes as rn  # noqa: E402

TAGS = ["aec_x-v1.0.0", "aec_x-v2.0.0", "aec_x-v10.0.0", "aec_y-v9.0.0", "aec_x-v2.0.1"]


def test_previous_version_is_the_highest_lower_semver_of_the_same_module():
    assert rn.previous_version(TAGS, "aec_x", "2.0.1") == "2.0.0"
    assert rn.previous_version(TAGS, "aec_x", "10.0.0") == "2.0.1"  # numeric, not alphabetical
    assert rn.previous_version(TAGS, "aec_x", "1.0.0") is None
    assert rn.previous_version(TAGS, "aec_z", "1.0.0") is None


def test_bump_kind():
    assert [rn.bump_kind(p, v) for p, v in [(None, "1.0.0"), ("1.2.3", "2.0.0"), ("1.2.3", "1.3.0"), ("1.2.3", "1.2.4")]] == [
        "FIRST", "MAJOR", "MINOR", "PATCH"]


def test_render_links_docs_compare_and_prs():
    text = rn.render("aec_x", "2.0.1", "2.0.0", "### Added\n- a thing", [("#108", "Add a thing"), ("abc1234", "a direct commit")], "o/r")
    assert text.startswith("## aec_x 2.0.1")
    assert "**PATCH release** · 2.0.0 → 2.0.1" in text
    assert "[Documentation](https://burohappoldmachinelearning.github.io/ADIRO/ontologies/aec_x/)" in text
    assert "[Compare](https://github.com/o/r/compare/aec_x-v2.0.0...aec_x-v2.0.1)" in text
    assert "- [#108](https://github.com/o/r/pull/108) Add a thing" in text and "- `abc1234` a direct commit" in text
    assert "### Added\n- a thing" in text and "https://w3id.org/adiro/aec_x/2.0.1" in text


def test_render_a_first_release_has_no_compare_or_pr_list():
    text = rn.render("aec_x", "1.0.0", None, "notes", [], "o/r")
    assert "**First release**" in text and "Compare" not in text and "Pull requests in this release" not in text
    assert "First tagged release of this module" in text


class _Result:
    def __init__(self, stdout="", returncode=0):
        self.stdout, self.returncode = stdout, returncode


def _fake_run(git_log, gh_by_sha, calls):
    """A stand-in for release_notes._run: `git log` returns git_log, `gh api .../commits/<sha>/pulls` returns gh_by_sha[sha]."""
    def run(args, root):
        calls.append(args)
        if args[0] == "git":
            return _Result(git_log)
        if args[0] == "gh":
            sha = args[2].split("/commits/")[1].split("/")[0]
            result = gh_by_sha[sha]
            if isinstance(result, Exception):
                raise result
            return result
        raise AssertionError(args)
    return run


def test_collect_changes_dedupes_prs_and_falls_back_to_bare_commits(monkeypatch):
    calls = []
    git_log = "aaa1111\tfix one\nbbb2222\tfix two\nccc3333\tdirect push\n"
    gh = {
        "aaa1111": _Result("108\tAdd a thing\n"),
        "bbb2222": _Result("108\tAdd a thing\n"),  # second commit of the same PR
        "ccc3333": _Result(""),  # pushed straight to main: no PR
    }
    monkeypatch.setattr(rn, "_run", _fake_run(git_log, gh, calls))
    assert rn.collect_changes(".", "o/r", "aec_x", "2.0.0", "aec_x-v2.0.1") == [("#108", "Add a thing"), ("ccc3333", "direct push")]
    git_call = calls[0]
    assert "aec_x-v2.0.0..aec_x-v2.0.1" in git_call and git_call[-1] == "src/aec_x.ttl"  # range and the ontology file only


def test_collect_changes_warns_when_the_gh_lookup_fails(monkeypatch, capsys):
    git_log = "aaa1111\tfix one\n"
    monkeypatch.setattr(rn, "_run", _fake_run(git_log, {"aaa1111": _Result("", returncode=1)}, []))
    assert rn.collect_changes(".", "o/r", "aec_x", "2.0.0", "aec_x-v2.0.1") == [("aaa1111", "fix one")]
    assert "::warning::PR lookup failed for aaa1111" in capsys.readouterr().err  # not a silent downgrade


def test_collect_changes_without_the_gh_cli_lists_commits_and_warns(monkeypatch, capsys):
    monkeypatch.setattr(rn, "_run", _fake_run("aaa1111\tfix one\n", {"aaa1111": FileNotFoundError()}, []))
    assert rn.collect_changes(".", "o/r", "aec_x", "2.0.0", "aec_x-v2.0.1") == [("aaa1111", "fix one")]
    assert "gh CLI not found" in capsys.readouterr().err


def test_collect_changes_for_a_first_release_makes_no_calls(monkeypatch):
    calls = []
    monkeypatch.setattr(rn, "_run", _fake_run("", {}, calls))
    assert rn.collect_changes(".", "o/r", "aec_x", None, "aec_x-v1.0.0") == [] and calls == []
