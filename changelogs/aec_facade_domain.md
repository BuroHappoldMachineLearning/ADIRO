# Changelog — aec_facade_domain

Per-module SemVer. See [../docs/contribute/versioning.md](../docs/contribute/versioning.md).
Format: [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

_Pending changes accumulate here. `owl:versionInfo` / `owl:versionIRI` are bumped only at a release cut._

### Changed
- Relabel `:StickCurtainWall` ("Stick"→"Stick Curtain Wall"), `:UnitisedCurtainWall` ("Unitised"→"Unitised
  Curtain Wall"), `:SemiUnitisedCurtainWall` ("Semi-unitised"→"Semi Unitised Curtain Wall"), and
  `:DeadLoadBracket` ("Dead load"→"Dead Load Bracket") to follow the labelling convention (label contains the
  spaced class name). Fixes duplicate `rdfs:label`s that collided with `:Stick` / `:Unitised` /
  `aec_domain_common:DeadLoad` (ROBOT `duplicate_label`, [RES-36]). No IRI or semantic change.

## [1.0.0]

Initial in-repo baseline (not yet cut as a GitHub release). No earlier released version to diff against.
