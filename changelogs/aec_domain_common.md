# Changelog — aec_domain_common

Per-module SemVer. See [../docs/contribute/versioning.md](../docs/contribute/versioning.md).
Format: [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

_Pending changes accumulate here. `owl:versionInfo` / `owl:versionIRI` are bumped only at a release cut._

### Added
- Ontology-header provenance metadata (`dcterms:title`, `dcterms:description`, `dcterms:license`, `dcterms:creator`, `dcterms:publisher`) for FAIR / registry readiness (#50).

### Changed
- Relabel `:DeadLoad` ("Dead load"→"Dead Load") to follow the labelling convention; also de-duplicates the
  `rdfs:label` vs `aec_facade_domain:DeadLoadBracket` (ROBOT `duplicate_label`, [RES-36]). No IRI or semantic change.

## [1.0.0]

Initial in-repo baseline (not yet cut as a GitHub release). No earlier released version to diff against.
