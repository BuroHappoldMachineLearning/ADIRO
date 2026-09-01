# Title-block vocabulary — review against the use cases and against DANO

**Date:** 2026-08-11 · **Issue:** [RES-89](https://bhmlrnd.youtrack.cloud/issue/RES-89) · **Branch:** `res-89-aec-titleblock-tbox`
**Reviews:** the 73 proposed terms in [Discussion #61 §11.1](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/61)
**Against:** `docs/uc-orsd/` (UC-01, UC-03, UC-06, UC-07) and [DANO](https://rub-informatik-im-bauwesen.github.io/dano/)

## Why this document exists

The proposed title-block vocabulary was assessed for *internal* redundancy in Discussion #61 §11.1 (29 core, 19
useful, 20 marginal, 5 redundant). This document applies two **external** tests that assessment could not:

1. **Do the terms serve the use cases?** The repo follows LOT — `Use Case → Information Needs → Functional
   Requirements → Competency Questions → OWL Terms` — and claims *"forward traceability (every OWL term traces
   back to a use case need)"* (`docs/uc-orsd/README.md` §1).
2. **Has someone already built the drawing-analysis half of this?** DANO is a published, CC BY 4.0 ontology for
   exactly computer-vision-based drawing analysis.

Both tests found things the internal review could not. **The first finding below is the most consequential
thing in this document and is not a redundancy question at all.**

---

## 1. Headline findings

| # | Finding | Consequence |
| --- | --- | --- |
| **1** | **UC-01 already implements title-block search, and it made the *opposite* architectural decision to RES-A-9 finding 2 — deliberately, and under review.** | The §1.1 reconciliation is not "reconcile with terms that drifted in". It is "choose between two reviewed architectures". Reframes pass 0 entirely |
| **2** | **~40 of the 73 terms have no competency question behind them, from any use case.** | Either the extraction work needs its own ORSD, or the vocabulary should be cut to what the use cases demand. Currently it violates the repo's own stated traceability rule |
| **3** | `Discipline` would duplicate `dcommon:Discipline`, a class hierarchy UC-01 already reuses — and a SKOS scheme would *lose* the sub-discipline reasoning UC-01 chose it for | 🟢 Core → 🔴 Redundant |
| **4** | `hasNorthPointOrientation` duplicates UC-07's `northArrowAngle`, which is better specified | 🟠 Marginal → 🔴 Redundant |
| **5** | `scale` duplicates `dm:hasScale`; the scale story is already two properties by design (string + numeric ratio) | 🟢 Core → 🔴 Redundant (the *field* is core; the *term* is not) |
| **6** | DANO already models the extraction-provenance layer (§10) — including a timestamp ADIRO omits — and its `DrawingElementMeta` is a worked reification pattern | Bears directly on the pass-5 blocker |
| **7** | `DocumentType` risks repeating a mistake UC-01 already corrected (its `DrawingType` → `LayoutContentType` deprecation) | Keep, but state explicitly that it is a different axis |

---

## 2. Part A — against the use cases

### 2.1 The architectural contradiction (finding 1)

UC-01 is **"Titleblock-Based Drawing Search"**, priority XL, and marked *"Done already"* in the prioritisation
matrix. Its ORSD contains this design note:

> **Design note — Titleblock as visual region vs titleblock data:** The existing `metadata:Titleblock` class
> models the *visual region* on a sheet (for CV annotation). The *information* conventionally found inside it
> (`drawingIdentifier`, `drawingTitle`, …) is attached as datatype properties directly on `DrawingSheet`. The two
> layers coexist independently: a sheet has a drawing number whether or not its visual Titleblock region has been
> bounded in annotation.

That is the **direct opposite** of RES-A-9 finding 2 and Discussion #64 §7, which require *"Domain is
`Titleblock`, never `Document`"*.

**This is not drift.** UC-01 v0.3's changelog records the sheet-level placement as an alignment decision taken in
review (`@alelom`'s PR review, item G2: *"Datatype properties attached directly to `DrawingSheet` — no
intermediate entity"*). It was proposed, reviewed, accepted and implemented. The ~12 `dm:` terms that Discussion
#64 §1.1 treats as an accidental overlap are the UC-01 deliverable.

**Both positions are defensible, for different jobs:**

| | UC-01's sheet-level model | RES-A-9's titleblock-level model |
| --- | --- | --- |
| Purpose | Search and filter sheets by metadata | Extract assertions from a detected region |
| Multi-sheet conflict | Not a concern — one value per sheet | The central concern — two sheets may disagree |
| Provenance | Not required | Required per value |
| Query shape | `?sheet metadata:drawingIdentifier "ST-101"` | `?tb tb:identificationNumber ?v . ?tb tb:assertsMetadataFor ?doc` |

UC-01's CQs never ask "which sheet asserts a conflicting value for this document", so it has no reason to carry
the indirection. The extraction pipeline's entire justification for the split is that question.

**What this means for pass 0.** Discussion #64 §1.1's three options need restating:

- **Option A/B as written** (reuse classes, parallel assertion layer) is still viable, but it is not "avoiding an
  accident" — it is *deliberately running two vocabularies for one concept*, one of which is a shipped,
  CQ-validated deliverable. That is a much higher bar to clear, and it needs UC-01's owner in the room.
- **Option C** (migrate to titleblock-level) would **overturn a reviewed decision and break UC-01's CQ SPARQL**.
  Already rejected for CVAT reasons; this is a second, independent reason.
- **A fourth option not currently on the table:** keep sheet-level as the *validated* layer (UC-01, unchanged) and
  introduce the titleblock-level layer *only* for unvalidated extraction output, with promotion sheet-ward on
  validation. That is close to option B but framed as a **pipeline stage** rather than a parallel vocabulary —
  which is arguably what RES-A-9 finding 2 actually described ("promote to the Document after validation") and
  would make the duplication temporary-by-design rather than permanent.

**Recommendation: put this in front of whoever owns UC-01 before pass 1.** It is the single highest-value
conversation in the whole plan.

### 2.2 What the use cases actually demand

Consolidating the four ORSD traceability matrices, the terms with a CQ behind them are:

| Use case | Status | Terms it needs (all already in `aec_drawing_metadata` / `aec_domain_common` / `aec_common_symbols`) |
| --- | --- | --- |
| **UC-01** Titleblock search | ✅ implemented | `DrawingSheet`, `Layout`, `LayoutContentType`, `DrawingRevision`, `Project`, `Person`, `StatusCode`, `DrawingPackage`, `dcommon:Discipline`; `drawingIdentifier`, `drawingTitle`, `hasScale`, `sheetSize`, `revisionCode`, `issueDate`, `personName`, `projectName`, `projectNumber`, `packageName`, `statusLabel`; `contains`, `hasProperty`, `hasDiscipline`, `hasRevision`, `isRevisionOf`, `belongsToProject`, `belongsToPackage`, `isAuthoredBy`, `isCheckedBy`, `isApprovedBy`, `hasStatusCode` |
| **UC-03** Cross-sheet linking | ✅ implemented | `csymbol:ReferenceSymbol`, `hasReferenceSymbol`, `appearsOn`, `referencesLayout`, `isReferencedBy`, `layoutIdentifier` |
| **UC-06** Content aggregation | ⚠️ draft | `Material`, `HazardClassification`, `depictsMaterial`, `isDepictedOn`, `hasHazardClassification`, `materialName`, `materialSymbol`, `hazardLabel` — **none of them title-block terms** |
| **UC-07** Wall orientation | ⚠️ draft | `BuildingElement`, `Wall`, `FacingDirection`, `northArrowAngle`, `scaleRatio`, wall dimension properties — **one overlap: the north arrow** |

**Every title-block field a current use case needs is already implemented.** UC-01 covers identity, project,
revision, the three person roles, discipline, content type, status and package. Nothing in the proposed 73-term
vocabulary is required to answer any existing CQ.

### 2.3 New redundancies the internal review missed

| Term | Rated in #61 | Revised | Why |
| --- | --- | --- | --- |
| `Discipline` (SKOS scheme) | 🟢 Core | 🔴 **Redundant** | `dcommon:Discipline` is a full class hierarchy (`Structural`, `MEP > Mechanical / Electrical > Lighting / Plumbing`, `Architectural > Facade / FireLifeSafety`, `Masterplan`, + `Civil`). UC-01 FR 5 reuses it and **explicitly dropped** a `disciplineCode` string (change G3) because `rdf:type` checks against the hierarchy give **automatic sub-discipline rollup** — querying `dcommon:MEP` matches `Mechanical`, `Electrical`, `Plumbing`, `Lighting` via `rdfs:subClassOf`. A flat SKOS scheme loses exactly that. Reuse `dcommon:Discipline` + `dcommon:hasDiscipline` |
| `hasNorthPointOrientation` | 🟠 Marginal | 🔴 **Redundant** | UC-07 specifies `northArrowAngle` (`xsd:decimal`, degrees clockwise from page-up) on the drawing, with a stated datum convention, and **explicitly rejects** modelling the arrow as an entity. ADIRO's version is the same measurement with a vaguer name, a different datatype and no datum. It is also a drawing-level datum, not a title-block field |
| `scale` | 🟢 Core | 🔴 **Redundant as a term** | `dm:hasScale` (string) exists from UC-01 FR 1, and UC-07 adds `scaleRatio` (decimal) for arithmetic. The scale story is *already* two properties by design. A third string property is duplication. **The field remains core to extraction** — it just binds to `dm:hasScale` |
| `dimensionUnits` | 🟡 Useful | 🟡 **Useful — confirmed genuinely new** | Nothing in any use case or module covers the German `1:50 – m,cm` convention. Keep, and attach it wherever `hasScale` lives |
| `DocumentType` | 🟢 Core | 🟢 **Core, with a warning** | UC-01 v0.2 introduced a `DrawingType` (Plan / Section / Elevation / Detail / Schedule) and v0.3 **deleted it** as a duplicate of `metadata:LayoutContentType` (change G4). ADIRO's `DocumentType` is DIN *Planart* + ISO 19650 type codes — design **stage** and document **kind**, a genuinely different axis from view type. Keep it, but say so in the `rdfs:comment`, or it will be deleted for the same reason `DrawingType` was |
| `SuitabilityStatus`, `DocumentLifecycleStatus` | 🟡 Useful | 🟡 **Useful, but no CQ demands the split** | UC-01 satisfies CQ 7.1/7.2 with a *single* `StatusCode` + `statusLabel`. RES-A-9 finding 5's three-way split is justified by **standards fidelity**, not by any current query. That is a legitimate reason — but it should be stated as such rather than presented as a requirement |
| `ContainerState` / `hasContainerState` | 🟠 Marginal | 🟠 **Marginal — confirmed, and now doubly so** | Not printed on a sheet (internal review) **and** no CQ in any of the four use cases references CDE location |

### 2.4 The traceability gap (finding 2)

Cross-referencing all four ORSDs' CQs against the 73 terms, roughly **40 have no competency question behind
them** — including every one of these:

`Organization` · `hasClient` · `hasLegalOwner` · `hasOriginator` · `hasResponsibleDepartment` ·
`hasTechnicalReference` · `ConfidentialityClassification` · `hasConfidentialityClassification` ·
`SuitabilityStatus` · `ContainerState` · `ClassificationCode` · `hasClassification` · `keyword` · `Language` ·
`hasLanguage` · `planKey` · `paperSize` · `hasProjectionMethod` · `purpose` · `intendedUse` · `validFrom` ·
`validUntil` · `organizationIdentifier` · `sequentialNumber` · `volumeSystemCode` · `levelLocationCode` ·
`supplementaryTitle` · `numberOfSheets` · `numberOfPages` · `pageNumber` · `revisionDescription` · `supersedes` ·
`hasRole` · the whole §10 provenance layer

Some of these are obviously valuable — `hasClient` is on nearly every AEC title block, and `planKey` buys free
supervision. **The problem is not that they are bad terms. It is that the repo's stated methodology cannot
justify them**, because the demand comes from somewhere the LOT pipeline does not model: the RES-A-13 extraction
experiment, whose driver is "capture whatever the title block prints", not a competency question.

**Two honest ways to close this:**

- **(a) Write an ORSD for the extraction use case.** "As a data engineer, I want every field printed in a title
  block captured with provenance and confidence, so that…" — with real CQs (*"which extracted values on sheet X
  have confidence below 0.8?"*, *"which sheets assert conflicting clients for one document?"*). This legitimises
  the provenance layer, `conflictsWith`, and the assertion-level modelling in one stroke, and it is the missing
  use case that RES-A-9 finding 2 is really serving. **Recommended.**
- **(b) Cut the vocabulary to use-case demand.** Defensible, but it would delete the extraction experiment's
  reason to exist.

Doing neither leaves ~40 terms that the repo's own README says should not exist.

### 2.5 Gaps — what the use cases need that the title-block vocabulary lacks

Minor, but worth noting since the review runs both ways:

- **`DrawingPackage` / `packageName`** (UC-01 FR 8) — volume/package grouping. Title blocks *do* often print a
  volume or package reference, and the proposed vocabulary has no term for it. `dm:` covers it; the extraction
  profile should include it.
- **`layoutIdentifier`** (UC-03, pending UC-01 v0.4) — a layout number within a sheet. Printed near views rather
  than in the title block, so probably correctly absent, but it interacts with `sheetNumber`.
- **No gap on the 17 core extraction fields** — all are covered by the proposal or by `dm:`.

---

## 3. Part B — against DANO

### 3.1 What DANO is

**Drawing Analysis Ontology** — `https://w3id.org/dano`, prefix `dano:`, CC BY 4.0, from RUB
Informatik im Bauwesen (the same group as `exdoc`). Scope, in its own words: *"concepts of technical drawings
from the perspective of computer vision-based drawing analysis"*. 16 classes, 12 object properties, 7 datatype
properties.

**Maintenance:** repo created 2025-03-11, last pushed **2025-07-15** — quiet for about 13 months, 5 stars, no
tags or releases. Better than DiCon (dormant since 2022) and it has a **permanent `w3id.org` IRI** rather than a
version-pinned path, but there is no release discipline. Treat as **borrowable, not dependable**.

### 3.2 The provenance overlap — DANO covers §10 substantially

This is the real find. ADIRO §10 proposes six provenance terms; DANO already has most of that ground:

| ADIRO §10 proposal | DANO equivalent | Assessment |
| --- | --- | --- |
| `extractionConfidence` (`xsd:float`) | `dano:hasConfidence` (`xsd:decimal`, on `DrawingElement`) | **Direct equivalent.** Align or reuse |
| `extractedFrom` → `SourceFile` (object) | `dano:inferredFrom` (`xsd:string`, "the origin file") | DANO uses a **string**. Corroborates that `SourceFile`-as-a-class may be over-modelled for current needs |
| `extractedByModel` → `MLModel` (object) | `dano:inferredBy` (`xsd:string`, actor/company/software) **+** `dano:inferredWith` (`xsd:string`, algorithm) | DANO **splits actor from algorithm**, which is a better decomposition than ADIRO's single property — and both are strings, independently corroborating the #61 verdict that `MLModel` is over-modelled |
| *(nothing proposed)* | `dano:inferredAt` (`xsd:date`) | **🔴 GAP IN ADIRO.** No extraction timestamp is proposed anywhere. Re-extraction comparison is impossible without one. Add it |
| `hasBoundingBox` → `BoundingBox` | `dano:hasGeometry`, `dano:defaultGeometry` | DANO links to a **geometry** rather than a bespoke bbox class — more general and reusable. Worth considering instead of minting `BoundingBox` |
| `hasValidationStatus` | *(none)* | **ADIRO-unique.** DANO has no human-in-the-loop concept. Keep |
| `conflictsWith` | *(none)* | **ADIRO-unique.** Keep |
| *(nothing proposed)* | `dano:hasIfcRepresentation` (`xsd:string`) | Cheap alternative to the §9 IFC alignment axioms for the common case |

### 3.3 `DrawingElementMeta` bears on the pass-5 blocker

Pass 5 is blocked on **RDF-star vs reification** for per-value provenance (RES-A-9 next step 5). DANO has already
made that choice:

```
DrawingElement --hasMeta--> DrawingElementMeta
                              ├── inferredAt   (date)
                              ├── inferredBy   (actor/software)
                              ├── inferredFrom (origin file)
                              └── inferredWith (algorithm)
```

It is **reification via a meta-object** — the option RES-A-9 §10 describes as *"uglier but far better tool
support"*. A peer research group hitting the same problem chose the same way, which is real evidence for that
branch of a decision currently held open.

Note DANO's asymmetry: `hasConfidence` sits on the **element**, not on the meta-object, while the four
`inferred*` properties sit on the meta. That is worth copying deliberately or rejecting deliberately — confidence
is per-assertion, whereas the inference metadata is often shared across every element from one run, so putting
them in different places is arguably correct rather than sloppy.

**Recommendation: use DANO as evidence in the pass-5 decision, and consider aligning `tb:` provenance properties
to `dano:` rather than minting parallel ones.** Do not import DANO — it would drag its 16 drawing-element classes
into a suite with a blocking DL reasoner for the sake of seven datatype properties.

### 3.4 DANO is relevant beyond the title block — flag to other use-case owners

Out of scope for RES-89, but this review found it and it should not be lost:

| DANO terms | Relevant to | Note |
| --- | --- | --- |
| `SectionSymbol`, `Terminator`, `refersTo`, `isReferredToBy` | **UC-03** cross-sheet linking | UC-03 mints `csymbol:ReferenceSymbol`, `referencesLayout`, `isReferencedBy`. DANO has a published equivalent pattern. UC-03 is already implemented, so this is an alignment question, not a rebuild — but worth knowing before UC-03 v0.3 |
| `Dimension`, `DimensionChain`, `DimensionLine`, `AxisLine`, `hasGeometry` | **UC-07** wall measurement | UC-07 needs on-drawing lengths and angles. DANO models dimension lines and geometry natively |
| `depicts`, `isDepictedBy` | **UC-06** materials | UC-06 mints `depictsMaterial` / `isDepictedOn`. DANO's generic `depicts` / `isDepictedBy` could be the parent property |
| `TextField`, `TextElement`, `isText` | The title block itself | A title block *is* a `dano:TextField` (a composite of `min 2` `TextElement`s). This is **complementary, not competing**: DANO gives the CV layer (here is a text region, here is its string), `tb:` gives the semantic layer (this string means "checked by"). The clean division is `dano:` for what was seen, `tb:` for what it means |
| `contains`, `isContainedIn` | `dm:contains` | Already covered internally |

---

## 4. Revised rating deltas

Changes to [Discussion #61 §11.1](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/61) implied by
this review. **#61 has not yet been updated** — apply these before it is used for pass-0 review.

| Term | #61 | Revised | Driver |
| --- | --- | --- | --- |
| `Discipline` | 🟢 Core | 🔴 Redundant | `dcommon:Discipline` (§2.3) |
| `scale` | 🟢 Core | 🔴 Redundant | `dm:hasScale` + UC-07 `scaleRatio` (§2.3) |
| `hasNorthPointOrientation` | 🟠 Marginal | 🔴 Redundant | UC-07 `northArrowAngle` (§2.3) |
| `MLModel` | 🟠 Over-modelled | 🟠 **Confirmed** — drop to a literal | DANO uses strings (§3.2) |
| `SourceFile` | 🟢 Core | 🟡 Useful — consider a literal | `dano:inferredFrom` is a string (§3.2) |
| `BoundingBox` | 🟢 Core | 🟡 Useful — consider a geometry | `dano:hasGeometry` (§3.2) |
| `extractionConfidence` | 🟡 Needed, blocked | 🟡 **Align to `dano:hasConfidence`** | §3.2 |
| `extractedByModel` | 🟡 Useful | 🟡 **Split** into actor + algorithm | `dano:inferredBy` / `inferredWith` (§3.2) |
| **NEW — extraction timestamp** | *(absent)* | 🟢 **Core — add it** | `dano:inferredAt`; re-extraction comparison needs it (§3.2) |
| `DocumentType` | 🟢 Core | 🟢 Core **+ comment required** | Must state it is not `LayoutContentType` (§2.3) |
| `SuitabilityStatus`, `DocumentLifecycleStatus` | 🟡 Useful | 🟡 Useful **— standards-driven, not CQ-driven** | §2.3 |

Net: **three more terms drop to redundant** (8 total), one **new core term** appears, and four provenance terms
change shape. The mint shrinks from ~48 to roughly **44**, and gains a timestamp.

---

## 5. Decisions this review asks for

| # | Decision | Owner | Blocks |
| --- | --- | --- | --- |
| 1 | **Sheet-level (UC-01) vs titleblock-level (RES-A-9) placement** — including the "pipeline stage" fourth option in §2.1 | UC-01 owner + Alessio | pass 1. Supersedes the §1.1 framing |
| 2 | **Write an extraction ORSD, or cut to use-case demand** (§2.4) | Alessio | the legitimacy of ~40 terms |
| 3 | Confirm `dcommon:Discipline` reuse and drop the SKOS `Discipline` | — | pass 3 |
| 4 | Drop `scale`, `hasNorthPointOrientation`; bind to `dm:hasScale` / UC-07 `northArrowAngle` | — | pass 2 |
| 5 | **Align provenance to `dano:` rather than minting parallel terms**; add the timestamp | — | pass 5 |
| 6 | Use DANO's `DrawingElementMeta` as evidence in the RDF-star vs reification decision | — | pass 5 |
| 7 | Flag DANO to the UC-03 / UC-06 / UC-07 owners (§3.4) | — | nothing here |

---

## 6. Method and limits

**Read in full:** UC-01 ORSD v0.3 (402 lines), UC-06 ORSD v0.1, `docs/uc-orsd/README.md`; UC-07 and UC-03
entity/traceability sections; the DANO specification pages; the DANO repository's activity.

**Not read:** UC-07 and UC-03 in full (CQ sections skimmed via their traceability matrices); the raw DANO TTL —
DANO's terms come from its generated specification, so exact domains/ranges should be confirmed against the
source before any alignment axiom is written. **UC-02, UC-04 and UC-05 have no ORSD**, so "no use case needs
this" means *no use case that has been written down* — UC-05 (contractor design comparison) in particular could
plausibly need `conflictsWith` and the assertion-level model.

**The "~40 terms have no CQ" count** is a cross-reference of written traceability matrices, not a judgement that
those terms are useless — §2.4 says so explicitly. Three of the seven use cases being unwritten is the larger
gap here, and it means this review can under-state demand but not over-state it.
