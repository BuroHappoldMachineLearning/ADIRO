# Changelog — aec_facade_domain

Per-module SemVer. See [../docs/contribute/versioning/](../docs/contribute/versioning/).
Format: [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

_Pending changes accumulate here. `owl:versionInfo` / `owl:versionIRI` are bumped only at a release cut._

### Deprecated
- **This module is deprecated, and this is its final release** ([#171](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/171)). It is replaced by `adiro_facade_domain` (`https://w3id.org/adiro/adiro_facade_domain`), the same module under a name without the repeated "AEC", which continues this module's version numbering: its first release is this one plus a MAJOR. The `owl:Ontology` header says `owl:deprecated true` and `dcterms:isReplacedBy` `adiro_facade_domain`; nothing else changes. Every release of this module, this one included, stays published at its own IRI, and its terms keep their IRIs. The new module comes with a mapping from each term to its new IRI, and a script that rewrites a graph. Downstream consumers need to move to the new module.


## [3.0.0] — 2026-10-19

### Added
- **Example images for `DGU`, `Mineral wool`, `Transom`, `Gasket`, `Sealant`, `Bracket`, `ShelfAngle`, `Firestop` and `Mullion`** ([#152](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/152)): synthetic curtain-wall details drawn for ADIRO, one section at a slab edge with the term highlighted and a plan section for the mullion, linked with the `exampleImage` annotation.
- **Definitions** ([#152](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/152)): `Mullion`, `Transom`, `MineralWool`, `Sealant`, `Bracket` and `ShelfAngle` get an `rdfs:comment`, and the comment of `DGU`, which only repeated its name, now says what the term is.

### Changed (BREAKING)
- **Uses the renamed labelling annotation** ([#141](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/141)): `labellableRoot` becomes `isComputerVisionLabel` on every term that carried it (see `aec_drawing_metadata`). The values are unchanged.


## [2.0.2] — 2026-10-13

### Added
- The ontology header now names every earlier published release with `owl:priorVersion` (1.0.0 and 2.0.0), so a tool that reads only the latest release can list and open the earlier ones ([#122](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/122)). No term changes.


### Removed
- The unused `owl:imports` of `aec_common_symbols`: nothing in this module refers to a term of it ([#134](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/134)). A consumer that relied on loading `aec_common_symbols` through this module imports it directly. No term changes.

## [2.0.1] — 2026-10-09

### Added
- **`rdfs:comment` descriptions for four previously-undescribed terms** — `Gasket`, `Firestop`, `CavityBarrier` and `Louvre`. Each is a short plain-language definition consistent with the term's place in the taxonomy. Partly clears this module from the [#87](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/87) undescribed-terms backlog. Annotation-only, non-breaking.

## [2.0.0] — 2026-08-10

### Changed (BREAKING)
- **Migrated all IRIs from `github.io/ADIRO` to `w3id.org/adiro`** — ontology IRI, `owl:versionIRI` base, term namespace, and internal `owl:imports` ([#53](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/53)). w3id is the permanent, content-negotiating identifier (redirects to the unchanged GitHub Pages host). Every term IRI changes → a **MAJOR** bump at the next release cut. Fetch URLs on Pages and annotation-tool labels (URI-local-name-derived) are unaffected.

### Added
- Ontology-header provenance metadata (`dcterms:title`, `dcterms:description`, `dcterms:license`, `dcterms:creator`, `dcterms:publisher`) for FAIR / registry readiness (#50).

### Changed
- Relabel `:StickCurtainWall` ("Stick"→"Stick Curtain Wall"), `:UnitisedCurtainWall` ("Unitised"→"Unitised
  Curtain Wall"), `:SemiUnitisedCurtainWall` ("Semi-unitised"→"Semi Unitised Curtain Wall"), and
  `:DeadLoadBracket` ("Dead load"→"Dead Load Bracket") to follow the labelling convention (label contains the
  spaced class name). Fixes duplicate `rdfs:label`s that collided with `:Stick` / `:Unitised` /
  `aec_domain_common:DeadLoad` (ROBOT `duplicate_label`, [RES-36]). No IRI or semantic change.

## [1.0.0]

Initial in-repo baseline (not yet cut as a GitHub release). No earlier released version to diff against.
