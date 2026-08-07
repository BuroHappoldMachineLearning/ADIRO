# AGENTS.md — ADIRO

Shared, **tool-agnostic** working guide for AI assistants (Claude Code, Cursor, and any other agent) and
humans. This is the **single source of truth** for how to work in this repo; each tool's native entry file
points here instead of restating it:
- **Claude Code** → `CLAUDE.md` imports this file; the `deploy` skill (`.claude/skills/deploy/`) points here.
- **Cursor** → `.cursor/rules/general.mdc` references this file and adds only Cursor-specific rules.

Keep this in sync with the code: if a convention here changes, change it **here** and let the adapters
inherit it. On any conflict between this file and the CI/build files (`.github/workflows/`, `mkdocs.yml`,
`pyproject.toml`, `scripts/`), **the CI/build files win — fix this file.**

## Purpose
ADIRO (*AEC Drawing Information Representation Ontologies*) is a bundle of OWL/TTL ontologies for AEC
(Architecture, Engineering & Construction) drawing representation, built to support machine-learning tasks —
in particular information-extraction workflows. It defines concepts for drawing metadata, common symbols,
domain-common symbols, and domain-specific symbols so AEC drawings can be made machine-readable and drive
graph databases / knowledge graphs.

Ontology sources live in `src/` as four independently versioned modules (dependency order):
1. `aec_drawing_metadata` — sheet/layout/document structure (titleblock, legend, revision table, drawing types…).
2. `aec_common_symbols` — cross-discipline reusable symbols (dimensions, callouts, grids, levels…).
3. `aec_domain_common` — concepts shared across a set of domains.
4. `aec_facade_domain` — facade-engineering discipline-specific concepts (`:FacadeComponent`, `:DGU`, …).

## Stack
- **Python** (3.10–3.13; CI runs 3.12), managed with **uv** (single root `pyproject.toml`).
- **pyLODE** (`pylode==3.2.3`), **rdflib** (`>=6.0.0`), **Material for MkDocs** (`mkdocs-material>=9.5.0`).
- In-repo **`ttl2md/`** package (separate `src/` tree + own tests) renders native Markdown from the TTL.
- **pytest** for tests.

## Docs build & publish
Material-for-MkDocs static site → GitHub Pages at **https://burohappoldmachinelearning.github.io/ADIRO/**.

- **Deploy workflow:** `.github/workflows/generate-deploy-docs.yml`. Triggers on push to `main`/`master` and
  manual `workflow_dispatch`. Jobs: `validate` + `test-ttl2md` + `test-docs` → `generate-docs` → `deploy`.
- **Doc generation:** `scripts/generate_docs.py` reads every `src/*.ttl`, emits a pyLODE HTML reference page
  per ontology, emits native Markdown pages (via `ttl2md/`) into `docs/ontologies/`, copies the `.ttl` and
  `*.display.json` sources into `docs/`, and regenerates the MkDocs landing page `docs/index.md` (including
  the auto-discovered ontology list). It hard-codes a dependency sort order for the modules. CI commits the
  regenerated `docs/` back, then runs `mkdocs build` (output `site/`, git-ignored) and deploys the artifact.
- **Local preview (uses `uv`):**
  ```bash
  uv sync                                    # install deps (once)
  uv run python scripts/generate_docs.py     # regenerate ontology pages + docs/index.md
  uv run mkdocs serve                         # live preview at http://127.0.0.1:8000/ADIRO/
  # or: uv run mkdocs build                   # produce the static site into site/
  ```
- `docs/brainstorming/`, `docs/modularization/`, and `docs/governance/` are excluded from the built site
  (`exclude_docs` in `mkdocs.yml`) — verify before assuming a docs page publishes.

## Validation & YouTrack-sync CI
- **`.github/workflows/validate-ontology.yml`** — on PRs to any branch; runs `scripts/validate_ontology.py`
  over `src/*.ttl` (parse check, circular-subclass detection, ensures an `owl:Ontology` declaration, and
  per-module version consistency — `owl:versionInfo` == `owl:versionIRI` tail == ontology IRI + version), plus
  `scripts/compat_diff.py` (RES-67, *warn* mode) which flags when a module's declared SemVer bump is smaller
  than its change requires. The same validate step gates the deploy workflow. **After any `.ttl` edit, validate immediately:**
  `uv run python scripts/validate_ontology.py src/<file>.ttl` (or with no arg to validate all of `src/`).
  Never skip it — a missing period or malformed RDF fails parsing and must be caught at once.
