# Changelog — aec_common_symbols

Per-module SemVer. See [../docs/contribute/versioning/](../docs/contribute/versioning/).
Format: [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

_Pending changes accumulate here. `owl:versionInfo` / `owl:versionIRI` are bumped only at a release cut._


## [4.0.1] — 2026-10-21

### Deprecated
- **This module is deprecated, and this is its final release** ([#171](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/171)). It is replaced by `adiro_common_symbols` (`https://w3id.org/adiro/adiro_common_symbols`), the same module under a name without the repeated "AEC", which continues this module's version numbering: its first release is this one plus a MAJOR. The `owl:Ontology` header says `owl:deprecated true` and `dcterms:isReplacedBy` `adiro_common_symbols`; nothing else changes. Every release of this module, this one included, stays published at its own IRI, and its terms keep their IRIs. The new module comes with a mapping from each term to its new IRI, and a script that rewrites a graph. Downstream consumers need to move to the new module.


## [4.0.0] — 2026-10-19

### Added
- **Example images for `Dimension`, `Grid` and `ReferenceSymbol`** ([#152](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/152)): synthetic images drawn for ADIRO with fictional content (a dimension chain, a grid with bubbles, and section, detail and elevation markers), linked with the `exampleImage` annotation.

### Changed
- **`ReferenceSymbol` classified under `ReferenceExpression`** ([#95](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/95)): its superclass changes from `DrawingElement` to the shared `metadata:ReferenceExpression`, which is itself a `DrawingElement`. Everything `ReferenceSymbol` entailed before is still entailed, and its `referencesLayout` relation is unchanged.

### Changed (BREAKING)
- **Uses the renamed labelling annotation** ([#141](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/141)): `labellableRoot` becomes `isComputerVisionLabel` on every term that carried it (see `aec_drawing_metadata`). The values are unchanged.


## [3.0.1] — 2026-10-13

### Added
- The ontology header now names every earlier published release with `owl:priorVersion` (1.0.0 and 2.0.0), so a tool that reads only the latest release can list and open the earlier ones ([#122](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/122)). No term changes.

## [3.0.0] — 2026-10-09

### Removed (BREAKING)
- **`appearsOn` and `isReferencedBy`** — the declared inverses of `hasReferenceSymbol` and
  `referencesLayout`, together with both `owl:inverseOf` axioms. [#21](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/21) decided project-wide that ADIRO
  declares no named inverse properties and no `owl:inverseOf` axioms. Only the forward direction of each pair
  survives: `hasReferenceSymbol` (Layout → ReferenceSymbol, ⊂ `metadata:contains`) and `referencesLayout`
  (ReferenceSymbol → Layout); reverse navigation uses SPARQL inverse paths. UC-03's CQ 3.3 validation query is
  rewritten accordingly. **MAJOR bump (3.0.0).**

## [2.0.0] — 2026-08-10

### Changed (BREAKING)
- **Migrated all IRIs from `github.io/ADIRO` to `w3id.org/adiro`** — ontology IRI, `owl:versionIRI` base, term namespace, and internal `owl:imports` ([#53](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/53)). w3id is the permanent, content-negotiating identifier (redirects to the unchanged GitHub Pages host). Every term IRI changes → a **MAJOR** bump at the next release cut. Fetch URLs on Pages and annotation-tool labels (URI-local-name-derived) are unaffected.

### Added
- Ontology-header provenance metadata (`dcterms:title`, `dcterms:description`, `dcterms:license`, `dcterms:creator`, `dcterms:publisher`) for FAIR / registry readiness (#50).

## [1.0.0]

Initial in-repo baseline (not yet cut as a GitHub release). No earlier released version to diff against.
