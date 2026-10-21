"""Merge `main` into a pull request whose only conflict is the worklog (#206).

Every pull request adds an entry at the top of `docs/ai/worklog.md`, so two open pull requests conflict there as soon as one
merges. The conflict carries no information: both sides add a new, independent entry and the resolution is always "keep both".
`.github/workflows/worklog-conflicts.yml` runs this script in three steps:

- ``find``   lists the open same-repository pull requests into the default branch that GitHub reports as conflicting.
- ``merge``  merges the default branch into one of them in a scratch checkout. It acts only when the worklog is the sole
             conflicting file and both sides only *add* lines to it; it then keeps both sides (the pull request's entry first,
             because it merges last), commits, and with ``--verify`` runs the validation and the tests on the merged tree.
             This step runs the pull request's code, so the workflow gives it no secrets.
- ``push``   is the same merge without ``--verify``, run from the default branch's copy of this script: it checks the tree
             equals the one the ``merge`` step verified, and the workflow then pushes it (not forced) as the ADIRO Bot.

Any other conflict, a worklog edit that is not a pure addition, or a failing check is left to the author.
Standard library only, so the workflow runs it with the runner's ``python3``.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
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

def only_adds(repo: Path, base: str, side: str) -> bool:
    """True when `side` changes the worklog by adding lines only (no line removed or rewritten) since `base`."""
    out = git(repo, "diff", "--numstat", base, side, "--", WORKLOG).stdout.split()
    return not out or out[1] == "0"


MARKER = 31  # longer than any line of `=` or `<` the worklog itself might contain


def keep_both(merged: str) -> str:
    """Resolve each conflict block of `merged` to both sides, ours first, with a blank line between them.

    `git merge-file --union` would do the same, but both entries end in a blank line that diff treats as shared, so the
    union runs the two entries together; a blank line is added where one side does not end in one.
    """
    out, ours, theirs, side = [], [], [], None
    for line in merged.splitlines(keepends=True):
        if line.startswith("<" * MARKER):
            side = ours
        elif line.startswith("=" * MARKER) and side is ours:
            side = theirs
        elif line.startswith(">" * MARKER) and side is theirs:
            gap = ["\n"] if ours and theirs and ours[-1].strip() else []
            out += ours + gap + theirs
            ours, theirs, side = [], [], None
        elif side is not None:
            side.append(line)
        else:
            out.append(line)
    return "".join(out)


def union(repo: Path) -> str:
    """The worklog with both sides of every conflict kept, the pull request's side (ours) first."""
    with tempfile.TemporaryDirectory() as tmp:
        paths = []
        for stage, name in ((2, "ours"), (1, "base"), (3, "theirs")):
            path = Path(tmp) / name
            path.write_bytes(subprocess.run(["git", "-C", str(repo), "show", f":{stage}:{WORKLOG}"],
                                            capture_output=True, check=True).stdout)
            paths.append(str(path))
        merged = subprocess.run(["git", "merge-file", "-p", f"--marker-size={MARKER}", *paths],
                                capture_output=True, text=True, encoding="utf-8").stdout
        return keep_both(merged)


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
    if not (only_adds(repo, fork_point, head_sha) and only_adds(repo, fork_point, base_sha)):
        git(repo, "merge", "--abort", check=False)
        return {**result, "status": EDITED}

    (repo / WORKLOG).write_text(union(repo), encoding="utf-8", newline="")
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
    # push: redo the merge without running anything from the pull request, and accept it only if it is the verified tree.
    verified = json.loads(args.out.read_text(encoding="utf-8")) if args.out.exists() else {}
    if verified.get("status") != READY:
        print(f"Not pushing: the verified status is {verified.get('status', 'missing')}.")
        return 1
    status = merge(args.repo, args.head, args.base, args.branch)
    if status["status"] != READY or status.get("tree") != verified.get("tree") or status["head_sha"] != verified.get("head_sha"):
        print(f"Not pushing: the merge here ({status}) is not the one that was verified ({verified}).")
        return 1
    print(f"Ready to push {status['merge_sha']} onto {args.branch}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
