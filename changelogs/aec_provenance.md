# Changelog — aec_provenance

Per-module SemVer. See [../docs/contribute/versioning/](../docs/contribute/versioning/).
Format: [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- **New foundational, domain-neutral module** for reified assertions with provenance and confidence
  ([Discussion #72](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/72)). Introduces:
  - Classes `FieldAssertion` (a reified value-claim about a field kind, carrying its own provenance) and
    `InferenceMeta` (what produced an inference, from where, when).
  - Object properties `assertsFieldKind`, `assertedBy` (source-region provenance), `hasValueEntity`,
    `hasInferenceMeta`, `inferredBy`, `inferredWith`, `inferredFrom`.
  - Datatype properties `hasLiteralValue`, `capturedCaption`, `hasConfidence` (decimal in [0,1], on the
    assertion individual - no RDF-star needed), `inferredAt`.
  - **PROV-O alignment** (`inferredBy` ⊑ `prov:wasAttributedTo`, `inferredFrom` ⊑ `prov:wasDerivedFrom`,
    `inferredAt` ⊑ `prov:generatedAtTime`, model as `prov:Agent`). PROV-O terms are declared locally
    (not `owl:imports`) so reasoning stays offline via `catalog-v001.xml`. PROV-O suggested by Tianyang Huang.
  - Annotation properties for field-kind schemes defined by importing modules: `expectedRange` (a field
    kind's expected value type) and `mapsToFieldProperty` (the canonical property a validated assertion
    promotes to). First consumed by `aec_drawing_metadata`'s `TitleblockFieldScheme`.

  `owl:versionInfo` / `owl:versionIRI` are bumped only at a release cut.

## [1.0.0]

Initial in-repo baseline (not yet cut as a GitHub release). No earlier released version to diff against.
