#!/usr/bin/env python3
"""One-way mirror of GitHub issues into YouTrack (GitHub -> YouTrack).

This implements the "inbox" model agreed in YouTrack MAN-8 and documented in
the "YouTrack and VCS guidance" article (MAN-A-3):

  * GitHub is the source of truth for a public issue's existence and its public
    description/discussion.
  * YouTrack holds an internal planning overlay (State, Assignee, Estimate, ...)
    that is deliberately NOT pushed back to GitHub. There is no reverse sync.

The script is invoked by .github/workflows/sync-issues-to-youtrack.yml on
`issues` events (opened / edited / reopened / closed).

Idempotency
-----------
On first mirror the script creates a YouTrack issue and posts a marker comment
back on the GitHub issue:

    <!-- youtrack-id: RES-123 -->

On every later event it reads that marker to find the existing YouTrack issue,
so re-runs and edits update in place instead of creating duplicates. No YouTrack
custom field or full-text search is required.

Required environment
---------------------
  YOUTRACK_URL     Base URL, e.g. https://bhmlrnd.youtrack.cloud
  YOUTRACK_TOKEN   YouTrack permanent token (perm:...)
  YOUTRACK_PROJECT Short name / key of the target project, e.g. RES
  GITHUB_TOKEN     Provided automatically by Actions (needs issues: write)
  GITHUB_REPOSITORY / GITHUB_EVENT_PATH / GITHUB_EVENT_NAME  (Actions defaults)

Optional
--------
  YOUTRACK_TAG     Name of a tag to apply to mirrored issues, e.g. ADIRO
                   (best-effort; failure to apply is non-fatal)
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request

MARKER_RE = re.compile(r"<!--\s*youtrack-id:\s*([A-Za-z0-9]+-\d+)\s*-->")


def fail(msg: str) -> "NoReturn":  # type: ignore[name-defined]
    print(f"::error::{msg}", file=sys.stderr)
    sys.exit(1)


def env(name: str, required: bool = True, default: str = "") -> str:
    val = os.environ.get(name, default).strip()
    if required and not val:
        fail(f"Missing required environment variable: {name}")
    return val


def _request(method: str, url: str, headers: dict, payload: dict | None = None) -> object:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else None
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        fail(f"{method} {url} -> HTTP {exc.code}: {detail}")
    except urllib.error.URLError as exc:
        fail(f"{method} {url} -> {exc}")


# --------------------------------------------------------------------------- #
# YouTrack helpers
# --------------------------------------------------------------------------- #
class YouTrack:
    def __init__(self, base_url: str, token: str) -> None:
        self.base = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def resolve_project_id(self, short_name: str) -> str:
        url = f"{self.base}/api/admin/projects?fields=id,shortName,name&$top=1000"
        projects = _request("GET", url, self.headers) or []
        for proj in projects:
            if proj.get("shortName", "").lower() == short_name.lower():
                return proj["id"]
        available = ", ".join(p.get("shortName", "?") for p in projects)
        fail(f"YouTrack project '{short_name}' not found. Available: {available}")

    def create_issue(
        self, project_id: str, summary: str, description: str, custom_fields: list | None = None
    ) -> dict:
        url = f"{self.base}/api/issues?fields=id,idReadable"
        payload = {
            "project": {"id": project_id},
            "summary": summary,
            "description": description,
        }
        if custom_fields:
            payload["customFields"] = custom_fields
        return _request("POST", url, self.headers, payload)  # type: ignore[return-value]

    def update_issue(self, issue_id: str, summary: str, description: str) -> dict:
        url = f"{self.base}/api/issues/{issue_id}?fields=id,idReadable"
        payload = {"summary": summary, "description": description}
        return _request("POST", url, self.headers, payload)  # type: ignore[return-value]

    def add_comment(self, issue_id: str, text: str) -> None:
        url = f"{self.base}/api/issues/{issue_id}/comments?fields=id"
        _request("POST", url, self.headers, {"text": text})

    def apply_tag(self, issue_id: str, tag_name: str) -> None:
        """Best-effort: apply an existing tag by name. Non-fatal on failure."""
        try:
            url = f"{self.base}/api/issueTags?fields=id,name&$top=1000"
            tags = _request("GET", url, self.headers) or []
            tag = next((t for t in tags if t.get("name", "").lower() == tag_name.lower()), None)
            if not tag:
                print(f"::warning::YouTrack tag '{tag_name}' not found; skipping tag.")
                return
            tag_url = f"{self.base}/api/issues/{issue_id}/tags?fields=id"
            _request("POST", tag_url, self.headers, {"id": tag["id"]})
        except SystemExit:
            # _request calls fail() -> SystemExit; downgrade tagging to a warning.
            print(f"::warning::Could not apply tag '{tag_name}' (non-fatal).")


# --------------------------------------------------------------------------- #
# GitHub helpers
# --------------------------------------------------------------------------- #
class GitHub:
    def __init__(self, token: str, repo: str) -> None:
        self.repo = repo
        self.api = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        }

    def find_marker(self, issue_number: int) -> str | None:
        url = f"{self.api}/repos/{self.repo}/issues/{issue_number}/comments?per_page=100"
        comments = _request("GET", url, self.headers) or []
        for comment in comments:
            match = MARKER_RE.search(comment.get("body", ""))
            if match:
                return match.group(1)
        return None

    def post_marker(self, issue_number: int, youtrack_id: str, youtrack_url: str) -> None:
        url = f"{self.api}/repos/{self.repo}/issues/{issue_number}/comments"
        body = (
            f"🔁 Mirrored into our internal tracker as **[{youtrack_id}]({youtrack_url})** "
            f"for triage and planning.\n\n"
            f"This GitHub issue remains the source of truth for public discussion — "
            f"keep the conversation here.\n\n"
            f"<!-- youtrack-id: {youtrack_id} -->"
        )
        _request("POST", url, self.headers, {"body": body})


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def build_description(issue: dict, repo: str) -> str:
    author = issue.get("user", {}).get("login", "unknown")
    html_url = issue.get("html_url", "")
    number = issue.get("number")
    body = issue.get("body") or "_(no description provided)_"
    return (
        f"> 🔁 **Mirrored from GitHub (one-way).** Source of truth for public "
        f"content: {html_url}\n"
        f"> Filed by **@{author}** in `{repo}` as issue #{number}.\n"
        f"> Do internal planning here; edit public content on GitHub.\n\n"
        f"{body}"
    )


def build_custom_fields() -> list:
    """Custom fields required by the target YouTrack project, from env.

    RES enforces a required `Assignee` (workflow rule), so mirrored issues must
    carry one — set YOUTRACK_ASSIGNEE to a login. State/Size are optional here
    (they have project defaults); set YOUTRACK_STATE / YOUTRACK_SIZE only if the
    project also requires them without a default.
    """
    fields: list = []
    assignee = os.environ.get("YOUTRACK_ASSIGNEE", "").strip()
    if assignee:
        # RES's Assignee is a MULTI-user field (schema: "Array of logins"), so the
        # field type is MultiUserIssueCustomField and the value must be a list.
        fields.append(
            {
                "name": "Assignee",
                "$type": "MultiUserIssueCustomField",
                "value": [{"login": assignee, "$type": "User"}],
            }
        )
    state = os.environ.get("YOUTRACK_STATE", "").strip()
    if state:
        fields.append(
            {
                "name": "State",
                "$type": "StateIssueCustomField",
                "value": {"name": state, "$type": "StateBundleElement"},
            }
        )
    size = os.environ.get("YOUTRACK_SIZE", "").strip()
    if size:
        fields.append(
            {
                "name": "Size",
                "$type": "SingleEnumIssueCustomField",
                "value": {"name": size, "$type": "EnumBundleElement"},
            }
        )
    estimation = os.environ.get("YOUTRACK_ESTIMATION", "").strip()
    if estimation:
        fields.append(
            {
                "name": "Estimation-hours",
                "$type": "SimpleIssueCustomField",
                "value": int(estimation),
            }
        )
    return fields


def main() -> None:
    event_name = env("GITHUB_EVENT_NAME")
    event_path = env("GITHUB_EVENT_PATH")
    repo = env("GITHUB_REPOSITORY")

    with open(event_path, "r", encoding="utf-8") as fh:
        event = json.load(fh)

    if event_name != "issues":
        print(f"Ignoring non-issue event: {event_name}")
        return

    action = event.get("action", "")
    issue = event.get("issue", {})
    number = issue.get("number")
    title = issue.get("summary") or issue.get("title") or f"GitHub issue #{number}"

    yt = YouTrack(env("YOUTRACK_URL"), env("YOUTRACK_TOKEN"))
    gh = GitHub(env("GITHUB_TOKEN"), repo)
    project_key = env("YOUTRACK_PROJECT")
    tag_name = env("YOUTRACK_TAG", required=False)

    existing_id = gh.find_marker(number)
    description = build_description(issue, repo)
    summary = f"[GitHub #{number}] {title}"

    if action == "closed":
        if existing_id:
            yt.add_comment(existing_id, f"ℹ️ The source GitHub issue #{number} was **closed**.")
            print(f"Commented on {existing_id}: GitHub issue closed.")
        else:
            print("Issue closed but no YouTrack mirror exists; nothing to do.")
        return

    if action == "reopened" and existing_id:
        yt.add_comment(existing_id, f"ℹ️ The source GitHub issue #{number} was **reopened**.")

    if existing_id:
        yt.update_issue(existing_id, summary, description)
        print(f"Updated existing YouTrack issue {existing_id} from GitHub #{number}.")
        return

    # No mirror yet -> create one and record the mapping back on GitHub.
    project_id = yt.resolve_project_id(project_key)
    created = yt.create_issue(project_id, summary, description, build_custom_fields())
    youtrack_id = created["idReadable"]
    if tag_name:
        yt.apply_tag(youtrack_id, tag_name)
    youtrack_url = f"{yt.base}/issue/{youtrack_id}"
    gh.post_marker(number, youtrack_id, youtrack_url)
    print(f"Created YouTrack issue {youtrack_id} from GitHub #{number}.")


if __name__ == "__main__":
    main()
