# Changelog — aec_drawing_metadata

Per-module SemVer. See [../docs/contribute/versioning.md](../docs/contribute/versioning.md).
Format: [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

_Pending changes accumulate here. `owl:versionInfo` / `owl:versionIRI` are bumped only at a release cut._

### Changed (BREAKING)
- **Migrated all IRIs from `github.io/ADIRO` to `w3id.org/adiro`** — ontology IRI, `owl:versionIRI` base, term namespace, and internal `owl:imports` ([#53](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/53)). w3id is the permanent, content-negotiating identifier (redirects to the unchanged GitHub Pages host). Every term IRI changes → a **MAJOR** bump at the next release cut. Fetch URLs on Pages and CVAT labels (URI-local-name-derived) are unaffected.

### Changed
- **`hasScale` now applies to `Layout` as well as `DrawingSheet`** — domain widened to `owl:unionOf (DrawingSheet Layout)`. A sheet routinely carries several drawings at different scales (a detail at 1:5 beside a plan at 1:100), which a single sheet-level scale cannot express.
  - **Widened rather than reused as-is, deliberately.** `rdfs:domain` in OWL is an *inference* rule, not a constraint: leaving the domain as `DrawingSheet` and asserting `someLayout hasScale "1:5"` would have made a reasoner infer `someLayout a DrawingSheet` — silently typing every scaled layout as a drawing sheet, which then requires it to contain a `Titleblock` and a `Layout` of its own. Not an inconsistency (nothing declares the two disjoint), which is exactly why it would have gone unnoticed.
  - Uses the `owl:unionOf` domain idiom already established in this file by `hasOrientation`.
  - **Non-breaking:** a *widened* domain permits strictly more than before, and every existing `DrawingSheet hasScale` assertion remains valid with the same entailments.
  - Side effect worth knowing: the common caption line `3  MULLION HEAD  1:5` now decomposes completely across three properties on one `Layout` — `layoutIdentifier`, `layoutTitle`, `hasScale`. `layoutTitle`'s extraction hint said the scale was sheet-level and has been corrected.
- **`DrawingSheet`'s `RevisionTable` cardinality relaxed from `exactly 1` to `min 0`.** A sheet is no longer required to contain a revision table *directly*.
  - **Why.** `:contains` is direct, non-transitive containment, and `Titleblock` may now contain a `RevisionTable` (above). Under the old `exactly 1`, a sheet whose revision table is printed inside the title-block strip — asserted naturally as `sheet contains titleblock` + `titleblock contains revisionTable` — had no *direct* `RevisionTable`, so a reasoner would infer a second, anonymous one. The constraint and the real-world layout were in conflict, and the layout wins.
  - **Be precise about what `min 0` does:** it is logically vacuous — it asserts nothing. This is the file's documentation idiom for "may contain", so the practical effect is that **the constraint is removed**, not replaced with a weaker one.
  - **Classified non-breaking** per the [compatibility-diff spec](../docs/governance/compatibility-diff-algorithm-spec.md) (`RESTRICTION_LOOSENED`), and nothing previously valid becomes invalid. Worth noting the one real cost anyway: an *entailment is lost*. You could previously infer from `?x a DrawingSheet` that `?x` contains a `RevisionTable`; you no longer can. No competency question in `docs/uc-orsd/` was found to depend on that — checked before making the change — but a consumer relying on the inference rather than on asserted data would notice.
  - `Titleblock`'s own `exactly 1` on `DrawingSheet` is **unchanged**: every sheet still has exactly one title block.

### Added
- **Eight terms relocated here from `aec_titleblock`** (team decision, 2026-09-14: this module is the single repository for drawing metadata, so new concepts land here rather than in a parallel module). Local names unchanged, so only the namespace moves: `Organisation`, `assertsMetadataFor`, `assertsClient`, `assertsOriginator`, `organisationName`, `assertsCrossReferenceNumber`, `extractionHint`. (`dimensionUnits` relocated with them but was **withdrawn 2026-09-14** before merge — see below — so seven of the eight land.) Non-breaking for this module (all `TERM_ADDED`); `aec_titleblock` was never released, so no published IRI is invalidated. Introduces the `skos:` prefix to this module for the first time (the relocated terms carry `skos:altLabel`).
  - **The `asserts<Thing>` naming is retained deliberately, and matters more here than it did in a separate module.** `assertsClient` (a claim read off a printed region) and `isCheckedBy` (a fact about a revision) now sit in one namespace, so the prefix no longer distinguishes claim from fact — the verb has to.
- **`dimensionUnits` withdrawn before merge (2026-09-14).** It relocated with the other seven, then went for the same reason as `planKey`: a German-practice field (DIN 1356-1's `1:50 – m,cm`) that appeared in **none** of the four surveyed projects, so it does not clear the agreed `<40%-of-sheets` rule. Withdrawn as **unevidenced, not as wrong** — the surveyed corpus is UK/US, and the vocabulary review had separately confirmed the concept is genuinely not covered elsewhere, so it is a plausible return once German projects are sampled. Recorded in the survey doc §7.3.
- **`layoutTitle`** — the caption naming an individual `Layout`, distinct from the sheet-level `drawingTitle`. A sheet routinely carries several drawings (details, sections, plans at different scales), each with its own printed title; without this they all inherit one title and cannot be told apart. Pairs with `layoutIdentifier` as title-to-number. Modelled as a datatype property on `Layout`, matching `drawingTitle` on `DrawingSheet` — titles in this ontology are properties, not regions.
- **`Titleblock` may now contain `KeyPlan`, `Legend` and `RevisionTable`** — three `min 0` `contains` restrictions, since all three are commonly printed inside the title-block strip rather than standing alone on the page. Each may alternatively be contained directly by the `DrawingSheet`, as before.
  - The cardinality tension this opened for `RevisionTable` is **resolved** — see *Changed* below.
- **`KeyPlan`** — a new `MetadataContainer` subclass for the small locator diagram showing where a sheet's subject sits within the wider building or site, plus a `min 0` `contains` restriction on `DrawingSheet` matching the existing `Legend` / `Note` pattern. Landed here rather than in `aec_titleblock` because it is a **detectable graphical region, not asserted text** — the same division that puts `Legend` and `RevisionTable` here. Evidence: the four-project title-block field survey (`docs/modularization/titleblock-field-survey-2026-09.md`), where it appeared as a distinct field on two of four projects ([#66](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/66)). **Downstream:** it carries `labellableRoot true`, so it introduces a **new CVAT annotation label** (`KeyPlan`, derived from the IRI local name) — coordinate per KB [DATA-A-9](https://bhmlrnd.youtrack.cloud/articles/DATA-A-9) before annotation work assumes the old label set.
- Ontology-header provenance metadata (`dcterms:title`, `dcterms:description`, `dcterms:license`, `dcterms:creator`, `dcterms:publisher`) for FAIR / registry readiness; clears the ROBOT `report` `missing_ontology_*` ERRORs (#50).

### Removed
- `owl:imports <http://www.w3.org/2002/07/owl#>` — importing the OWL vocabulary *as an ontology* made the merged suite non-OWL-2-DL (illegal `owl:topDataProperty` range axiom) and blocked the reasoner; removing it makes the suite consistent / DL-valid (#55). No semantic change.

## [2.0.0]

Current in-repo baseline (not yet cut as a GitHub release). Includes the [RES-37](https://bhmlrnd.youtrack.cloud/issue/RES-37) fix aligning
`owl:versionIRI` with `owl:versionInfo`. No earlier released version to diff against.
