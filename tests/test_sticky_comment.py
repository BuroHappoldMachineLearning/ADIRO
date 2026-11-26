"""The comment-size guard of .github/actions/sticky-comment (#296): a report over GitHub's limit is cut, not rejected."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ACTION = Path(__file__).resolve().parent.parent / ".github" / "actions" / "sticky-comment" / "action.yml"
GITHUB_LIMIT = 65536

# Runs the guard's block of the action's script on `report` with a stub `core`, and prints what is left of it.
RUN = r"""
const fs = require('fs');
const src = fs.readFileSync(process.argv[1], 'utf8');
const block = src.slice(src.indexOf('const LIMIT'), src.indexOf('core.warning(`The report was')) + '}';
const core = { summary: { addRaw() { return { write: async () => {} }; } }, warning: () => {} };
const run = new Function('core', 'report', 'return (async () => {' + block + '; return report; })();');
run(core, fs.readFileSync(process.argv[2], 'utf8')).then((out) => process.stdout.write(JSON.stringify(out)));
"""


def guard(tmp_path, report):
    if shutil.which("node") is None:
        pytest.skip("node is not installed")
    path = tmp_path / "report.md"
    path.write_text(report, encoding="utf-8", newline="")
    run = subprocess.run(["node", "-e", RUN, str(ACTION), str(path)], capture_output=True, text=True, encoding="utf-8", check=True)
    return json.loads(run.stdout)


def test_a_long_report_is_cut_at_a_line_with_its_details_closed(tmp_path):
    lines = [f"- line {i} " + "y" * 20 for i in range(3000)]
    report = "<details><summary>x</summary>\n\n" + "\n".join(lines) + "\n\n</details>"
    out = guard(tmp_path, report)
    assert len(out) < GITHUB_LIMIT - 1000, "room for the marker and the footer"
    assert out.count("<details>") == out.count("</details>") == 1
    kept = out.split("\n\n</details>")[0].splitlines()[-1]
    assert kept in lines, "cut at a line, not inside one"
    assert "**Cut short:**" in out and "/actions/runs/" not in out, "a run link in the text would repost the comment on every run"


def test_a_report_under_the_limit_is_unchanged(tmp_path):
    report = "<details><summary>x</summary>\n\n- one\n\n</details>"
    assert guard(tmp_path, report) == report
