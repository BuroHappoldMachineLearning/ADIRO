"""Merge `main` into a pull request whose only conflict is the worklog (#206).

Every pull request adds an entry at the top of `docs/ai/worklog.md`, so two open pull requests conflict there as soon as one
merges. The conflict carries no information: both sides add a new, independent entry and the resolution is always "keep both".
`.github/workflows/worklog-conflicts.yml` runs this script in three steps:

- ``find``   lists the open same-repository pull requests into the default branch that GitHub reports as conflicting.
- ``merge``  merges the default branch into one of them in a scratch checkout. It acts only when the worklog is the sole
             conflicting file and both sides only *add* lines to it; it then keeps both sides (the pull request's entry first,
             because it merges last), commits, and with ``--verify`` runs the validation and the tests on the merged tree.
             This step runs the pull request's code, so the workflow gives it no secrets.
- ``push``   is the same merge without ``--verify``, run from the default branch's copy of this script, with the default
             branch's commit that the ``merge`` step merged (#224: the docs deploy commits to the default branch about a minute
             after every merge, usually between the two steps, so merging the branch's tip by then gives a tree that was never
             verified). That commit comes from the ``merge`` step, which runs the pull request's code, so it is accepted only if
             it is a commit of the default branch. The step checks the tree equals the verified one, and the workflow then
             pushes it as the ADIRO Bot, leased on the head ``find`` saw, so a branch that moved meanwhile is left alone. A
             default branch that moved on is merged by the next run.

Any other conflict, a worklog edit that is not a pure addition, or a failing check is left to the author.
Standard library only, so the workflow runs it with the runner's ``python3``.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

WORKLOG = "docs/ai/worklog.md"
BOT_NAME = "adiro-bot[bot]"
BOT_EMAIL = "340218862+adiro-bot[bot]@users.noreply.github.com"

# The checks `validate-ontology.yml` runs on every pull request; tests/test_worklog_conflicts.py keeps the two in step.
VERIFY = [
    ("dependencies", ["uv", "sync", "--python", "3.12", "--no-install-project"]),
    ("validation", ["uv", "run", "--python", "3.12", "--no-project", "python", "scripts/validate_ontology.py"]),
    ("tests", ["uv", "run", "--python", "3.12", "--no-project", "--with", "pytest", "--with", "pillow", "--with", "rdflib",
               "--with", "pyshacl", "--with", "pylode==3.2.3", "python", "-m", "pytest", "tests", "-q"]),
]

# Statuses of `merge`: only "ready" is pushed.
READY, CLEAN, OTHER, EDITED, FAILED = "ready", "clean", "other-conflicts", "worklog-edited", "verify-failed"

# Why a pull request is not pushed, for the run summary (#224: a run that pushes nothing must say why).
REASONS = {
    CLEAN: "it no longer conflicts with the default branch",
    OTHER: "it conflicts in other files than the worklog; left to its author",
    EDITED: "its worklog change is not a pure addition; left to its author",
    FAILED: "a check fails on the merged tree; the comment on the pull request says which",
}
SHA_RE = re.compile(r"[0-9a-f]{40}")


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8", check=check)


# --- find -----------------------------------------------------------------------------------------------------------

PR_FIELDS = "number,headRefName,headRefOid,baseRefName,isCrossRepository,mergeable"


def gh_json(*args: str):
    out = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8", check=True).stdout
    return json.loads(out)


def list_prs(base: str, number: int | None, gh=gh_json, sleep=time.sleep, attempts: int = 10) -> list[dict]:
    """The open pull requests into `base` (or just `number`), polled until GitHub has computed `mergeable` for each."""
    if number is None:
        prs = gh("pr", "list", "--state", "open", "--base", base, "--limit", "200", "--json", PR_FIELDS)
    else:
        pr = gh("pr", "view", str(number), "--json", PR_FIELDS + ",state")
        prs = [pr] if pr.get("state") == "OPEN" and pr["baseRefName"] == base else []
    for _ in range(attempts):
        unknown = [p for p in prs if p["mergeable"] == "UNKNOWN"]
        if not unknown:
            break
        sleep(6)  # GitHub computes `mergeable` lazily; asking again starts the computation
        for p in unknown:
            p["mergeable"] = gh("pr", "view", str(p["number"]), "--json", "mergeable")["mergeable"]
    return prs


def candidates(prs: list[dict]) -> tuple[list[dict], list[int]]:
    """The conflicting same-repository pull requests, and the conflicting fork ones (the bot cannot push to a fork)."""
    conflicting = [p for p in prs if p["mergeable"] == "CONFLICTING"]
    picked = [{"number": p["number"], "branch": p["headRefName"], "head_sha": p["headRefOid"]}
              for p in conflicting if not p["isCrossRepository"]]
    forks = [p["number"] for p in conflicting if p["isCrossRepository"]]
    return picked, forks


# --- merge ----------------------------------------------------------------------------------------------------------

HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", re.M)


def show(repo: Path, rev: str) -> list[str]:
    return git(repo, "show", f"{rev}:{WORKLOG}").stdout.splitlines(keepends=True)


def insertions(repo: Path, base: str, side: str) -> dict[int, list[str]] | None:
    """The lines `side` adds to the worklog since `base`, keyed by the base line they follow (0 = the top).

    None when `side` also removes or rewrites a line: then it is not a pure addition and the bot leaves it alone.
    """
    diff = git(repo, "diff", "--no-ext-diff", "--no-color", "-U0", base, side, "--", WORKLOG).stdout
    lines = show(repo, side)
    added = {}
    for old_start, old_count, new_start, new_count in HUNK.findall(diff):
        if old_count != "0":
            return None
        start, count = int(new_start), int(new_count or 1)
        added[int(old_start)] = lines[start - 1:start - 1 + count]
    return added


def keep_both(base: list[str], ours: dict[int, list[str]], theirs: dict[int, list[str]]) -> str:
    """The base worklog with both sides' additions, ours (the pull request's) first where both add at the same point.

    Built from the two sides' insertions rather than from `git merge-file`, which treats a line that ends both new entries
    (a blank line, or the same closing sentence) as shared and keeps it once, under the second entry.
    """
    out = []
    for i in range(len(base) + 1):
        a, b = ours.get(i, []), theirs.get(i, [])
        gap = ["\n"] if a and b and a[-1].strip() else []
        out += a + gap + b
        if i < len(base):
            out.append(base[i])
    return "".join(out)


def merge(repo: Path, head: str, base: str, branch: str, verify=None, runner=subprocess.run) -> dict:
    """Merge `base` into `head` (a commit of the pull request `branch`), resolving a worklog-only conflict.

    Leaves `repo` at the merge commit when the status is "ready", and at `head` otherwise.
    """
    head_sha = git(repo, "rev-parse", head).stdout.strip()
    base_sha = git(repo, "rev-parse", base).stdout.strip()
    result = {"head_sha": head_sha, "base_sha": base_sha}
    git(repo, "checkout", "--quiet", "--detach", head_sha)
    merged = git(repo, "-c", f"user.name={BOT_NAME}", "-c", f"user.email={BOT_EMAIL}",
                 "merge", "--no-ff", "--no-commit", base_sha, check=False)
    conflicts = git(repo, "diff", "--name-only", "--diff-filter=U").stdout.split()
    if merged.returncode == 0 and not conflicts:
        git(repo, "merge", "--abort", check=False)
        return {**result, "status": CLEAN}
    if conflicts != [WORKLOG]:
        git(repo, "merge", "--abort", check=False)
        return {**result, "status": OTHER, "files": conflicts}
    fork_point = git(repo, "merge-base", head_sha, base_sha).stdout.strip()
    ours, theirs = insertions(repo, fork_point, head_sha), insertions(repo, fork_point, base_sha)
    if ours is None or theirs is None:
        git(repo, "merge", "--abort", check=False)
        return {**result, "status": EDITED}

    (repo / WORKLOG).write_text(keep_both(show(repo, fork_point), ours, theirs), encoding="utf-8", newline="")
    git(repo, "add", WORKLOG)
    message = (f"Merge main into {branch}: keep both worklog entries\n\n"
               f"The only conflict was {WORKLOG}, where both sides add an entry, so both are kept (#206).")
    git(repo, "-c", f"user.name={BOT_NAME}", "-c", f"user.email={BOT_EMAIL}", "commit", "--quiet", "-m", message)
    result["merge_sha"] = git(repo, "rev-parse", "HEAD").stdout.strip()
    result["tree"] = git(repo, "rev-parse", "HEAD^{tree}").stdout.strip()

    for name, command in verify or []:
        run = runner(command, cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if run.returncode != 0:
            print((run.stdout or "")[-4000:] + (run.stderr or "")[-4000:], file=sys.stderr)
            git(repo, "checkout", "--quiet", "--detach", head_sha)
            return {**result, "status": FAILED, "failed": name}
    return {**result, "status": READY}


# --- comment --------------------------------------------------------------------------------------------------------

def comment(status: dict, run_url: str) -> str:
    """The sticky comment for a pull request the bot could not update, or "" (which removes the comment)."""
    if status.get("status") != FAILED:
        return ""
    check = status.get("failed") if status.get("failed") in dict(VERIFY) else "a check"
    return (f"This pull request conflicts with `main` only in `{WORKLOG}`, and the ADIRO Bot can keep both entries, but on the "
            f"merged result **{check}** fails ([run]({run_url})), so it did not push the merge. Something on `main` breaks this "
            f"pull request: merge `main` into the branch, fix what fails, and push. See "
            f"[#206](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/206).")


# --- command line ---------------------------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("find", help="print the pull requests to try, as JSON")
    f.add_argument("--base", default="main")
    f.add_argument("--pr", type=int)
    for name in ("merge", "push"):
        m = sub.add_parser(name)
        m.add_argument("--repo", type=Path, default=Path("."))
        m.add_argument("--head", required=True, help="the pull request's head commit")
        m.add_argument("--base", required=True, help="the default branch, e.g. origin/main")
        m.add_argument("--branch", required=True)
        m.add_argument("--out", type=Path, required=True, help="the status file to write (merge) or read (push)")
    c = sub.add_parser("comment", help="print the sticky comment for a status file")
    c.add_argument("status", type=Path)
    c.add_argument("--run-url", required=True)
    args = parser.parse_args(argv)

    if args.cmd == "find":
        picked, forks = candidates(list_prs(args.base, args.pr))
        for number in forks:
            print(f"#{number} is a fork pull request: the bot cannot push to it, left to its author.", file=sys.stderr)
        print(json.dumps(picked))
        return 0
    if args.cmd == "comment":
        status = json.loads(args.status.read_text(encoding="utf-8")) if args.status.exists() else {}
        print(comment(status, args.run_url))
        return 0
    if args.cmd == "merge":
        status = merge(args.repo, args.head, args.base, args.branch, verify=VERIFY)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(status), encoding="utf-8")
        print(json.dumps(status))
        return 0
    return push(args.repo, args.head, args.base, args.branch, args.out)


def push(repo: Path, head: str, base: str, branch: str, out: Path) -> int:
    """Redo the verified merge without running anything from the pull request; 0 if it is the verified tree.

    The merge uses the default branch's commit the `merge` step merged, not `base`'s tip, which may have moved since (#224).
    The status file was written by a job that runs the pull request's code, so its commit is accepted only if it is a
    commit of `base`: the pushed merge then holds only the pull request and the default branch's own history.
    """
    verified = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {}
    state = verified.get("status")
    if state != READY:
        print(f"Not pushing: {REASONS.get(state, 'the merge step left no result (it failed or did not run)')}.")
        return 1
    base_sha = str(verified.get("base_sha", ""))
    if not SHA_RE.fullmatch(base_sha) or git(repo, "merge-base", "--is-ancestor", base_sha, base, check=False).returncode != 0:
        print(f"Not pushing: the verified merge names {base_sha or 'no commit'} as the default branch, which is not a commit of {base}.")
        return 1
    status = merge(repo, head, base_sha, branch)
    if status["status"] != READY or status.get("tree") != verified.get("tree") or status["head_sha"] != verified.get("head_sha"):
        print(f"Not pushing: the merge here ({status}) is not the one that was verified ({verified}).")
        return 1
    moved = git(repo, "rev-parse", base).stdout.strip() != base_sha
    print(f"Ready to push {status['merge_sha']} onto {branch}, with the default branch at {base_sha[:7]}"
          + (" (it has moved on since; the next run merges the rest)." if moved else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
