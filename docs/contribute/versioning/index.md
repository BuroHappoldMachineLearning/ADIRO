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

The bump for a module is decided by classifying its change against **that module's last released version**, per the [compatibility-diff spec](compatibility-diff-algorithm-spec.md):

| Bump | When | Examples |
|---|---|---|
| **MAJOR** (`x.0.0`) | Any **breaking** change | Term removed/renamed, namespace moved, type changed, a restriction tightened so existing data becomes invalid, **deprecation** (see below) |
| **MINOR** (`x.y.0`) | **Non-breaking** additions | New class/property/individual, a loosened restriction |
| **PATCH** (`x.y.z`) | Annotation-only | Labels, comments, `rdfs:seeAlso`, metadata |

*Potentially-breaking* changes (domain/range/superclass changes) default to **MAJOR** unless review confirms they're safe.

## Imports

- **Internal imports default to "latest"** — modules import each other via the **unversioned** IRI (`owl:imports <…/aec_drawing_metadata>`). The working norm is to keep every module functioning against every other module's *latest*.
- **Version-pinned imports are allowed only for WIP / specific cases**, and each pinned import **must be documented and justified**: an `rdfs:comment` on the `owl:imports` axiom **plus** a note in the module's changelog. Treat a pin as **temporary** unless the justification is permanent.
- **External-ontology imports** (geometry, PROV-O, DAnO, …) follow a separate strategy — prefer a **local stub + alignment** with no import at all; where the source's entailments are actually needed, **SLME extraction** (`robot extract --method STAR`) from the **version-pinned core file**, with the reasoner gate as the safeguard. A pinned external source is subject to the same document-and-justify rule as above. Full rule: **[External ontology imports](../../design-decisions/external-ontology-imports.md)**; decision record in [Discussion #74](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/74); implementation in [RES-68](https://bhmlrnd.youtrack.cloud/issue/RES-68).

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

A release affects **only the changed module(s)**: determine the bump (compat-diff spec), bump `owl:versionInfo`/`owl:versionIRI`, move that module's `[Unreleased]` changelog entries under the new version heading, then tag `<module>-v<semver>` (e.g. `aec_common_symbols-v1.2.0`) and publish a **GitHub Release** from that tag. Snapshotting to `versions/<module>/<semver>/` and publishing to Pages then happen automatically — see **[Release process](release-process.md)** for the step-by-step and which GitHub Action does what.

If several modules changed together, cut **one tag per changed module** — each is an independent release.

## Naming earlier versions with `owl:priorVersion`

Every release names **all** of its earlier published versions with `owl:priorVersion`, one line per version IRI, in the `owl:Ontology` header of the module:

```turtle
<https://w3id.org/adiro/aec_drawing_metadata> a owl:Ontology ;
    owl:priorVersion <https://w3id.org/adiro/aec_drawing_metadata/2.0.0> ;
    owl:priorVersion <https://w3id.org/adiro/aec_drawing_metadata/3.0.0> ;
    owl:priorVersion <https://w3id.org/adiro/aec_drawing_metadata/4.0.0> ;
    owl:versionIRI <https://w3id.org/adiro/aec_drawing_metadata/4.0.1> ;
    owl:versionInfo "4.0.1" .
```