- **`.github/workflows/sync-issues-to-youtrack.yml`** — one-way mirror of GitHub issue events → YouTrack
  **RES** project via `scripts/sync_issue_to_youtrack.py` (inbox model; YouTrack is never pushed back).
- **`.github/workflows/backfill-issues-to-youtrack.yml`** — manual one-shot backfill (`dry_run` defaults
  true), idempotent via a youtrack-id marker comment (`scripts/backfill_issues_to_youtrack.py`).
- **No secrets in this repo:** YouTrack sync reads `secrets.YOUTRACK_URL` / `secrets.YOUTRACK_TOKEN` plus
  `vars.*` from repo settings.

## Versioning
**Per-module SemVer** — each `src/*.ttl` is versioned independently via its own `owl:versionIRI` +
`owl:versionInfo` (currently `aec_drawing_metadata` 2.0.0; the other three 1.0.0). The full scheme — IRI
strategy, bump rules (compatibility-diff spec), imports policy, deprecation, the tag-driven release flow, and
changelogs — is in **`docs/contribute/versioning.md`**; rationale in KB
[DATA-A-10](https://bhmlrnd.youtrack.cloud/articles/DATA-A-10); plan/decisions in
[RES-27](https://bhmlrnd.youtrack.cloud/issue/RES-27).
- **Releases are per-module:** tag `<module>-v<semver>` (e.g. `aec_common_symbols-v1.2.0`) →
  `.github/workflows/backup-version.yml` snapshots that module to `versions/<module>/<semver>/`, and the deploy
  workflow serves it at `…/ADIRO/<module>/<semver>/<module>.ttl` (alongside the latest `…/ADIRO/<module>.ttl`).
- **Changelogs:** per-module `changelogs/<module>.md` (source of truth, `[Unreleased]` section) + a top-level
  `CHANGELOG.md` rollup. Bump `owl:versionInfo` / `owl:versionIRI` **only at a release cut**, not per edit.
- **CI enforces per-module version consistency** (`scripts/validate_ontology.py`, [RES-66](https://bhmlrnd.youtrack.cloud/issue/RES-66)).
- **TBox `.ttl` edits:** the scheme is agreed ([RES-27](https://bhmlrnd.youtrack.cloud/issue/RES-27)) and the repo now has the Phase-0 docs + version-consistency
  CI, so **additive TBox edits may resume** — record them under the module's `[Unreleased]` changelog; the next
  release cut performs the bump. *(Supersedes the earlier "hold pending ratification".)*

## Keep in sync (mandatory)
- **Ontology ↔ docs.** The published docs are generated from `src/*.ttl`. Whenever a `.ttl` changes, regenerate
  the docs in the same change: `uv run python scripts/generate_docs.py`,
  and let `generate-deploy-docs.yml` publish. Do not hand-edit generated pages in `docs/` — they are overwritten.
- **Versioning.** Record any change to a module's semantics under that module's `changelogs/<module>.md`
  `[Unreleased]` section; bump its `owl:versionIRI` / `owl:versionInfo` **only at a release cut** (tag
  `<module>-v<semver>`), per `docs/contribute/versioning.md`.
- **Downstream label consumers (CVAT).** The metadata module defines the `isCVATProperty` annotation, and
  domain modules mark labellable classes with it, so the ontology **drives CVAT annotation labels**. Changes
  to labellable classes or `isCVATProperty` usage affect those consumers — coordinate via DATA-A-9
  (https://bhmlrnd.youtrack.cloud/articles/DATA-A-9). *(verify: exact DATA-A-9 scope / article slug.)*
- **This file ↔ CI.** If you change CI, docs generation, or versioning, update the relevant section here in
  the same PR. CI wins on conflicts.

## Team workflow
Issue-first: propose additions/changes as an issue before coding (GitHub issues mirror into YouTrack RES).
Team knowledge base: **https://bhmlrnd.youtrack.cloud/articles/MAN-A-13**.
