# `aec_titleblock` — what to mint next, evidence from Ahmed Zaalouk's field survey

**Status:** `assertsCrossReferenceNumber` **decided and implemented** (2026-09-01); the four organisation-role
candidates in §3.1 are **parked for future discussion**
**Author:** drafted 2026-09-01, following PR [#66](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/66) review round 1
**Answers:** the field-frequency survey that `docs/ai/worklog.md` (2026-08-13 entry) and the TTL footer's
withdrawal of `hasLegalOwner` both said was still pending
**Also relevant to:** Ahmed Zaalouk's PR #66 comment (2026-08-19) deferring detailed review of the organisation
properties until he could "take a look at the title blocks" — this is that look
**Scope:** which `tb:` terms to add in the *next* pass, not a re-litigation of the 11 terms already shipped or of
decision 1 (Option 1, resolved — see `titleblock-placement-option1-plan.md`)

> **Project identity.** The source spreadsheet names four real BH projects. This document refers to them only as
> **Project A–D**, consistently, so it can be cited outside project-restricted channels. The mapping is not
> reproduced here — anyone needing to trace a row back to a project should go to the spreadsheet directly, which
> is client/project-restricted material and stays out of this public repo.

---

## 1. The data

`Title block dataset/title block.xlsx` (Ahmed Zaalouk) — four real BH projects (referred to below as **Project
A–D**), each sheet's title-block fields hand-catalogued with a name, synonyms, a description, and a
**frequency**: how many sampled sheets on that project print the field.

| Project | Sampled title blocks (≈ max frequency) | Distinct fields catalogued |
| --- | --- | --- |
| Project A | 215 | 24 |
| Project B | 94 | 17 |
| Project C | 30 | 4 |
| Project D | 10 | 13 |

Project A and Project D are heterogeneous samples (frequency varies field to field — some fields are on every
sheet, some on a handful). Project B and Project C read as **one drawing template each** — every catalogued
field sits at the project's maximum frequency, so presence there means "in the template", not "independently on
~100% of sheets". That distinction matters below: a field appearing in *only* Project B or *only* Project C at
100% is one data point, not a strong one, no matter how large the percentage looks.

**Method applied:** for each field, frequency ÷ that project's own maximum frequency, then look at how many of
the **four independent projects** the field (or an obvious synonym) appears in at all. Breadth across projects is
the stronger signal here — a field that only one template happens to print is weak evidence for a general-purpose
ontology term, however high its in-project percentage.

**Applying the acceptance criterion already agreed** (Discussion #61, Zaalouk 1 / Alessio, recorded in the build
plan §5): *defer any field appearing on <~40% of sampled sheets.* Read per-project below; the crosscheck is
breadth.

---

## 2. What's already covered — the survey corroborates the shipped design, no action needed

Cross-checking the survey against `src/aec_drawing_metadata.ttl` and the shipped `tb:` terms first, because a
"why isn't there a term for X" question is cheaper to close than to leave open.

| Survey field(s) | Covered by | Projects | Verdict |
| --- | --- | --- | --- |
| Project / Building / Site (100%, A) · Project Title (100%, B) · Project Name (100%, D) | `dm:Project` + `dm:projectName` + `dm:belongsToProject` | 3/4 | **Already modelled.** Same shape as decision 1 (Option 1) — no `tb:` counterpart needed |
| Component / Package (100%, B) | `dm:DrawingPackage` + `dm:packageName` + `dm:belongsToPackage` | 1/4 | **Already modelled** |
| Department (5.1%, A) · Discipline (100%, B, same template field as Department) | `dcommon:Discipline` (per `titleblock-vocabulary-review.md` §2.3) | 2/4 | **Already dropped as redundant** — footer (b). Survey does not change this; 5.1% on the one heterogeneous sample confirms it, if anything |
| Client (100%, B and D) | `tb:assertsClient` | 2/4 | **Already shipped** |
| Architect / Design Practice (95.8%, A) | `tb:assertsOriginator` | 1/4, near-universal within it | **Already shipped** |
| Drawn / Drawn By (100% in all four) · Checked / Checked by (22.8–100%) | `dm:isAuthoredBy` / `dm:isCheckedBy` (Option 1) | 4/4 | **Already resolved, reused from `dm:`** |
| Date (100%, A & D) · Rev. (18.6–100%) · Scale (100% everywhere it's a column) · Drawing Number / Description / Title / Sheet Title (37.7–100%) | `dm:issueDate` / `dm:revisionCode` / `dm:hasScale` / `dm:drawingIdentifier` / `dm:drawingTitle` (Option 1) | 4/4 | **Already resolved, reused from `dm:`** |
| Notice / General Notes (94–100%) · Legend (100%, D) | `dm:Note` / `dm:TextualNote` / `dm:Legend` via `dm:contains` | 2/4 | **Already modelled** as page regions, footer (b) — flag to the extraction pipeline, not an ontology gap |
| ~~key plan (94–100%)~~ | ~~`dm:Note` / `dm:TextualNote`~~ → **`dm:KeyPlan`** | 2/4 | **CORRECTED 2026-09-14 — this row was wrong.** A key plan is a *locator diagram*, not a notes block; it was lumped in above on the strength of Project B's description (which describes copyright statements — most likely a mislabelled cell). Project D's description is the accurate one: "denotes the location of the drawing in plan", value type *Sketch*. Minted as `dm:KeyPlan`, a region class beside `Legend` — see the build plan §1c. Real evidence is **one solid project + one doubtful**, not a clean 2/4 |
| Revision / Issue History / Issue-Revision Schedule (20.5–100%) | `dm:DrawingRevision` (the class, not a single field) | 3/4 | **Already modelled** as structure |

Nine of the survey's field groups need nothing new. That is useful signal on its own: it means the module's
current 11 terms plus the Option 1 reuse decision already account for the majority of what real title blocks
print, and the gaps below are the genuine remainder rather than an oversight.

---

## 3. Two genuine gaps, both crossing multiple projects

Neither of these appeared in the original 73-term brainstorm (Discussion #61 §11.1) or in the ISO 7200 pass —
they surface only because this is real drawings, not a standards reading. That is exactly the kind of evidence
the team asked for before deciding `hasLegalOwner` and the acceptance criterion.

### 3.1 A second organisation role, beyond client and originator — **parked for future discussion**

| Field | Project | Frequency |
| --- | --- | --- |
| Consultant | A | 56 / 215 = 26.0% |
| Infrastructure + Engineers | B | 94 / 94 = 100% (template) |
| Executive Architect | B | 94 / 94 = 100% (template) |
| Architect of Record | B | 94 / 94 = 100% (template) |
| Contractor | C | 30 / 30 = 100% (template) |
| Contractor | D | 10 / 10 = 100% |

**Breadth: 4/4 projects**, under five different labels. That is the strongest cross-project signal in the whole
survey, and it lines up with the thing Zaalouk himself flagged on PR #66 (2026-08-19) as needing "a robust
analysis" before he could review the organisation properties. `tb:Organization` and the `asserts<Thing>` naming
pattern already exist and generalise cleanly — the open question is **shape, not whether**:

- **One new property per role**, mirroring `assertsClient` / `assertsOriginator` — e.g. `assertsContractor`,
  `assertsEngineer`, `assertsArchitect`, `assertsConsultant`. Consistent with the existing naming convention;
  risks the same fragmentation the `DocumentType` withdrawal was trying to avoid if Project B's three-way split
  (Executive Architect / Architect of Record / Infrastructure + Engineers) turns out to be real rather than one
  project's house style.
- **One generic property**, e.g. `assertsInvolvedOrganization`, with the specific role captured as a
  `skos:altLabel`-style annotation or left to `extractionHint` rather than the property name. Fewer terms, but
  loses the "the property name states the claim" clarity that was the whole point of the `asserts*` convention.

Project A's "Consultant" sits below the 40% line in isolation (26.0%), but it is corroborated by three other
projects expressing the same underlying concept at 100% of their own templates, under different names. Recommend
weighing this as one gap with four pieces of evidence, not four independent fields each individually below
threshold.

**Decided (2026-09-01): not this pass.** `tb:assertsOriginator` already covers "who produced this drawing" for
the first pass, and four candidate role names (`assertsContractor`, `assertsEngineer`, `assertsArchitect`,
`assertsConsultant`) are identified but **deliberately not minted now** — parked for a future discussion on
shape (one property per role vs. one generic property + role annotation) rather than decided by default here.

### 3.2 A second (or third) drawing-numbering system for the same sheet — **decided, implemented**

| Field | Project | Frequency |
| --- | --- | --- |
| SA/SK No. | A | 132 / 215 = 61.4% |
| Client Ref. Drawing Number | A | 30 / 215 = 14.0% |
| Drawer Number | A | 29 / 215 = 13.5% |
| Aconex Document Number | B | 94 / 94 = 100% (template) |
| Design team drawing number | B | 94 / 94 = 100% (template) |
| SK | C | 30 / 30 = 100% (template) |

**Breadth: 3/4 projects.** The pattern: `dm:drawingIdentifier` already captures *a* drawing number, but real
sheets often carry a **second** number from a different system — the design team's own numbering (distinct from
the originator's), an EDMS/CDE document number (Aconex), or a sketch/site-advice reference (SA/SK). This is not
in the original 73-term list; the closest existing candidate, `hasTechnicalReference` (ISO 7200 §5.3.3, *who to
contact* — a `Person`), is a different concept and was already correctly rated "do not implement" (Discussion
#61 §11.2, manufacturing heritage). Project A's SA/SK No. alone clears the 40% line (61.4%); Aconex Document
Number and Design team drawing number are 100% of Project B's single-project template each, which — per the same
caution as §3.1 — is one data point, not three.

**Decided (2026-09-01): mint `tb:assertsCrossReferenceNumber`** — a single datatype property (domain
`dm:Titleblock`, range `xsd:string`), covering SA/SK No. / Aconex Document Number / Design team drawing number /
Client Ref. Drawing Number as `skos:altLabel`s, consistent with the `planKey` precedent (stored whole and
verbatim, not parsed). The *which system issued it* distinction is left to `extractionHint` rather than a
controlled vocabulary — because an empty scheme was exactly the objection that withdrew `DocumentType` in review
round 1, and populating one properly is its own pass. See `src/aec_titleblock.ttl` and
`changelogs/aec_titleblock.md` for the shipped term.

---

## 4. Fields surveyed and **not** proposed, with the reason stated

Per the "record decisions deferred or rejected, not only work done" convention (`AGENTS.md`, worklog rules) —
so nobody re-derives this from the spreadsheet again.

| Field | Frequency | Why not (yet) |
| --- | --- | --- |
| Level | A, 59/215 = 27.4% | Below 40%, single project. Plausibly `dm:` sheet-location material rather than a title-block content field — worth a CQ before minting, not a survey-only decision |
| Client Ref. Drawing Number (as its own term) | A, 14.0% | Below 40% on its own; folded into the §3.2 gap as one of several labels for the same underlying concept rather than proposed separately |
| Drawer Number | A, 13.5% | Below 40%, single project, and its own description says archive/storage location — a records-management fact about the physical original, not something a title block *asserts* about the drawing's content |
| Client DRG No. | A, 1.4% | Noise-level frequency, single project |
| Note, CI/sfb, Preliminary, Contract, Working DRG, ISSUE, No. | A, all ≤1.9% | Noise-level; several are annotated "UNKNOWN" in the source data by its author. Not evidence of anything |

---

## 5. Questions for the team

1. For §3.1: start with `assertsContractor` only (the two-project verbatim match), or take Project B's
   three-role split as real and design for it now? If real, is Executive Architect vs Architect of Record vs
   Infrastructure + Engineers a role distinction ADIRO should encode, or is it one project's contract structure
   that a generic `assertsConsultant` would cover just as well? — **parked, not decided this pass.**
2. Is a **four-project spreadsheet** sufficient evidence to mint from, in general, or does the team want a wider
   sampling pass before further gaps are built on it? (Noting Project B and Project C are each one template, not
   independent sheets — see §1.)
3. Does `Level` (§4) belong in this module at all, or is it sheet/storey metadata that belongs in
   `aec_drawing_metadata` alongside `DrawingSheet`, closer to how `belongsToProject` works?

---

## 6. Recommendation / outcome

Two candidates were identified, both with multi-project evidence that nothing in the original 73-term brainstorm
anticipated. **Decided 2026-09-01:**

- **`tb:assertsCrossReferenceNumber`** (§3.2) — minted this pass. Narrowest defensible cut: one property, verbatim
  labels kept as `skos:altLabel`s, no controlled vocabulary.
- **The organisation-role gap** (§3.1) — `assertsContractor` / `assertsEngineer` / `assertsArchitect` /
  `assertsConsultant` are identified as candidates but **not minted this pass**. `tb:assertsOriginator` already
  covers the general case for now; the four more specific roles are parked for a future discussion on shape
  (named per role vs. one generic property), for the same reason `DocumentType` was withdrawn in review round 1
  — better to land a smaller, uncontested set than to mint terms a second review round has to walk back.

Everything else the survey turned up either confirms the shipped design needs no change (§2) or falls below the
team's own 40% threshold with no cross-project corroboration (§4).

---

## 7. Vocabulary considered and **not** minted — the full record

> **Rehomed here 2026-09-14.** This record lived in the footer of `src/aec_titleblock.ttl`. That module was
> deleted when its terms moved into `aec_drawing_metadata`, and this is the only copy — so it is kept here
> rather than lost with the file. It is the reasoning for terms a reviewer may well ask about; a rejected
> option is the most expensive thing to rediscover.

All term names below are *proposals that were never minted*, except where a `dm:` target is named.

### 7.1 Resolved 2026-08-19 (Option 1) — reuse `aec_drawing_metadata` directly

These are not missing; they already exist and are used as-is. Extraction writes straight onto
`dm:DrawingSheet` / `dm:DrawingRevision`, with **no "unvalidated claim" staging layer** — a trade-off accepted
explicitly, not by default. (The 2026-09-14 relocation makes the *placement* question moot, since there is no
longer a second module to duplicate into, but this still explains why no `dm:asserts*` twin exists for these
ten.)

| Proposed | Use instead | Attaches to |
| --- | --- | --- |
| `identificationNumber` | `dm:drawingIdentifier` | `DrawingSheet` |
| `title` | `dm:drawingTitle` | `DrawingSheet` |
| `scale` | `dm:hasScale` | `DrawingSheet` |
| `paperSize` | `dm:sheetSize` | `DrawingSheet` |
| `revisionIndex` | `dm:revisionCode` | `DrawingRevision` |
| `dateOfIssue` | `dm:issueDate` | `DrawingRevision` |
| `createdBy` | `dm:isAuthoredBy` | `DrawingRevision` → `Person` |
| `checkedBy` | `dm:isCheckedBy` | `DrawingRevision` → `Person` |
| `approvedBy` | `dm:isApprovedBy` | `DrawingRevision` → `Person` |
| `status` | `dm:hasStatusCode` | `DrawingRevision` → `StatusCode` |

### 7.2 Withdrawn after review of PR #66 (2026-08-13)

- **`hasLegalOwner`** — Alessio Lombardi and Tianyang Huang both observe that a title block does not normally
  express legal ownership. Deferred pending the field survey; under the agreed `<40%` rule it is unlikely to
  return. ISO 7200 §5.1.2 defines it, but **the standard is not the evidence — the drawings are.**
- **`DocumentType` / `DocumentTypeScheme` / `hasDocumentType`** — withdrawn to land complete. A controlled
  vocabulary with no concepts in it cannot be used, which was the review objection, and the definition needed
  tightening. Populating it also touches the standards-licensing question (listing DIN 1356-1 *Planart* values),
  worth deciding rather than rushing.

### 7.3 Withdrawn 2026-09-11 and 2026-09-14, on this survey's evidence

None appeared in **any** of the four sampled projects, so none clears the `<40%` rule. All were minted from a
standards reading rather than from drawings — exactly the basis §7.2 rejected.

- **`supplementaryTitle`** (ISO 7200 §5.2.3, optional) — stacked title lines do occur, but no surveyed sheet
  separated them into a distinct field; the surveyed title fields map to `dm:drawingTitle`.
- **`numberOfSheets` and `sheetNumber`** (ISO 7200 §5.1.7 and §5.1.6) — the "Sheet 3 of 7" pair. The first went
  2026-09-11, the second followed 2026-09-14, so the sheet-position concept is absent **entirely** rather than
  half-modelled. Note **§5.1.6 is mandatory in ISO 7200** — a deliberate, evidence-led departure from the
  standard, not an oversight. If ISO 7200 conformance becomes a stated goal, this is the decision to revisit.
- **`planKey`** (DIN SPEC 91391-1 *Plankopf* composite code) — a German-practice field; the surveyed corpus is
  UK/US projects, so it may well return once German projects are sampled. Withdrawn as **unevidenced, not as
  wrong.**

### 7.4 Dropped as redundant, per the vocabulary review — do not re-add

| Proposed | Use instead |
| --- | --- |
| `Sheet` | `dm:DrawingSheet` |
| `Discipline` | `dcommon:Discipline` — a class hierarchy, giving sub-discipline rollup a flat SKOS scheme would lose. Referencing it needs an `owl:imports` of `aec_domain_common`, which pulls the whole module chain; that import question is unresolved, so nothing references `dcommon:` yet |
| `hasNorthPointOrientation` | UC-07 `northArrowAngle` (drawing-level) |
| `hasAnnotationBlock` | `dm:Legend` / `dm:Note` with `dm:contains` |
| `pageNumber` / `numberOfPages` | duplicated the sheet-position pair, itself withdrawn entirely in §7.3 |

### 7.5 Still to come, now targeting `aec_drawing_metadata`

- The remaining SKOS schemes and their concepts; the extension properties.
- The **extraction-provenance layer**, blocked on the RDF-star vs reification decision. An extraction timestamp
  must be included when it lands — its absence was a real gap found by comparison with DANO.
- **Parked 2026-09-01** pending a team discussion on shape: the organisation-role gap found in all four surveyed
  projects — `assertsContractor`, `assertsEngineer`, `assertsArchitect`, `assertsConsultant`.
  `dm:assertsOriginator` covers the general case for now (§3.1, §5).
