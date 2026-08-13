# Changelog — aec_titleblock

Per-module SemVer. See [../docs/contribute/versioning.md](../docs/contribute/versioning.md).
Format: [Keep a Changelog](https://keepachangelog.com/).

Design authority: [Discussion #64 — Building the ADIRO title-block TBox](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/64)
· tracked by [RES-89](https://bhmlrnd.youtrack.cloud/issue/RES-89).

## [Unreleased]

_Pending changes accumulate here. `owl:versionInfo` / `owl:versionIRI` are bumped only at a release cut._

### Added
- **New module `aec_titleblock` — initial version.** Ontology declaration under `https://w3id.org/adiro/aec_titleblock`
  at `0.1.0`, importing `aec_drawing_metadata`; provenance metadata (`dcterms:*`); registered in
  `src/catalog-v001.xml`, `scripts/generate_docs.py` dependency order and the `mkdocs.yml` nav.
- **14 terms.** Classes: `Organization`, `DocumentType` (+ `DocumentTypeScheme`). Object properties:
  `assertsMetadataFor`, `hasClient`, `hasLegalOwner`, `hasOriginator`, `hasDocumentType`. Datatype properties:
  `organizationName`, `supplementaryTitle`, `sheetNumber`, `numberOfSheets`, `planKey`, `dimensionUnits`.
  Annotation property: `extractionHint`.
- Pre-1.0 on purpose: the vocabulary is expected to break while the extraction work runs, and the domain
  placement recorded in this version is provisional (see below).

**Selection rule — only uncontested terms.** A term is in this version only if it has no counterpart in
`aec_drawing_metadata`. Everything that overlaps an existing `dm:` term (identifier, title, scale, paper size,
revision code, issue date, the three person roles, the status properties) is **deferred** and listed in the
TTL footer, because the sheet-level vs titleblock-level placement question is unresolved — see
`docs/modularization/titleblock-vocabulary-review.md` §2.1. Domains are `dm:Titleblock` and
`assertsMetadataFor` ranges over `dm:DrawingSheet`; both are **provisional** and flagged as such in the file.

Also dropped as redundant and deliberately absent: `Sheet` (use `dm:DrawingSheet`), `Discipline` (use
`dcommon:Discipline`), `hasNorthPointOrientation` (use UC-07 `northArrowAngle`), `hasAnnotationBlock` (use
`dm:Legend`/`dm:Note`), `pageNumber`/`numberOfPages` (duplicate the sheet-level pair).
