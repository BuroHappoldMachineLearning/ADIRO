# Changelog — adiro_provenance

Per-module SemVer. See [../docs/contribute/versioning/](../docs/contribute/versioning/).
Format: [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Changed
- **`storageLocation` may be relative** ([#239](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/239)): a relative reference is resolved against the root of the dataset the data belongs to, which the data does not record, and is resolved before a public release, whose check accepts only absolute addresses on its allowed hosts. `Configuration`'s definition says again that a resolution is recorded on the coordinate frame it gives (`resolutionDpi`, in `adiro_geometry`).

### Added
- **The text read from a drawing** ([#238](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/238)). New class `TextReading` (an `InferredEntity`): the text a step read from a region, such as a title block, or from a whole page (`isReadingOf`), as printed and whether or not any of it was read as a field, in `readText`, with the language as the literal's language tag. A reading that read nothing has an outcome instead (`hasReadingOutcome`, a property of its own: `hasOutcome` keeps its domain `FieldAssertion`). New outcome value `Failed` (a step that did not complete; retried), for a field assertion or a reading, with the error in `errorMessage`, which a step that failed before producing anything records on itself. New `StepKind` (`RegionDetection`, `TextRecognition`, `FieldExtraction`) with `hasStepKind` on a step, so a step that found nothing is still known for what it looked for. Data that lists the outcome values may meet `Failed`, a fifth value.
- **The runs of an extraction and their configuration** ([#237](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/237)). An extraction run is a `prov:Activity`; each of its steps (detecting a region, reading text, extracting fields) is an `InferenceMeta` with the model it used, and is part of the run through `dcterms:isPartOf`. New class `Configuration` (a `prov:Entity`) with `configurationContent`: the settings a step used (a prompt, rendering settings, size limits), kept as text whose format ADIRO does not model and with no credentials in it, recorded with `prov:used`; identical content should be one individual. The typing stubs `dcterms:isPartOf` and `prov:startedAtTime` are declared, with no axioms. `InferenceMeta`'s definition describes steps and runs.

## [2.1.0] — 2026-10-27

### Added
- **Where a file was obtained from** ([#229](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/229)). `sourceLocation` records the address a `DrawingFile`'s bytes were obtained from, such as a public archive's download address or, when it is the only origin known, an address in an organisation's own storage. `storageLocation` still records where copies are kept. The origin no longer gets lost when a public file is copied into internal storage before processing. `sourcePage` records the catalogue or landing page that describes the file at its origin, which is often a more lasting address. Both take an `xsd:anyURI` and are related to DCAT and Dublin Core terms by `skos:closeMatch` (`dcat:downloadURL` and `dcterms:source`; `dcat:landingPage`).
- **A file made from another file points back to it**: the PROV-O typing stub `prov:wasDerivedFrom` is declared, and is used between two `DrawingFile`s (a format conversion, a page split out of a PDF). Only the original records a `sourceLocation`.
- Data checks in `data-validation/`: a warning for a file with no recorded origin, itself or through the files it was derived from; and, for a public release only (`validate_data.py --public-hosts FILE`), a violation for any `sourceLocation`, `sourcePage`, `storageLocation` or `acceptedUnder` that is not on the release's allowlist of public hosts (the release must drop it before publishing).

### Changed
- **`supersedes` takes effect when the superseding assertion is accepted** ([#221](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/221)). Its definition now says so: until then the earlier assertion stays in force, and an accepted assertion replaces every assertion it supersedes, directly or through others. A pending or rejected re-extraction no longer withdraws an accepted value. No term, domain or range changes; tooling that reads `supersedes` as an immediate withdrawal should follow the new rule.

## [2.0.0] — 2026-10-21

### Changed
- **BREAKING: renamed from `aec_provenance`** ([#171](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/171)). The module, its ontology IRI and the IRI of every term it defines now use `adiro_provenance` (`https://w3id.org/adiro/adiro_provenance`) instead of `aec_provenance`; the title says "ADIRO" instead of "AEC". Nothing else changes: the terms, their definitions and their axioms are those of `aec_provenance`'s final release, whose version this release follows with a MAJOR bump. Every release of the old module stays published at its own IRI and is named here with `owl:priorVersion`; its history is in [its changelog](aec_provenance.md). The example images are published under the new module's path. `migration/aec_to_adiro.ttl` maps each old term IRI to the new one, and `scripts/migrate_aec_to_adiro.py` rewrites a graph or a list of links. Downstream consumers need to move to the new IRIs, including the annotation tooling, which reads the class IRIs and the labelling annotations.

