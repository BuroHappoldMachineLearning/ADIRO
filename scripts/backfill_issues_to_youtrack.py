#!/usr/bin/env python3
"""One-shot backfill of pre-existing GitHub issues into YouTrack.

The event-driven mirror (`sync_issue_to_youtrack.py`) only fires for issues
opened/edited AFTER the automation went live. This script ports issues that
already existed, using the exact same logic so backfilled issues are
indistinguishable from auto-synced ones.

It is idempotent: any issue that already carries the `<!-- youtrack-id: KEY-N -->`
marker comment is skipped, so it is safe to re-run and it will never collide
with the live workflow.

Invoked by .github/workflows/backfill-issues-to-youtrack.yml (workflow_dispatch).

Environment (same as the live sync, plus two inputs)
----------------------------------------------------
  YOUTRACK_URL / YOUTRACK_TOKEN / YOUTRACK_PROJECT / YOUTRACK_TAG (optional)
  GITHUB_TOKEN / GITHUB_REPOSITORY
  BACKFILL_STATE    'open' (default) or 'all' — which issues to port
  BACKFILL_DRY_RUN  'true' (default) logs actions without writing anything
"""

from __future__ import annotations

import os
import urllib.parse

from sync_issue_to_youtrack import (  # reuse the live logic
    GitHub,
    YouTrack,
    _request,
    build_custom_fields,
    build_description,
    env,
)


def list_issues(gh: GitHub, state: str) -> list[dict]:
    """Return all issues (excluding pull requests) for the repo, paginated."""
    issues: list[dict] = []
    page = 1
    while True:
        query = urllib.parse.urlencode(
            {"state": state, "per_page": 100, "page": page, "sort": "created", "direction": "asc"}
        )
        url = f"{gh.api}/repos/{gh.repo}/issues?{query}"
        batch = _request("GET", url, gh.headers) or []
        if not batch:
            break
        # The issues endpoint also returns PRs; drop anything with a pull_request key.
        issues.extend(item for item in batch if "pull_request" not in item)
        page += 1
    return issues


def main() -> None:
    repo = env("GITHUB_REPOSITORY")
    state = os.environ.get("BACKFILL_STATE", "open").strip().lower() or "open"
    dry_run = os.environ.get("BACKFILL_DRY_RUN", "true").strip().lower() != "false"

    if state not in ("open", "all"):
        state = "open"

    gh = GitHub(env("GITHUB_TOKEN"), repo)
    # YouTrack config is only needed for real writes; a dry run must be able to
    # preview using GITHUB_TOKEN alone.
    yt = None
    project_key = tag_name = None
    if not dry_run:
        yt = YouTrack(env("YOUTRACK_URL"), env("YOUTRACK_TOKEN"))
        project_key = env("YOUTRACK_PROJECT")
        tag_name = env("YOUTRACK_TAG", required=False)

    mode = "DRY RUN (no writes)" if dry_run else "LIVE (creating issues)"
    print(f"Backfill starting — repo={repo} state={state} — {mode}")

    issues = list_issues(gh, state)
    print(f"Found {len(issues)} issue(s) to consider.\n")

    project_id = None  # resolved lazily, only when a real create is needed
    created, skipped, would_create = 0, 0, 0

    for issue in issues:
        number = issue.get("number")
        title = issue.get("title") or f"GitHub issue #{number}"
        existing_id = gh.find_marker(number)

        if existing_id:
            # Already mirrored: don't recreate, but (re)apply the tag so a re-run
            # can backfill tags onto issues created before the tag existed.
            if not dry_run and tag_name:
                yt.apply_tag(existing_id, tag_name)
            print(f"  #{number}  SKIP  already mirrored as {existing_id}  — {title}")
            skipped += 1
            continue

        if dry_run:
            print(f"  #{number}  WOULD MIRROR  — {title}")
            would_create += 1
            continue

        if project_id is None:
            project_id = yt.resolve_project_id(project_key)

        summary = f"[GitHub #{number}] {title}"
        description = build_description(issue, repo)
        result = yt.create_issue(project_id, summary, description, build_custom_fields())
        youtrack_id = result["idReadable"]
        if tag_name:
            yt.apply_tag(youtrack_id, tag_name)
        youtrack_url = f"{yt.base}/issue/{youtrack_id}"
        gh.post_marker(number, youtrack_id, youtrack_url)
        print(f"  #{number}  CREATED  {youtrack_id}  — {title}")
        created += 1

    print("\nBackfill summary:")
    print(f"  already mirrored (skipped): {skipped}")
    if dry_run:
        print(f"  would mirror:               {would_create}")
        print("\nDry run only — nothing was written. Re-run with dry_run=false to apply.")
    else:
        print(f"  created:                    {created}")


if __name__ == "__main__":
    main()
