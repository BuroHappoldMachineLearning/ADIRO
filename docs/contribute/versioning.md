# Versioning

ADIRO is a suite of **four independently-versioned OWL modules** (dependency order):

1. `aec_drawing_metadata`
2. `aec_common_symbols`
3. `aec_domain_common`
4. `aec_facade_domain`

Each module carries **its own [SemVer](https://semver.org/) version** and is released on its own cadence — there is **no single umbrella version**. (Architecture & rationale: KB [DATA-A-10](https://bhmlrnd.youtrack.cloud/articles/DATA-A-10); plan & decisions: [RES-27](https://bhmlrnd.youtrack.cloud/issue/RES-27).)

Current versions: `aec_drawing_metadata` **2.0.0**; the other three **1.0.0**. These are per-module starting points, not a suite version.

## IRIs

Each module declares three kinds of IRI, all on the canonical **`w3id.org/adiro`** namespace (since the [#53](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/53) migration; the files are physically served from GitHub Pages — see [Resolvability](#resolvability)):

| Kind | Example | Stability |
|---|---|---|
| **Unversioned ontology IRI** ("latest") | `https://w3id.org/adiro/aec_drawing_metadata` | Identifies the current release |
| **Versioned IRI** (`owl:versionIRI`) | `https://w3id.org/adiro/aec_drawing_metadata/2.0.0` | Immutable — a specific release |
| **Term namespace** (`#`) | `https://w3id.org/adiro/aec_drawing_metadata#Titleblock` | **Unversioned / stable** — what consumers depend on |

- The `owl:versionIRI` **must** equal the unversioned ontology IRI + `/` + `owl:versionInfo` (enforced in CI — see [Validation](#validation)).
- **Filenames stay unversioned** (`aec_drawing_metadata.ttl`, never `aec_drawing_metadata_v2.ttl`). Versioned copies live under `versions/` (see [Releases](#releases)).
- **Term IRIs never carry a version** — term stability across releases is exactly what downstream consumers (e.g. the ml-drawing-data-pipeline, CVAT labels) rely on.

### Resolvability

Ontology files must be **resolvable** — the annotation pipeline pins a specific ontology version and must dereference the exact version it was built against. Served from GitHub Pages:

- **Latest:** `…/ADIRO/<module>.ttl` (e.g. `…/ADIRO/aec_drawing_metadata.ttl`).
- **Versioned:** `…/ADIRO/<module>/<semver>/<module>.ttl` (e.g. `…/ADIRO/aec_drawing_metadata/2.0.0/aec_drawing_metadata.ttl`) — published from `versions/` by the deploy workflow. Consumers that pin a version (e.g. the pipeline) reference this URL.

The ontology IRIs are `w3id.org/adiro/…` **identifiers**, distinct from the physical `.ttl` fetch URLs above. Through w3id they **content-negotiate** (bare IRI → the `.ttl` for RDF clients, or the HTML docs for browsers); the raw GitHub Pages `.ttl` URLs remain the direct-fetch fallback (Pages itself can't content-negotiate).

#### `w3id.org/adiro` (live — content-negotiating front door)

**`https://w3id.org/adiro/…` is live** ([perma-id/w3id.org#6514](https://github.com/perma-id/w3id.org/pull/6514)) and *does* content-negotiate, redirecting (302) to the Pages files above:

| Request | Resolves to |
|---|---|
| `w3id.org/adiro/<module>` + `Accept: text/turtle` | latest `…/ADIRO/<module>.ttl` |
| `w3id.org/adiro/<module>` + `Accept: text/html` | the pyLODE HTML docs page |
| `w3id.org/adiro/<module>/<semver>` | that version's `.ttl` |
| `w3id.org/adiro/<any path>` | passthrough to `…/ADIRO/<any path>` |

w3id is a **host-independent** front door: it redirects *to* github.io today, so if hosting ever moves only the `.htaccess` changes and pinned `w3id` URLs keep working. **The ontology's own IRIs are still `github.io`** — repointing them to `w3id.org/adiro` is a separate, deliberate identity change (deferred; [RES-69](https://bhmlrnd.youtrack.cloud/issue/RES-69)). Until then, consumers may pin **either** front door for a given version.

## Bump rules (SemVer, per module)

The bump for a module is decided by classifying its change against **that module's last released version**, per the [compatibility-diff spec](../governance/compatibility-diff-algorithm-spec.md):

| Bump | When | Examples |
|---|---|---|
| **MAJOR** (`x.0.0`) | Any **breaking** change | Term removed/renamed, namespace moved, type changed, a restriction tightened so existing data becomes invalid, **deprecation** (see below) |
| **MINOR** (`x.y.0`) | **Non-breaking** additions | New class/property/individual, a loosened restriction |
| **PATCH** (`x.y.z`) | Annotation-only | Labels, comments, `rdfs:seeAlso`, metadata |

*Potentially-breaking* changes (domain/range/superclass changes) default to **MAJOR** unless review confirms they're safe.

## Imports

- **Internal imports default to "latest"** — modules import each other via the **unversioned** IRI (`owl:imports <…/aec_drawing_metadata>`). The working norm is to keep every module functioning against every other module's *latest*.
- **Version-pinned imports are allowed only for WIP / specific cases**, and each pinned import **must be documented and justified**: an `rdfs:comment` on the `owl:imports` axiom **plus** a note in the module's changelog. Treat a pin as **temporary** unless the justification is permanent.
- **External-ontology imports** (geometry, DaNO, …) follow a separate strategy — SLME extraction + version-pinning + a reasoner gate. See KB [RES-A-12](https://bhmlrnd.youtrack.cloud/articles/RES-A-12) / [RES-68](https://bhmlrnd.youtrack.cloud/issue/RES-68).

### Root change that could break dependents

Because dependents import a root (e.g. `aec_drawing_metadata`) at **latest**, a **MAJOR** bump on a root can break them at latest. Rule: after any module bump, the OWL reasoner should be run across the **whole suite at latest** to catch this — **now automated as a blocking CI gate** (`ontology-reasoning.yml`, [RES-36](https://bhmlrnd.youtrack.cloud/issue/RES-36)): every ontology PR is reasoned (HermiT) over the merged suite at latest and fails if it becomes inconsistent or gains an unsatisfiable class. Any dependent that breaks gets **its own follow-up release** (bumped per its own compat classification). As a temporary WIP measure, a dependent may pin the prior root version (the documented+justified exception above) until updated.

## Deprecation — never delete

Never delete or re-use a term IRI. To remove a term: mark it `owl:deprecated true`, add a history note, and provide a replacement mapping (`owl:equivalentClass` / `rdfs:subClassOf`) per the compatibility-diff spec. Deprecation counts as a **MAJOR** change. This keeps consumers' data valid across releases.

## Changelogs

Every change is recorded in **Keep-a-Changelog** style:

- **Per-module changelog** — `changelogs/<module>.md` is the **source of truth** for that module (so a leaf ontology stays independently extractable with its own history). Day-to-day edits accumulate under an **`[Unreleased]`** heading.
- **Top-level rollup** — `CHANGELOG.md` links the modules and their latest entries.

`owl:versionInfo` / `owl:versionIRI` are **only** bumped at a release cut (below) — *not* on every edit. In-flight edits live under `[Unreleased]`.

## Releases

A release affects **only the changed module(s)**. To cut a release for a module:

1. **Determine the bump** by classifying the change vs the module's last released version (compat-diff spec) → MAJOR / MINOR / PATCH.
2. **Bump** `owl:versionInfo` **and** `owl:versionIRI` in that module's `.ttl` (CI enforces tag == `versionInfo` == `versionIRI` tail).
3. **Move** that module's `[Unreleased]` changelog entries under the new version heading.
4. **Tag** `<module>-v<semver>` — e.g. `aec_common_symbols-v1.2.0` — and create a **GitHub Release**.
5. **Snapshot** (automatic): `.github/workflows/backup-version.yml` copies the module to `versions/<module>/<semver>/`.
6. **Publish** (automatic): the Pages deploy serves the unversioned latest `…/<module>.ttl` and the versioned snapshot `…/<module>/<semver>/<module>.ttl` as resolvable URLs.

If several modules changed together, cut **one tag per changed module** — each is an independent release.

> Tag convention: `<module>-v<semver>`. Module names use `_` and never contain `-v`, so the tag parses unambiguously into module + version, and maps 1:1 to the versionIRI path `…/<module>/<semver>`.

## Validation

Every PR runs `scripts/validate_ontology.py` (via `validate-ontology.yml`), which checks TTL parsing, circular subclass hierarchies, an `owl:Ontology` declaration, **and per-module version consistency** ([RES-66](https://bhmlrnd.youtrack.cloud/issue/RES-66)): each module must carry exactly one `owl:versionInfo` and one `owl:versionIRI`, and the versionIRI must equal the unversioned ontology IRI + `/` + the versionInfo.

PRs also run `scripts/compat_diff.py` ([RES-67](https://bhmlrnd.youtrack.cloud/issue/RES-67), **warn** mode): it classifies each module's change against its last released snapshot (per the [compatibility-diff spec](../governance/compatibility-diff-algorithm-spec.md)) and flags when the **declared** version bump is smaller than the change requires. It's advisory for now; the entailment-based upgrade and `enforce` mode are Phase 2b (RES-78 / RES-81).

On any PR that touches an ontology, a second workflow (`compat-diff-comment.yml`) posts a **sticky comment** with two parts: **Changes in this PR** (deltas diffed against the base branch — what the PR itself touches) and **Next version if released** (the cumulative forecast — each module's `src/` vs its last released snapshot, i.e. the running total of *all* unreleased changes). Because `owl:versionInfo` is only bumped at the release cut, the forecast spans every unreleased PR, not just this one; an under-bump warning appears only on a release-cut PR that bumped `owl:versionInfo` by less than the change requires.

Ontology PRs also run **`ontology-reasoning.yml`** ([RES-36](https://bhmlrnd.youtrack.cloud/issue/RES-36)): HermiT reasons over the whole suite at latest — a **blocking gate** on inconsistency / unsatisfiable classes / non-OWL-2-DL — plus ROBOT `report` for structural QC (**advisory**; e.g. `duplicate_label` is a warning). This backs the root-change reasoner gate above. Reproduce it locally with `scripts/run_reasoning.sh` (see the repo `AGENTS.md`).

## How ADIRO versioning compares to ODK / OBO Foundry

The de-facto standard for open scientific ontologies is the [OBO Foundry](https://obofoundry.org/) conventions, tooled by the [Ontology Development Kit (ODK)](https://github.com/INCATools/ontology-development-kit). ADIRO is not an OBO ontology, but OBO/ODK is the most mature reference point for ontology versioning, so we track it deliberately — matching it where it is sound and diverging where our use case (machine-readable AEC drawings feeding a **version-pinned ML pipeline**) demands more.

| Dimension | OBO Foundry / ODK | ADIRO | Assessment |
|---|---|---|---|
| **Version identifier** | Dated releases (`YYYY-MM-DD`) **preferred**; SemVer only "acceptable" ([Principle 4](https://obofoundry.org/principles/fp-004-versioning.html)) | **SemVer, per module** (`x.y.z`) | Both satisfy Principle 4 (unique, resolvable, versioned IRI). We chose SemVer deliberately — see next row. |
| **Compatibility in the version** | **Not encoded** — a date conveys recency, not whether a release breaks consumers | **Encoded** — MAJOR/MINOR/PATCH classified by the [compatibility-diff spec](../governance/compatibility-diff-algorithm-spec.md) and checked in CI | **ADIRO does better for our purpose.** A pinned consumer (the ML pipeline, CVAT) reads a MAJOR bump as "your pinned build may break"; OBO consumers must diff releases themselves. |
| **Modularity** | One ontology → one version and cadence (imports handled as modules) | **Four independently-versioned modules** | Trade-off. Per-module suits a layered suite whose parts evolve at different rates; OBO's single number is simpler to track. |
| **Resolvable IRIs** | OBO PURL (`purl.obolibrary.org`, `.htaccess` redirect) + dated version IRI | `w3id.org/adiro` content-negotiating front door + versioned IRI | **Par** — the same pattern (community redirect layer, resolvable versioned IRIs). |
| **Deprecation** | Never delete; `owl:deprecated`, replace axioms, `replaced_by`/`consider`, `obsolete ` label prefix | Never delete; `owl:deprecated` + replacement mapping (counts as MAJOR) | **Par** — we follow the OBO obsoletion model. (We do not yet use the `obsolete ` label prefix / `IAO:0100001` "term replaced by" annotations — a low-cost alignment we could adopt.) |
| **Reasoning + structural QC** | Bundles ROBOT + reasoners (ELK / HermiT / Konclude); runs reasoning + `robot report` in CI | HermiT (full OWL 2 DL) as a **blocking** gate + `robot report` (advisory) | **Par / slightly stricter** — we block on inconsistency / unsatisfiability across the merged suite. |
| **Release products** | Multiple variants (`-base`, `-simple`, `-full`, extracted imports) via a Makefile | Single `.ttl` per module (unversioned latest + versioned snapshot) | **ODK does more.** We do not yet need variant products; ODK's are valuable at OBO scale. |
| **Import handling** | SLME module extraction, version-pinned in config | SLME extract + pin + reasoner gate ([RES-68](https://bhmlrnd.youtrack.cloud/issue/RES-68)) | **Par.** |
| **Changelogs / release notes** | Varies by project; GitHub Releases | Keep-a-Changelog per module + top-level rollup + auto-populated Release notes | **ADIRO more structured.** |
| **Tooling maturity** | Mature, batteries-included (Docker image, Makefile, dashboards, large community) | Bespoke scripts, younger, small surface | **ODK does better** — battle-tested and widely adopted. |

**Net:** for the thing that matters most to us — telling a *machine* consumer whether a new release is safe to adopt — ADIRO is stronger than the OBO default, because we encode compatibility in SemVer and enforce it with the compatibility-diff classifier plus the reasoner gate, rather than leaving consumers to diff dated releases. Where ODK is stronger — a mature, general-purpose release framework with variant products and a large community — we deliberately kept a smaller bespoke setup sized to ADIRO today, while staying close enough to OBO conventions (resolvable versioned IRIs, never-delete deprecation, reasoning + ROBOT QC) that adopting ODK tooling later would be evolutionary, not a rewrite.
