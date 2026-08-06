# Versioning

ADIRO is a suite of **four independently-versioned OWL modules** (dependency order):

1. `aec_drawing_metadata`
2. `aec_common_symbols`
3. `aec_domain_common`
4. `aec_facade_domain`

Each module carries **its own [SemVer](https://semver.org/) version** and is released on its own cadence — there is **no single umbrella version**. (Architecture & rationale: KB [DATA-A-10](https://bhmlrnd.youtrack.cloud/articles/DATA-A-10); plan & decisions: [RES-27](https://bhmlrnd.youtrack.cloud/issue/RES-27).)

Current versions: `aec_drawing_metadata` **2.0.0**; the other three **1.0.0**. These are per-module starting points, not a suite version.

## IRIs

Each module declares three kinds of IRI:

| Kind | Example | Stability |
|---|---|---|
| **Unversioned ontology IRI** ("latest") | `…/ADIRO/aec_drawing_metadata` | Always resolves to the current release |
| **Versioned IRI** (`owl:versionIRI`) | `…/ADIRO/aec_drawing_metadata/2.0.0` | Immutable — a specific release |
| **Term namespace** (`#`) | `…/ADIRO/aec_drawing_metadata#Titleblock` | **Unversioned / stable** — what consumers depend on |

- The `owl:versionIRI` **must** equal the unversioned ontology IRI + `/` + `owl:versionInfo` (enforced in CI — see [Validation](#validation)).
- **Filenames stay unversioned** (`aec_drawing_metadata.ttl`, never `aec_drawing_metadata_v2.ttl`). Versioned copies live under `versions/` (see [Releases](#releases)).
- **Term IRIs never carry a version** — term stability across releases is exactly what downstream consumers (e.g. the ml-drawing-data-pipeline, CVAT labels) rely on.

### Resolvability

Ontology files must be **resolvable** — the annotation pipeline pins a specific ontology version and must dereference the exact version it was built against. Served from GitHub Pages:

- **Latest:** `…/ADIRO/<module>.ttl` (e.g. `…/ADIRO/aec_drawing_metadata.ttl`).
- **Versioned:** `…/ADIRO/<module>/<semver>/<module>.ttl` (e.g. `…/ADIRO/aec_drawing_metadata/2.0.0/aec_drawing_metadata.ttl`) — published from `versions/` by the deploy workflow. Consumers that pin a version (e.g. the pipeline) reference this URL.

Note the declared `owl:versionIRI` (`…/<module>/<semver>`, without a filename) is an **identifier**, not necessarily dereferenceable on Pages — Pages can't content-negotiate, so you fetch the explicit `.ttl` above. A future `w3id.org` migration ([RES-69](https://bhmlrnd.youtrack.cloud/issue/RES-69)) would make the bare IRI content-negotiate.

## Bump rules (SemVer, per module)

The bump for a module is decided by classifying its change against **that module's last released version**, per the [compatibility-diff spec](https://github.com/BuroHappoldMachineLearning/ADIRO/blob/main/docs/governance/compatibility-diff-algorithm-spec.md):

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

Because dependents import a root (e.g. `aec_drawing_metadata`) at **latest**, a **MAJOR** bump on a root can break them at latest. Rule: after any module bump, the OWL reasoner should be run across the **whole suite at latest** to catch this — the intended release gate, to be **automated in CI** via the validation track ([RES-36](https://bhmlrnd.youtrack.cloud/issue/RES-36); not yet implemented — today's PR CI only runs `scripts/validate_ontology.py`). Any dependent that breaks gets **its own follow-up release** (bumped per its own compat classification). As a temporary WIP measure, a dependent may pin the prior root version (the documented+justified exception above) until updated.

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

Deeper ontology QA/QC — OWL reasoner consistency, unsatisfiable-class detection, ROBOT `report` — is a separate standing validation track ([RES-36](https://bhmlrnd.youtrack.cloud/issue/RES-36)) and is what backs the root-change reasoner gate above.
