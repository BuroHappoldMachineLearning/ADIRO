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

### Changed
- **PROV-O alignment re-seated across two classes.** It previously hung entirely off `InferenceMeta`
  (`inferredBy` ⊆ `prov:wasAttributedTo`, `inferredFrom` ⊆ `prov:wasDerivedFrom`, `inferredAt` ⊆
  `prov:generatedAtTime`). All three of those PROV-O properties carry `rdfs:domain prov:Entity`, so the
  alignment entailed that the *metadata record* was the thing attributed, derived and generated — and
  PROV-O declares `prov:Entity` **`owl:disjointWith`** `prov:Activity`, so it typed `InferenceMeta` as
  the opposite of what it is. Now: `FieldAssertion` ⊆ `prov:Entity`, `InferenceMeta` ⊆ `prov:Activity`,
  `hasInferenceMeta` ⊆ `prov:wasGeneratedBy`, `inferredBy` ⊆ `prov:wasAssociatedWith`, `inferredWith`
  and `inferredFrom` ⊆ `prov:used`, `inferredAt` ⊆ `prov:endedAtTime`. Verified by reasoning over the
  module merged with the real PROV-O vocabulary. Stub set changed accordingly.

### Added
- **`assertedAbout`** — the subject a claim is *about*, as distinct from `assertedBy`, the region it was
  *read from*. Without it `mapsToFieldProperty` named a property but nothing named the individual to hang
  it on, and promotion was not expressible: targets span `Titleblock`, `DrawingSheet`, `DrawingRevision`
  and `DrawingPackage`, and a sheet has many revisions. No `rdfs:range` asserted, deliberately.

### Notes
- This module deliberately mentions **no** external vocabulary other than PROV-O, which it aligns to
  directly. The crosswalk to DAnO's equivalent provenance terms lives in the optional
  `aec_dano_alignment` module - see [DAnO comparison](../docs/design-decisions/dano-comparison.md)
  for why those mappings are annotation-level only.

## [1.0.0]

Initial in-repo baseline (not yet cut as a GitHub release). No earlier released version to diff against.
