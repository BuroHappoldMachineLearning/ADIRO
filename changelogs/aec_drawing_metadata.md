# Changelog — aec_drawing_metadata

Per-module SemVer. See [../docs/contribute/versioning.md](../docs/contribute/versioning.md).
Format: [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

_Pending changes accumulate here. `owl:versionInfo` / `owl:versionIRI` are bumped only at a release cut._

### Changed (BREAKING)
- **Migrated all IRIs from `github.io/ADIRO` to `w3id.org/adiro`** — ontology IRI, `owl:versionIRI` base, term namespace, and internal `owl:imports` ([#53](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/53)). w3id is the permanent, content-negotiating identifier (redirects to the unchanged GitHub Pages host). Every term IRI changes → a **MAJOR** bump at the next release cut. Fetch URLs on Pages and CVAT labels (URI-local-name-derived) are unaffected.

### Added
- **Eight terms relocated here from `aec_titleblock`** (team decision, 2026-09-14: this module is the single repository for drawing metadata, so new concepts land here rather than in a parallel module). Local names unchanged, so only the namespace moves: `Organisation`, `assertsMetadataFor`, `assertsClient`, `assertsOriginator`, `organisationName`, `dimensionUnits`, `assertsCrossReferenceNumber`, `extractionHint`. Non-breaking for this module (all `TERM_ADDED`); `aec_titleblock` was never released, so no published IRI is invalidated. Introduces the `skos:` prefix to this module for the first time (the relocated terms carry `skos:altLabel`).
  - **The `asserts<Thing>` naming is retained deliberately, and matters more here than it did in a separate module.** `assertsClient` (a claim read off a printed region) and `isCheckedBy` (a fact about a revision) now sit in one namespace, so the prefix no longer distinguishes claim from fact — the verb has to.
- **`layoutTitle`** — the caption naming an individual `Layout`, distinct from the sheet-level `drawingTitle`. A sheet routinely carries several drawings (details, sections, plans at different scales), each with its own printed title; without this they all inherit one title and cannot be told apart. Pairs with `layoutIdentifier` as title-to-number. Modelled as a datatype property on `Layout`, matching `drawingTitle` on `DrawingSheet` — titles in this ontology are properties, not regions.
- **`KeyPlan`** — a new `MetadataContainer` subclass for the small locator diagram showing where a sheet's subject sits within the wider building or site, plus a `min 0` `contains` restriction on `DrawingSheet` matching the existing `Legend` / `Note` pattern. Landed here rather than in `aec_titleblock` because it is a **detectable graphical region, not asserted text** — the same division that puts `Legend` and `RevisionTable` here. Evidence: the four-project title-block field survey (`docs/modularization/titleblock-field-survey-2026-09.md`), where it appeared as a distinct field on two of four projects ([#66](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/66)). **Downstream:** it carries `labellableRoot true`, so it introduces a **new CVAT annotation label** (`KeyPlan`, derived from the IRI local name) — coordinate per KB [DATA-A-9](https://bhmlrnd.youtrack.cloud/articles/DATA-A-9) before annotation work assumes the old label set.
- Ontology-header provenance metadata (`dcterms:title`, `dcterms:description`, `dcterms:license`, `dcterms:creator`, `dcterms:publisher`) for FAIR / registry readiness; clears the ROBOT `report` `missing_ontology_*` ERRORs (#50).

### Removed
- `owl:imports <http://www.w3.org/2002/07/owl#>` — importing the OWL vocabulary *as an ontology* made the merged suite non-OWL-2-DL (illegal `owl:topDataProperty` range axiom) and blocked the reasoner; removing it makes the suite consistent / DL-valid (#55). No semantic change.

## [2.0.0]

Current in-repo baseline (not yet cut as a GitHub release). Includes the [RES-37](https://bhmlrnd.youtrack.cloud/issue/RES-37) fix aligning
`owl:versionIRI` with `owl:versionInfo`. No earlier released version to diff against.
