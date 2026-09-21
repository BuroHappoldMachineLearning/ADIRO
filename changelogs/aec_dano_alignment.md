# Changelog — aec_dano_alignment

Per-module SemVer. See [../docs/contribute/versioning/](../docs/contribute/versioning/).
Format: [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

_Pending changes accumulate here. `owl:versionInfo` / `owl:versionIRI` are bumped only at a release cut._

### Added
- **New optional compatibility layer** mapping ADIRO to the Drawing Analysis Ontology
  ([DAnO](https://w3id.org/dano)), settling [#77](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/77).
  `skos:closeMatch` from `aprov:InferenceMeta`, `aprov:inferredBy`, `aprov:inferredWith`, `aprov:inferredFrom`,
  `aprov:inferredAt`, `aprov:hasConfidence` and `dm:depicts` to their `dano:` counterparts.
- **No ADIRO core module references DAnO.** The crosswalk lives here and nothing imports this file, so a
  consumer opts in by loading it. This module `owl:imports` `aec_provenance` and `aec_drawing_metadata`, not
  the other way round.
- **All mappings are annotation-level.** No `rdfs:subPropertyOf` alignment is asserted to any DAnO term:
  DAnO's `inferred*` are datatype properties while ADIRO's are object properties (a sub-property axiom across
  that boundary is ill-typed and outside OWL 2 DL), `dano:inferredAt` ranges over `xsd:date` which is disjoint
  from ADIRO's `xsd:dateTime`, and `dano:hasConfidence` / `dano:depicts` carry domains that would entail ADIRO
  individuals are DAnO drawing elements. The DAnO terms are not declared locally - they appear only as
  annotation values. Full rationale:
  [DAnO comparison](../docs/design-decisions/dano-comparison.md).

### Notes
- `dano:isDepictedBy` is intentionally unmapped until ADIRO mints an inverse for `dm:depicts`; the name is
  UC-06's call (its ORSD proposes `isDepictedOn`).
- DAnO is CC BY 4.0, from RUB Informatik im Bauwesen. Only its IRIs are referenced; no DAnO axiom is copied.

## [1.0.0]

Initial in-repo baseline (not yet cut as a GitHub release).
