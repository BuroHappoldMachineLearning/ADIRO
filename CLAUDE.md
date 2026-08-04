# CLAUDE.md — ADIRO

The shared, tool-agnostic conventions for this repo are in `AGENTS.md` (imported below). Follow them.

@AGENTS.md

## Claude Code specifics
- **Docs build / validation / publishing:** the `deploy` skill (`.claude/skills/deploy/`) is the entry point;
  its authority is `AGENTS.md`.
- **One source of truth:** `AGENTS.md` is canonical — Cursor (`.cursor/rules/general.mdc`) and this file both
  point at it. If a convention changes, change it in `AGENTS.md`, not in a per-tool file.
- **Team workflow:** issue-first — see the `orientation` skill and `tools:youtrack`. KB
  https://bhmlrnd.youtrack.cloud/articles/MAN-A-13.
