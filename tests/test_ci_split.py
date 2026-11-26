"""The tests run in their own check on every pull request; the ontology checks run when a pull request changes what they read (#316)."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"
ENTRY_POINTS = ("validate_ontology.py", "compat_diff.py")
# Imported only to order the QC comment's table (#300), which ontology-reasoning.yml renders; validate-ontology.yml
# never writes the table, so a change to it changes nothing this workflow checks.
NOT_INPUTS = {"generate_docs.py"}


def paths(workflow):
    block = re.search(r"(?m)^    paths:\n((?:      - .*\n)+)", (WORKFLOWS / workflow).read_text(encoding="utf-8"))
    assert block, f"{workflow} has a paths filter"
    return re.findall(r"- '([^']+)'", block.group(1))


def local_imports(script, seen=None):
    """The scripts/ modules `script` imports, transitively."""
    seen = set() if seen is None else seen
    text = (ROOT / "scripts" / script).read_text(encoding="utf-8")
    for name in re.findall(r"(?m)^\s*(?:import|from) (\w+)", text):
        module = f"{name}.py"
        if (ROOT / "scripts" / module).is_file() and module not in seen and module not in NOT_INPUTS:
            seen.add(module)
            local_imports(module, seen)
    return seen


def test_the_ontology_check_runs_when_a_script_it_runs_or_imports_changes():
    filtered = set(paths("validate-ontology.yml"))
    scripts = set(ENTRY_POINTS).union(*(local_imports(s) for s in ENTRY_POINTS))
    missing = sorted(s for s in scripts if f"scripts/{s}" not in filtered)
    assert not missing, f"add to the paths of validate-ontology.yml: {missing}"
    for data in ("src/**", "versions/**", "assets/**", "changelogs/**", "config/**", ".github/workflows/validate-ontology.yml"):
        assert data in filtered, data


def test_the_tests_run_on_every_pull_request_and_only_in_their_own_check():
    tests = (WORKFLOWS / "tests.yml").read_text(encoding="utf-8")
    assert "pytest tests" in tests and "paths:" not in tests, "every pull request, whatever it changes"
    assert "pytest" not in (WORKFLOWS / "validate-ontology.yml").read_text(encoding="utf-8")


def test_the_internal_names_check_runs_on_every_pull_request_as_a_test():
    """It reads files outside the ontology paths (#89), so the filtered validator alone would miss a pull request."""
    text = (ROOT / "tests" / "test_internal_names.py").read_text(encoding="utf-8")
    assert "find_internal_names(Path(__file__).resolve().parent.parent) == []" in text


BOT_SKIP = "github.actor != 'adiro-bot[bot]' || github.head_ref == 'release/next'"


def test_the_checks_the_worklog_bot_already_ran_skip_its_merge_commits_but_not_the_release_pr():
    """The bot runs the validator and the tests on its merge before pushing it, and pushes only if they pass (#206).
    Running them again on its commit is the same work twice; the Release PR, also pushed by the bot, is checked."""
    for workflow in ("tests.yml", "validate-ontology.yml", "pr-guidance.yml"):
        text = (WORKFLOWS / workflow).read_text(encoding="utf-8")
        assert BOT_SKIP in text, workflow
    assert "adiro-bot" not in (WORKFLOWS / "ontology-reasoning.yml").read_text(encoding="utf-8"), \
        "the reasoner is a gate the bot does not run"


def test_the_bot_runs_the_validator_as_the_pull_request_check_does():
    """What the skip relies on: the same enforcement flags in the bot's verification as in validate-ontology.yml."""
    flags = lambda text: set(re.findall(r"(?m)^\s+(ENFORCE_\w+): \"1\"", text))  # set, not commented out
    ci = flags((WORKFLOWS / "validate-ontology.yml").read_text(encoding="utf-8"))
    merge = (WORKFLOWS / "worklog-conflicts.yml").read_text(encoding="utf-8").split("Merge, resolve the worklog and verify")[1]
    assert ci and ci <= flags(merge.split("- name:")[0]), (ci, merge[:300])