The list is complete, not just the previous version, because a tool such as [OntoCanvas](https://alelom.github.io/OntoCanvas/) reads the open file and the latest release (fetched from the ontology IRI) and does not follow a chain of releases: the latest release has to say which versions exist, so that a person can list and open each of them.

- **The release cut writes it.** `scripts/prepare_release.py` rewrites the lines for each module it releases, from the releases archived under `versions/<module>/`. They are not edited by hand, and a hand-made release runs `uv run python scripts/prepare_release.py priors` after bumping the version.
- **Only published releases are named.** A version is listed when it is archived under `versions/`, which is what the deploy publishes, so its IRI resolves. A module's first release has nothing to list. `aec_drawing_metadata` 1.0.0 was never published under a resolvable version IRI (no archive, and neither its `w3id.org` nor its old host IRI answers), so it is not listed.
- **The IRI named is the `w3id.org/adiro` one.** Releases made before the `w3id.org` front door existed (`aec_common_symbols`, `aec_domain_common` and `aec_facade_domain` 1.0.0, and `aec_drawing_metadata` 2.0.0) declare their `owl:versionIRI` on the physical host, and that host form does not itself resolve. Archived releases are never edited, so the `w3id.org` IRI of the same version is named, and validation accepts the legacy form as that release's declared IRI.
- **Archived releases are never edited.** The list in the latest release is the one place that names them.
- **A change to the header is a PATCH.** The compatibility diff treats a changed header annotation (anything except `owl:versionIRI`, `owl:versionInfo` and `owl:imports`) as `ONTOLOGY_HEADER_CHANGED`, a non-breaking change that requires a PATCH, so a header-only change produces a release like any other.

Two checks keep the lists true. `scripts/validate_ontology.py` (every PR, blocking) requires each `owl:priorVersion` to be a version IRI of the same module, earlier than the file's own version and archived with a matching `owl:versionIRI`, and every earlier archived release to be listed. After each deploy, the `verify-prior-versions` job of `generate-deploy-docs.yml` runs `scripts/check_prior_versions.py`: each IRI is requested with `Accept: text/turtle`, must answer HTTP 200 after redirects, and must serve the release whose `owl:versionIRI` it names.

## Validation

Every PR runs `scripts/validate_ontology.py` (via `validate-ontology.yml`), which checks TTL parsing, circular subclass hierarchies, an `owl:Ontology` declaration, **and per-module version consistency** ([RES-66](https://bhmlrnd.youtrack.cloud/issue/RES-66)): each module must carry exactly one `owl:versionInfo` and one `owl:versionIRI`, and the versionIRI must equal the unversioned ontology IRI + `/` + the versionInfo.

The same `validate-ontology.yml` run also runs `scripts/compat_diff.py` ([RES-67](https://bhmlrnd.youtrack.cloud/issue/RES-67), **warn** mode): it classifies each module's change against its last released snapshot (per the [compatibility-diff spec](compatibility-diff-algorithm-spec.md)) and flags when the **declared** version bump is smaller than the change requires. It's advisory for now; the entailment-based upgrade and `enforce` mode are Phase 2b (RES-78 / RES-81).

On any PR that touches an ontology, a second workflow (`compat-diff-comment.yml`) posts a **sticky comment** with two parts: **Changes in this PR** (deltas diffed against the base branch — what the PR itself touches) and **Next version if released** (the cumulative forecast — each module's `src/` vs its last released snapshot, i.e. the running total of *all* unreleased changes). Because `owl:versionInfo` is only bumped at the release cut, the forecast spans every unreleased PR, not just this one; an under-bump warning appears only on a release-cut PR that bumped `owl:versionInfo` by less than the change requires.

Ontology PRs also run **`ontology-reasoning.yml`** ([RES-36](https://bhmlrnd.youtrack.cloud/issue/RES-36)): HermiT reasons over the whole suite at latest — a **blocking gate** on inconsistency / unsatisfiable classes / non-OWL-2-DL — plus ROBOT `report` for structural QC (**advisory**; e.g. `duplicate_label` is a warning). This backs the root-change reasoner gate above. Reproduce it locally with `scripts/run_reasoning.sh` (see the repo `AGENTS.md`).

## How ADIRO versioning compares to ODK / OBO Foundry

See **[Versioning vs. ODK / OBO Foundry](versioning-vs-odk.md)** — a side-by-side comparison of ADIRO's scheme with the OBO Foundry / ODK standard, and where we do better or worse. In short: we deliberately chose SemVer plus an enforced compatibility contract over OBO's date-based releases, because our downstream consumers *pin* a version and need to know when a release breaks them.
