"""Workflow dispatch must use the ADIRO Bot token (#190).

A run created with the default GITHUB_TOKEN is started by github-actions[bot], and GitHub starts no `workflow_run` workflow
for it, so `alert-on-failure.yml` would never see its failure. A step that runs `gh workflow run` therefore authenticates
with the ADIRO Bot app token, as the release workflow already does.
"""
import re
from pathlib import Path

WORKFLOWS = Path(__file__).resolve().parent.parent / ".github" / "workflows"


def steps(text):
    """The text of each step: from a `- name:` / `- uses:` / `- run:` line at the step indent to the next one."""
    parts = re.split(r"(?m)^(?=      - (?:name|uses|run|id|if):)", text)
    return [code(p) for p in parts if p.strip()]


def code(step):
    """The step without its comment lines: a comment may name GITHUB_TOKEN to explain why it is not used."""
    return "\n".join(line for line in step.splitlines() if not line.lstrip().startswith("#"))


def test_a_step_that_dispatches_a_workflow_does_not_use_github_token():
    offenders = []
    for path in sorted(WORKFLOWS.glob("*.yml")):
        for step in steps(path.read_text(encoding="utf-8")):
            if re.search(r"^\s*run:.*\bgh workflow run\b", step, re.M) or re.search(r"^\s+gh workflow run\b", step, re.M):
                if "GITHUB_TOKEN" in step or "github.token" in step or "app-token.outputs.token" not in step:
                    offenders.append(f"{path.name}: {step.strip().splitlines()[0]}")
    assert offenders == [], "dispatch with the ADIRO Bot token (steps.app-token.outputs.token), not GITHUB_TOKEN: " + "; ".join(offenders)


def test_the_commit_back_job_starts_from_the_tip_of_the_branch():
    text = (WORKFLOWS / "generate-deploy-docs.yml").read_text(encoding="utf-8")
    generate = text[text.index("  generate-docs:"):text.index("  deploy:")]
    assert "ref: ${{ github.ref_name }}" in generate, "generate-docs must check out the branch by name, not the dispatched commit"


def test_the_link_check_tolerates_a_transient_server_error_but_not_a_missing_page():
    text = (WORKFLOWS / "generate-deploy-docs.yml").read_text(encoding="utf-8")
    accepted = re.search(r"--accept '([^']+)'", text).group(1)
    codes = set()
    for part in accepted.split(","):
        low, _, high = part.partition("..=")
        codes.update(range(int(low), int(high or low) + 1))
    assert {502, 503, 504} <= codes, "a transient 5xx from GitHub must not fail the deploy (#202)"
    assert 404 not in codes and 410 not in codes, "a missing page must still fail: it is how a wrong issue number is caught"
    assert re.search(r"--max-concurrency \d+", text), "the link check limits its concurrency instead of using lychee's default of 128"
