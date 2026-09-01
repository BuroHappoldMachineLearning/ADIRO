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
- **12 terms.** Class: `Organization`. Object properties: `assertsMetadataFor`, `assertsClient`,
  `assertsOriginator`. Datatype properties: `organizationName`, `supplementaryTitle`, `sheetNumber`,
  `numberOfSheets`, `planKey`, `dimensionUnits`, `assertsCrossReferenceNumber`. Annotation property:
  `extractionHint`.
- **`assertsCrossReferenceNumber` (2026-09-01).** A second identifier a title block prints for the same sheet
  from a different numbering system (design-team-internal, client/EDMS, sketch/site-advice) — evidenced by a
  four-project field-frequency survey, recurring in 3 of 4 sampled projects. String-valued, stored verbatim
  like `planKey`; no controlled vocabulary for the issuing system. See
  `docs/modularization/titleblock-field-survey-2026-09.md` §3.2. The same survey identified a second candidate —
  a contractor/consultant/engineer/architect organisation role, present in all four projects — which is
  **deliberately parked, not minted**, pending a team discussion on shape (§3.1 of the same document).
- **Naming convention:** value-bearing object properties are `asserts<Thing>`, not `has<Thing>` — a title block
  states a claim, not a verified fact, and the name makes that visible at every call site. It also keeps these
  terms obviously distinct from their `aec_drawing_metadata` counterparts.
- Pre-1.0 on purpose: the vocabulary is expected to break while the extraction work runs, and the domain
  placement recorded in this version is provisional (see below).

**Selection rule — only uncontested terms.** A term is in this version only if it has no counterpart in
`aec_drawing_metadata`. Everything that overlaps an existing `dm:` term (identifier, title, scale, paper size,
revision code, issue date, the three person roles, the status properties) is **deferred** and listed in the
TTL footer, because the sheet-level vs titleblock-level placement question is unresolved — see
`docs/modularization/titleblock-vocabulary-review.md` §2.1. Domains are `dm:Titleblock` and
`assertsMetadataFor` ranges over `dm:DrawingSheet`; both are **provisional** and flagged as such in the file.

**Withdrawn in review of PR #66 (2026-08-13):** `hasLegalOwner` — a title block does not normally express legal
ownership, so it is deferred pending the field-frequency survey and the agreed <40%-of-sheets rule.
`DocumentType` / `DocumentTypeScheme` / `hasDocumentType` — deferred to a later pass so the scheme can land
*with its concept values*; a controlled vocabulary with nothing in it cannot be used.

Also dropped as redundant and deliberately absent: `Sheet` (use `dm:DrawingSheet`), `Discipline` (use
`dcommon:Discipline`), `hasNorthPointOrientation` (use UC-07 `northArrowAngle`), `hasAnnotationBlock` (use
`dm:Legend`/`dm:Note`), `pageNumber`/`numberOfPages` (duplicate the sheet-level pair).
