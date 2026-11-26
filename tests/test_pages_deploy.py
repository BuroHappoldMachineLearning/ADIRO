"""The Pages deploy does not race its own artifact (#319)."""
import re
from pathlib import Path

WORKFLOW = (Path(__file__).resolve().parent.parent / ".github" / "workflows" / "generate-deploy-docs.yml").read_text(encoding="utf-8")


def job(name):
    start = WORKFLOW.index(f"\n  {name}:\n", WORKFLOW.index("\njobs:\n"))
    following = re.search(r"\n  [a-z-]+:\n", WORKFLOW[start + 1:])
    return WORKFLOW[start:start + 1 + following.start()] if following else WORKFLOW[start:]


def test_the_pages_artifact_is_uploaded_a_job_before_the_deploy():
    """Uploaded in the deploy job, a second before `deploy-pages` asked for it, it was sometimes not yet listed."""
    assert "actions/upload-pages-artifact@" in job("generate-docs")
    assert "upload-pages-artifact" not in job("deploy") and "download-artifact" not in job("deploy")
    assert "needs: generate-docs" in job("deploy")


def test_a_failed_deploy_is_tried_once_more_and_the_second_failure_fails_the_job():
    deploy = job("deploy")
    first = deploy.split("id: deployment\n")[1].split("- name:")[0]
    assert "continue-on-error: true" in first and "actions/deploy-pages@" in first
    retry = deploy.split("id: deployment_retry\n")[1]
    assert "if: steps.deployment.outcome == 'failure'" in retry and "continue-on-error" not in retry
    assert "steps.deployment_retry.outputs.page_url" in deploy, "the environment shows the URL of whichever try passed"
