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
- `docs/brainstorming/`, `docs/modularization/`, and `docs/ai/` are excluded from the built site
  (`exclude_docs` in `mkdocs.yml`) — verify before assuming a docs page publishes.

## Validation & YouTrack-sync CI
- **`.github/workflows/validate-ontology.yml`** — on PRs to any branch; runs `scripts/validate_ontology.py`
  over `src/*.ttl` (parse check, circular-subclass detection, ensures an `owl:Ontology` declaration, and
  per-module version consistency — `owl:versionInfo` == `owl:versionIRI` tail == ontology IRI + version), plus
  `scripts/compat_diff.py` (RES-67, *warn* mode) which flags when a module's declared SemVer bump is smaller
  than its change requires. The same validate step gates the deploy workflow.
- **`.github/workflows/compat-diff-comment.yml`** — on PRs touching `src/**.ttl` (RES-67), posts a sticky
  comment with each changed module's **prospective next version** (`compat_diff.py --markdown`). Report-only;
  the gate is the warn step above.
- **`.github/workflows/ontology-reasoning.yml`** — on PRs touching `src/**.ttl` (RES-36), runs an OWL 2 DL
  reasoner (**HermiT**) + ROBOT `report` over the whole suite at latest and posts a sticky comment. The
  **reasoner is a blocking gate** — a PR that makes the merged suite inconsistent / unsatisfiable / non-DL
  fails the check; ROBOT `report` stays **advisory** (warn-only). It calls `scripts/run_reasoning.sh` — the
  *same* script you run locally (below) — so CI and local match. Imports resolve offline via `src/catalog-v001.xml`.

**After any `.ttl` edit, validate immediately:**
`uv run python scripts/validate_ontology.py src/<file>.ttl` (or with no arg to validate all of `src/`).
Never skip it — a missing period or malformed RDF fails parsing and must be caught at once.

### Local ontology reasoning / QC (ROBOT)
The reasoning CI and humans run the **same** script — `scripts/run_reasoning.sh` — so a local run reproduces
CI exactly (handy when an LLM/agent is iterating). It merges `src/*.ttl` at latest, runs HermiT for
**consistency + unsatisfiable-class** detection, then ROBOT `report`. ROBOT is fetched automatically to
`.tools/robot.jar` (git-ignored) on first run; outputs land in `.tools/reasoning-out/`.

Prerequisite — a **Java 11+ runtime (JRE or JDK)** on `PATH` (OWL DL reasoners + ROBOT are JVM tools; there is
no pure-Python equivalent for DL consistency/unsat). Install once, then open a new terminal:
- **Windows (org standard):** `winget install EclipseAdoptium.Temurin.17.JDK`
- **Linux (Debian/Ubuntu):** `sudo apt-get install -y openjdk-17-jre` — distro-agnostic alternative:
  SDKMAN (`curl -s https://get.sdkman.io | bash` → `sdk install java 17.0.20-tem`)
- **macOS:** `brew install temurin@17`

Run: `bash scripts/run_reasoning.sh` (warn mode, always exits 0). `ENFORCE=1 bash scripts/run_reasoning.sh`
exits non-zero on inconsistency/unsatisfiable classes. Override defaults with `REASONER=` / `ROBOT_VERSION=`
/ `ROBOT_JAR=`.

**Shell:** the script is bash. On **Windows** run it in **Git Bash** (ships with Git for Windows) — **WSL is
not required** (it drives the native Windows `java.exe` fine; MSYS2 and WSL also work). Pure-PowerShell users
who won't use bash can instead run the two underlying `java -jar robot.jar merge … reason …` / `… report …`
commands directly, but Git Bash is simpler.
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

## Ontology authoring conventions
- **`rdfs:label` is the human-readable name.** Give every class a clear label that **contains** the class's
  PascalCase local name split into words (Title Case) — `:UnitisedCurtainWall` → `"Unitised Curtain Wall"` —
  but the label *is* a human name, so it may **expand acronyms** (`:DGU` → `"Double Glazing Unit"`) or add a
  qualifier; keep the short form as `skos:altLabel` (`:DGU skos:altLabel "DGU"`). Object/data **properties**
  keep their lowerCamelCase name as the label.
- **Exactly one `rdfs:label` per term, in English.** ROBOT `report` raises **`multiple_labels` as an
  ERROR** for any term with more than one, so multilingual naming goes in `skos:altLabel`, not in a second
  `rdfs:label`. German and abbreviated drawing captions therefore live in `skos:altLabel` — which is also
  where extraction tooling looks for them.
