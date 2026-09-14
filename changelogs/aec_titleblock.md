# Changelog — aec_titleblock

Per-module SemVer. See [../docs/contribute/versioning.md](../docs/contribute/versioning.md).
Format: [Keep a Changelog](https://keepachangelog.com/).

Design authority: [Discussion #64 — Building the ADIRO title-block TBox](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/64)
· tracked by [RES-89](https://bhmlrnd.youtrack.cloud/issue/RES-89).

## [Unreleased]

_Pending changes accumulate here. `owl:versionInfo` / `owl:versionIRI` are bumped only at a release cut._

> ### ⚠️ This module now declares no terms
>
> **Team decision, 2026-09-14:** `aec_drawing_metadata` is the single repository for drawing metadata, so new
> concepts land there rather than in a parallel module. All eight terms this module held were **relocated to
> `aec_drawing_metadata`** on that date, keeping their local names — see that module's changelog.
>
> Nothing was released from here, so no published IRI is invalidated by the move.
>
> **Open:** whether this file should be deleted outright rather than kept as an empty declaration. Deleting it
> also means removing the `catalog-v001.xml` entry, the `generate_docs.py` dependency-order entry, the
> `mkdocs.yml` nav entry, this changelog, the display JSON and the generated `docs/` artefacts. That was not
> part of the relocation decision, so the file is kept pending an explicit call —
> see `docs/modularization/aec_titleblock-build-plan.md` §1d.

### Added
- **New module `aec_titleblock` — initial version.** Ontology declaration under `https://w3id.org/adiro/aec_titleblock`
  at `0.1.0`, importing `aec_drawing_metadata`; provenance metadata (`dcterms:*`); registered in
  `src/catalog-v001.xml`, `scripts/generate_docs.py` dependency order and the `mkdocs.yml` nav.
- ~~**8 terms.** Class: `Organization`. Object properties: `assertsMetadataFor`, `assertsClient`,
  `assertsOriginator`. Datatype properties: `organizationName`, `dimensionUnits`,
  `assertsCrossReferenceNumber`. Annotation property: `extractionHint`.~~ **All relocated to
  `aec_drawing_metadata` 2026-09-14.**
- **`assertsCrossReferenceNumber` (2026-09-01, now `dm:assertsCrossReferenceNumber`).** A second identifier a
  title block prints for the same sheet from a different numbering system (design-team-internal, client/EDMS,
  sketch/site-advice) — evidenced by a four-project field-frequency survey, recurring in 3 of 4 sampled
  projects. String-valued, stored verbatim; no controlled vocabulary for the issuing system. See
  `docs/modularization/titleblock-field-survey-2026-09.md` §3.2. The same survey identified a second candidate —
  a contractor/consultant/engineer/architect organisation role, present in all four projects — which is
  **deliberately parked, not minted**, pending a team discussion on shape (§3.1 of the same document).
- **Naming convention:** value-bearing object properties are `asserts<Thing>`, not `has<Thing>` — a title block
  states a claim, not a verified fact, and the name makes that visible at every call site. Originally this also
  kept these terms distinct from their `aec_drawing_metadata` counterparts; **after the relocation that second
  reason inverts into a stronger one** — claim and fact now share a namespace, so the verb is the only thing
  telling `assertsClient` from `isCheckedBy`.
- Pre-1.0 on purpose: the vocabulary was expected to break while the extraction work ran, and it did.

**Selection rule — only uncontested terms.** A term is in this version only if it has no counterpart in
`aec_drawing_metadata`. Everything that overlaps an existing `dm:` term (identifier, title, scale, paper size,
revision code, issue date, the three person roles, the status properties) is **deferred** and listed in the
TTL footer, because the sheet-level vs titleblock-level placement question is unresolved — see
`docs/modularization/titleblock-vocabulary-review.md` §2.1. Domains are `dm:Titleblock` and
`assertsMetadataFor` ranges over `dm:DrawingSheet`; both are **provisional** and flagged as such in the file.

**Withdrawn 2026-09-11 and 2026-09-14, after the field survey:** `supplementaryTitle` (ISO 7200 §5.2.3),
`numberOfSheets` (§5.1.7), `planKey` (DIN SPEC 91391-1) and `sheetNumber` (§5.1.6). None appeared in any of the
four sampled projects, so none clears the agreed <40%-of-sheets rule — all were minted from a standards reading
rather than from drawings. Two points worth keeping visible:

- The **sheet-position concept is now absent entirely** rather than half-modelled: `numberOfSheets` went first
  and `sheetNumber` followed. Note ISO 7200 §5.1.6 is **mandatory** in that standard, so this is a deliberate,
  evidence-led departure from it — not an oversight.
- `planKey` is withdrawn as **unevidenced, not as wrong** — the surveyed corpus is UK/US projects and it is a
  German-practice field, so it may return when German projects are sampled.

Recorded in the TTL footer §(a3).

**Withdrawn in review of PR #66 (2026-08-13):** `hasLegalOwner` — a title block does not normally express legal
ownership, so it is deferred pending the field-frequency survey and the agreed <40%-of-sheets rule.
`DocumentType` / `DocumentTypeScheme` / `hasDocumentType` — deferred to a later pass so the scheme can land
*with its concept values*; a controlled vocabulary with nothing in it cannot be used.

Also dropped as redundant and deliberately absent: `Sheet` (use `dm:DrawingSheet`), `Discipline` (use
`dcommon:Discipline`), `hasNorthPointOrientation` (use UC-07 `northArrowAngle`), `hasAnnotationBlock` (use
`dm:Legend`/`dm:Note`), `pageNumber`/`numberOfPages` (duplicate the sheet-level pair).
