"""The tool-specific entry files must stay thin: they import AGENTS.md instead of restating it.

A summary copied into CLAUDE.md or a Cursor rule goes stale the first time AGENTS.md changes (the Cursor rule once
kept saying TBox edits were on hold two days after AGENTS.md lifted the hold). So these files are an import plus a
sentence, and a rule that needs more belongs in AGENTS.md.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CURSOR_RULES = sorted((ROOT / ".cursor" / "rules").glob("*.mdc"))
MAX_ADAPTER_LINES = 25


def test_claude_md_and_every_cursor_rule_import_agents_md():
    assert "@AGENTS.md" in (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert CURSOR_RULES, "expected at least one Cursor rule"
    for path in CURSOR_RULES:
        assert "@AGENTS.md" in path.read_text(encoding="utf-8"), (
            f"{path.relative_to(ROOT)} must import AGENTS.md, not carry its own conventions")


def test_adapter_files_stay_thin():
    for path in [ROOT / "CLAUDE.md", *CURSOR_RULES]:
        lines = path.read_text(encoding="utf-8").splitlines()
        assert len(lines) <= MAX_ADAPTER_LINES, (
            f"{path.relative_to(ROOT)} has {len(lines)} lines (max {MAX_ADAPTER_LINES}): "
            "put the content in AGENTS.md and link to it instead of restating it here")
