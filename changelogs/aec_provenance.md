# Changelog — aec_provenance

Per-module SemVer. See [../docs/contribute/versioning/](../docs/contribute/versioning/).
Format: [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- **The outcome and the acceptance of a field assertion** ([#187](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/187)): `AssertionOutcome` (`Empty`, `Illegible`, `NotPrinted`, `NotFound`; what a search found when it found no value) with `hasOutcome`, and `AcceptanceStatus` (`Pending`, `Accepted`, `Rejected`) with `hasAcceptance`, `acceptedBy`, `acceptedAt` and `acceptedUnder`; `supersedes` between assertions. An assertion has a value or an outcome, never both; only an accepted assertion that has a value is promoted by `mapsToFieldProperty`, whose comment says so. `supersedes` is related to `prov:wasRevisionOf` by `skos:closeMatch`.
- **The file a drawing is stored in, and its pages** ([#192](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/192)): `DrawingFile` (a reference to a document, identified by its content hash) and `FilePage` (one page of a file, counted from 1), with the properties that describe them (`fileName`, `mediaType`, `contentHash`, `hashAlgorithm`, `storageLocation`, `fileCreatedAt`, `fileModifiedAt`, `fileCreatedBy`, `fileModifiedBy`, `pageCount`, `fileSize`; `belongsToFile`, `pageNumber`, `displayWidthPt`, `displayHeightPt`, `pdfRotationDeg`). Both are `prov:Entity` and subclasses of the ISO 21597-1 (ICDD) `Document` and, for the page, nothing more; each property is related to ICDD, Dublin Core terms and DCAT by `skos:closeMatch`, never as a subproperty.
- **`Party`, `Person` and `Organisation`** ([#192](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/192)), moved here from `aec_drawing_metadata` (their IRIs change): `Party` is abstract, the disjoint union of the other two, and a `prov:Agent`; each is a subclass of its ISO 21597-1 counterpart. Downstream consumers that read a person or an organisation by IRI need to adjust.
- **A human annotation is an inference step performed by a person** ([#192](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/192)): the comments of `InferredEntity`, `inferredBy` and `hasConfidence` say that the producing step can be a model or a person (an `aprov:Person`, with no `inferredWith`, and a confidence only if one is given). No term changes.
- **ISO 21597-1 typing stubs** (`ct:Document`, `ct:Party`, `ct:Person`, `ct:Organisation`, edition 1), declared locally, with no `owl:imports`; `rdfs:isDefinedBy` points at the published `Container.rdf`, because the namespace address itself does not answer.

## [1.0.1] — 2026-10-19

### Changed
- **`assertedBy`'s example reworded** ([#162](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/162), [#166](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/166)): the comment gave "a sheet-level scale in the title block versus a per-layout scale in a layout corner" as an example of one field kind asserted from different regions. The scale field kind is promoted to the sheet's `drawingScale`, and no field kind exists for a layout's caption scale, so the example now reads "a sheet's scale read from the title block versus the same sheet's scale read from a general note". Comment only; no term, axiom or domain changes.

## [1.0.0] — 2026-10-09

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
  - **`InferredEntity`** — a superclass of `FieldAssertion` for anything ADIRO infers or extracts that carries
    its own provenance and confidence. `hasInferenceMeta` and `hasConfidence` now take it as their `rdfs:domain`
    (previously `FieldAssertion`), so a spatial localisation (`aec_geometry:BoundingBox`,
    [#90](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/90)) can carry the same provenance/confidence
    machinery as a value claim. This also resolves the confidence-on-geometry domain concern raised in the UC-03
    review. Refines terms added earlier in this same unreleased cycle.

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
  directly. ADIRO ships **no** DAnO crosswalk; the correspondence with DAnO's equivalent provenance terms is
  documentation only - see the [DAnO comparison](../docs/specification/design-decisions/dano-comparison.md).

