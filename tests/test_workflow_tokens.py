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
    text = (WORKFLOWS / "post-deploy-checks.yml").read_text(encoding="utf-8")
    accepted = re.search(r"--accept '([^']+)'", text).group(1)
    codes = set()
    for part in accepted.split(","):
        low, _, high = part.partition("..=")
        codes.update(range(int(low), int(high or low) + 1))
    assert {502, 503, 504} <= codes, "a transient 5xx from GitHub must not fail the deploy (#202)"
    assert 404 not in codes and 410 not in codes, "a missing page must still fail: it is how a wrong issue number is caught"
    assert re.search(r"--max-concurrency \d+", text), "the link check limits its concurrency instead of using lychee's default of 128"


def test_deploys_do_not_wait_for_the_checks_of_the_published_site():
    """The link and release-IRI checks run in their own workflow, after a successful deploy of the default branch (#217)."""
    import yaml

    deploy = yaml.safe_load((WORKFLOWS / "generate-deploy-docs.yml").read_text(encoding="utf-8"))
    checks_text = (WORKFLOWS / "post-deploy-checks.yml").read_text(encoding="utf-8")
    checks = yaml.safe_load(checks_text)
    assert not {"check-links", "verify-prior-versions"} & set(deploy["jobs"]), "the checks are not in the deploy's queue"
    assert {"check-links", "verify-prior-versions"} <= set(checks["jobs"])
    on = checks.get("on", checks.get(True))  # PyYAML reads the key `on` as True
    assert on["workflow_run"]["workflows"] == [deploy["name"]] and on["workflow_run"]["types"] == ["completed"]
    assert checks["concurrency"]["cancel-in-progress"] is True, "a newer deploy cancels the checks of an older one"
    assert "conclusion == 'success'" in checks["jobs"]["deployed"]["if"] and "default_branch" in checks["jobs"]["deployed"]["if"]
    # a run for a failed deploy, or another branch's, must not cancel the checks of the live site: it gets its own group
    group = checks["concurrency"]["group"]
    assert "conclusion == 'success'" in group and "default_branch" in group and "github.run_id" in group
    # a manual run reads the artifact of the latest successful deploy, which can be days old
    upload = next(s for j in deploy["jobs"].values() for s in j.get("steps", []) if str(s.get("uses", "")).startswith("actions/upload-artifact") and s["with"]["name"] == "docs")
    assert upload["with"]["retention-days"] >= 7
    watched = (WORKFLOWS / "alert-on-failure.yml").read_text(encoding="utf-8")
    assert f"- {checks['name']}" in watched, "the alert watcher watches the checks"
