---
name: deploy
description: >-
  How ADIRO builds & publishes its ontology docs (MkDocs -> GitHub Pages) and runs its
  validation and YouTrack-sync CI. Read when editing ontologies, docs, or CI, or cutting a version.
---

# ADIRO — docs build, validation & publishing

**The authority for this is the root [`AGENTS.md`](../../../AGENTS.md) — read it.** That file is tool-neutral
(shared with Cursor and humans); this skill is just the Claude Code trigger for it.

In brief: a Material-for-MkDocs site is generated from `src/*.ttl` by `scripts/generate_docs.py` (pyLODE HTML
+ `ttl2md` Markdown) and deployed to GitHub Pages by `.github/workflows/generate-deploy-docs.yml`. PRs run
`validate-ontology.yml` (`scripts/validate_ontology.py`); GitHub issues mirror to YouTrack RES via
`sync-issues-to-youtrack.yml`. Versioning is per-module SemVer — **TBox `.ttl` edits are on hold pending
RES-27** (KB https://bhmlrnd.youtrack.cloud/articles/DATA-A-10). Full workflow names, commands, gotchas, and
the mandatory keep-in-sync rules are in `AGENTS.md`.

**Keep in sync:** if you change CI/docs/versioning, update `AGENTS.md` in the same PR. CI wins on conflicts.

## Related
- KB: DATA-A-10 (ADIRO versioning), MAN-A-13 (team KB).
- Shared: the `orientation` skill and `tools:youtrack`.
