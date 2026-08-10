# Changelog — aec_drawing_metadata

Per-module SemVer. See [../docs/contribute/versioning.md](../docs/contribute/versioning.md).
Format: [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

_Pending changes accumulate here. `owl:versionInfo` / `owl:versionIRI` are bumped only at a release cut._

### Added
- Ontology-header provenance metadata (`dcterms:title`, `dcterms:description`, `dcterms:license`, `dcterms:creator`, `dcterms:publisher`) for FAIR / registry readiness; clears the ROBOT `report` `missing_ontology_*` ERRORs (#50).

### Removed
- `owl:imports <http://www.w3.org/2002/07/owl#>` — importing the OWL vocabulary *as an ontology* made the merged suite non-OWL-2-DL (illegal `owl:topDataProperty` range axiom) and blocked the reasoner; removing it makes the suite consistent / DL-valid (#55). No semantic change.

## [2.0.0]

Current in-repo baseline (not yet cut as a GitHub release). Includes the [RES-37](https://bhmlrnd.youtrack.cloud/issue/RES-37) fix aligning
`owl:versionIRI` with `owl:versionInfo`. No earlier released version to diff against.