- **Keep labels unique across classes** — but note this is a **docs-quality convention, *not* an RDF/OWL
  requirement** (RDF is fine with duplicate labels; the IRI is the identifier). We enforce it because the
  published docs (pyLODE / ttl2md) and label-based search display `rdfs:label`, so duplicates confuse a human
  reader — and because for `owl:oneOf` **enumeration values** the `rdfs:label` *is* the CVAT SELECT option a
  person picks. Enforced by ROBOT `report` `duplicate_label` ([RES-36](https://bhmlrnd.youtrack.cloud/issue/RES-36)),
  as a **warning** (exceptions allowed). Legacy-label conformance is tracked in
  [RES-92](https://bhmlrnd.youtrack.cloud/issue/RES-92).
- **CVAT label text comes from the URI, not `rdfs:label`.** The pipeline builds each CVAT *class* label from the
  class **IRI local name** (fragment after `#`) and normalizes it via its own `name_normalizer_rules`; it does
  **not** read the class's `rdfs:label`. `rdfs:label` reaches CVAT only for `owl:oneOf` enumeration values
  (SELECT options). So class identity in CVAT is guaranteed by the (unique) IRI — `rdfs:label` uniqueness is for
  humans/docs, not CVAT. Verified against the pipeline; see KB
  [DATA-A-9](https://bhmlrnd.youtrack.cloud/articles/DATA-A-9).

## Keep in sync (mandatory)
- **Worklog.** Record any non-trivial change you make in **`docs/ai/worklog.md`** (newest entry first) — what
  changed, how it was verified (including gates you could *not* run), decisions deferred or rejected, and the
  next step. It is the handover record between sessions; `git log` does not carry intent or open threads. Excluded
  from the built site (`exclude_docs`).
- **Ontology ↔ docs.** The published docs are generated from `src/*.ttl`. Whenever a `.ttl` changes, regenerate
  the docs in the same change: `uv run python scripts/generate_docs.py`,
  and let `generate-deploy-docs.yml` publish. Do not hand-edit generated pages in `docs/` — they are overwritten.
- **Versioning.** Record any change to a module's semantics under that module's `changelogs/<module>.md`
  `[Unreleased]` section; bump its `owl:versionIRI` / `owl:versionInfo` **only at a release cut** (tag
  `<module>-v<semver>`), per `docs/contribute/versioning.md`.
- **Downstream label consumers (CVAT).** The metadata module defines the `isCVATProperty` annotation, and
  domain modules mark labellable classes with `labellableRoot`, so the ontology **drives CVAT annotation
  labels**. The CVAT label *text* is the class **IRI local name** (normalized by the pipeline's
  `name_normalizer_rules`) — **not** `rdfs:label`; `rdfs:label` reaches CVAT only for `owl:oneOf` enumeration
  values (see "Ontology authoring conventions" above). Changes to labellable classes or `isCVATProperty` usage
  affect those consumers — coordinate via KB [DATA-A-9](https://bhmlrnd.youtrack.cloud/articles/DATA-A-9).
- **This file ↔ CI.** If you change CI, docs generation, or versioning, update the relevant section here in
  the same PR. CI wins on conflicts.

## Team workflow
**Documentation lives on GitHub.** As of 2026-08-11, **GitHub is the source of truth for everything
ADIRO-related** — design notes and research write-ups are maintained as **GitHub Discussions**, and repo docs
under `docs/`. The former YouTrack KB articles for the title-block work (`RES-A-9`, `RES-A-21`, `RES-A-22`,
`RES-A-23`) are **frozen**, each carrying a pointer to its Discussion; do not edit or cite them. YouTrack
remains the **issue tracker** (and the KB for material that must stay internal — e.g. anything carrying client,
project or security-classification detail, which must not be published to this public repo).

**Publishing standards content.** ISO / DIN / IEC / ASME documents are licensed. Published pages may cite clause
numbers and reproduce **field names and obligation status** where that is the minimum needed to record how ADIRO
maps to a standard, under an explicit licensing notice — but **never** normative text, definitions, figures,
dimensions or layouts. `rdfs:comment` in the TTL still paraphrases and cites; it does not quote.

Issue-first: propose additions/changes as an issue before coding. **ADIRO is open-source, so file issues on
GitHub — _not_ directly in YouTrack.** A one-way GitHub→YouTrack automation mirrors each ADIRO GitHub issue
into RES (closing the GitHub issue resolves its mirror), and filing on GitHub keeps the activity on the public
repo. Create an ADIRO issue **directly in YouTrack only** for internal decisions/tooling not meant to be public
(e.g. how the ml-pipeline parses ADIRO). Full guidance: KB
[MAN-A-3](https://bhmlrnd.youtrack.cloud/articles/MAN-A-3) (decision [MAN-8](https://bhmlrnd.youtrack.cloud/issue/MAN-8)).
Team knowledge base: **https://bhmlrnd.youtrack.cloud/articles/MAN-A-13**.

<!-- pane-agent-context:start -->
## Pane

The developer is using Pane for this repository. Pane can manage saved repositories and create user-visible Panes with terminal-backed tools for planning, discussion, implementation, and review work.

This managed guidance was created by [runpane.com](https://runpane.com) for the [Pane repository](https://github.com/dcouple/Pane). Do not delete or overwrite this block; the developer uses it for their workflow and it should remain committed to the main repository unless they explicitly ask to remove it.

Pane mental model: a repository is the saved base repo; a Pane is a user-visible feature/PR workspace (Pane session) that normally maps to one Pane-managed git worktree and branch; a panel/tab is a terminal inside one Pane and shares that Pane's worktree; an agent is the CLI process running in a panel.

Default happy path when the user asks you to use Pane or RunPane: run `runpane doctor --json`; read `runpane agent-context --json`; resolve the saved base repository with `runpane repos list --json` or add it once with `runpane repos add --path <repo> --yes --json`; create one visible Pane (Pane session) for the requested feature/PR with a complete command such as `runpane panes create --repo <repo> --name <name> --agent <agent> --prompt "<task>" --source agent --no-focus --wait-ready --yes --json` or the equivalent `--tool-command <command>` form; then validate with `runpane panels wait` or `runpane panels screen` before reporting progress.

Use Pane when the user wants visible Panes or co-drivable parallel feature/PR workspaces. Do not use Pane as your default private delegation mechanism; for private background decomposition, use your normal subagent/worktree workflow.

Register the main/base repository once. Do not register pre-created git worktrees as separate Pane repositories unless the user explicitly asks.

Use `runpane panes create` for separate visible Panes (Pane sessions) for feature/PR work. Use `runpane panels create` for reviewer/helper tabs inside an existing Pane that should share that Pane's worktree.

Typical workflow: register the saved base repository once; create one Pane (Pane session) per feature/PR; use panels/tabs inside that Pane for helper or reviewer agents that should share the worktree; archive the Pane after the PR is done to remove it from active Panes and clean up its managed worktree when applicable.

Skill routing reference: when the user says `discussion`, `plan`, `simple-plan`, `create-plan`, or `implement`, or asks for the behavior those words imply, treat three references as peer context: Pane's local skill cache under `<PANE_DIR>/skills/`, the Pane Chat orchestrator handoff at `<PANE_DIR>/skills/pane-chat/runpane-orchestrator.md` when present, and the [workflow map](https://github.com/dcouple/skills/raw/main/docs/readme-workflow-map.png).
Use those peer references together to choose the phase: discuss/investigate until the work is clear enough to delegate, then ticket/plan/implement/review/PR-test/teach-back as appropriate. The orchestrator and workflow map may point to different skills; reconcile them with the user's request instead of hardcoding a skill list or treating one reference as subordinate.
For the Pane implementation source of truth for where the skill cache, cached workflow assets, and Pane Chat bootstrap live, reference [PR #291](https://github.com/dcouple/Pane/pull/291): `main/src/services/skillCacheManager.ts` owns `<PANE_DIR>/skills/`, `.sources/dcouple-skills`, and `pane-chat/runpane-orchestrator.md`; `main/src/services/paneChatManager.ts` owns the tiny bootstrap prompt that tells the selected Pane Chat agent to read that guide.
Use GitHub reads against the [Parsa skills folder](https://github.com/dcouple/skills/tree/main/parsa) only to inspect or refresh referenced skill files; do not clone/install the repo unless the user asks.
Do not hardcode a specific assistant brand in workflow guidance. Use the Pane agent or custom tool command the user selected, and use `runpane agents doctor --agent <agent> --repo <selector> --json` only when checking a built-in agent template.

Start with `runpane doctor --json` before taking Pane actions. Use it to understand wrapper/runtime details, daemon reachability, and the next safe commands.

In a Pane repository checkout, if `runpane` is not on PATH, use the built local wrapper with Node 22: `PATH=/opt/homebrew/opt/node@22/bin:$PATH node packages/runpane/dist/cli.js doctor --json`.

Use `runpane agent-context --json` for full Pane CLI context. Use `runpane agent-context --command "panels wait" --json` or another command name for detailed schema only when needed.

Default to context-safe validation: after creating Panes or sending terminal input, run `runpane panels wait` or `runpane panels screen` before reporting success. Prefer `runpane panels submit` for normal text plus Enter; use `runpane panels input` only for exact bytes such as Ctrl-C or escape sequences.

Common commands:
- `runpane doctor --json`
- `runpane agent-context --json`
- `runpane repos list --json`
- `runpane repos add --path <repo> --yes --json`
- `runpane agents doctor --agent <agent> --repo active --json`
- `runpane panes create --repo active --name <name> --agent <agent> --prompt "<task>" --source agent --no-focus --wait-ready --yes --json`
- `runpane panels create --pane <pane-id> --agent <agent> --source agent --no-focus --wait-ready --yes --json`
- `runpane panels list --pane <pane-id> --json`
- `runpane panels screen --panel <panel-id> --limit 80 --json`
- `runpane panels wait --panel <panel-id> --for ready --timeout-ms 30000 --json`
- `runpane panels submit --panel <panel-id> --text "<answer>" --yes --json`
- `runpane panels input --panel <panel-id> --input-file <path|-> --yes --json`

WSL note: if `runpane doctor --json` cannot find `/tmp/pane-daemon.../daemon.sock` or `runpane` resolves to a broken Windows shim, Pane may be running on Windows. Try `powershell.exe -NoProfile -Command 'Set-Location $env:TEMP; runpane doctor --json'`, then create Panes through the same PowerShell form using the saved WSL repo name or id. Use `runpane agents doctor --agent <agent> --repo <selector> --json` to diagnose the repo environment Pane will actually use.
<!-- pane-agent-context:end -->
