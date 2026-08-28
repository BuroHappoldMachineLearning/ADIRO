# ADIRO worklog

A **running record of changes made to this repository by AI-assisted sessions** — what was done, how it was
verified, and what the next step is. It exists so that a change made in one session is legible to whoever picks
the work up next, without re-reading a transcript.

**Scope:** repo changes, and the external artefacts a repo change depends on (a GitHub Discussion published, a
YouTrack issue updated). ADIRO documentation authority now sits on GitHub — see the 2026-08-11 governance entry. Not a substitute for `git log` — this records *intent, verification and open
threads*, which commits do not carry.

## How to maintain this file

- **Newest entry first**, directly under this section.
- One entry per session or coherent change set. Keep the heading format: `## YYYY-MM-DD — <short title>`.
- Every entry states: the **issue** it belongs to, the **branch**, what **changed**, how it was **verified**
  (including anything that could *not* be verified, and why), and the **next step**.
- Record decisions that were *deferred or rejected*, not only work done — a rejected option is the most
  expensive thing to rediscover.
- When an entry's next step is completed in a later session, do not rewrite history: add the new entry and let
  the older one stand. Cross-reference by date.
- Keep it factual. If a gate was not run, say so plainly rather than implying it passed.

---

## 2026-08-19 — Placement question resolved: Option 1 (reuse `dm:` directly)

**Issue:** [RES-89](https://bhmlrnd.youtrack.cloud/issue/RES-89) · **PR:** [#66](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/66) · **Branch:** `res-89-aec-titleblock-tbox`

### The decision

For the 10 content properties that overlap `aec_drawing_metadata` (drawing number, title, scale, sheet size,
revision code, issue date, author/checker/approver, status) — **reuse `dm:` directly. No `tb:` counterpart is
minted for any of them, and no parallel assertion layer is built.** This resolves what Discussion #64 called
"the largest open decision in the whole plan" (§1.1, open question 6).

Concretely: the extraction pipeline writes these 10 values straight onto the existing `dm:DrawingSheet` /
`dm:DrawingRevision` properties — the same ones UC-01's search feature already reads. There is no `tb:`-level
"unvalidated claim" stage for them.

**Preceded by a proposal document** written for team review before implementing:
`docs/modularization/titleblock-placement-option1-plan.md`. It lays out what Option 1 buys (zero new terms, zero
migration risk to UC-01, and — a fact confirmed while drafting it — `aec_drawing_metadata` already restricts
every `DrawingSheet` to exactly one `Titleblock`, so the two are already the same fact at the schema level for
this piece), what it costs (no per-field quarantine before an extracted value becomes "official"; validation
must happen in the pipeline or via SHACL instead), and three questions put to the team before implementation.

### What this does NOT resolve

Flagged explicitly so it isn't conflated: ADIRO still has no `Document` class distinct from `DrawingSheet`, so
the separate concern in [RES-A-9 finding 2](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/61)
— *different sheets* in one document set disagreeing with each other — remains an open gap regardless of this
decision. Tracked as its own item, not folded into placement.

### Changes made

| Surface | Change |
| --- | --- |
| `docs/modularization/titleblock-placement-option1-plan.md` | **New.** The proposal document, written before implementation |
| `src/aec_titleblock.ttl` | Header's "unresolved question" note rewritten as "Decision 1 — Placement (resolved)"; footer section (a) rewritten from "pending decision 1" to "resolved: reuse `dm:` directly" for all 10 fields, each with its `dm:` target and attachment point named |
| [Discussion #64](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/64) | §1.1 gains a resolution banner; the old "A for classes + B for properties" recommendation is struck through as superseded for properties (A for classes stands); open question 6 closed |
| `docs/modularization/aec_titleblock-build-plan.md` | Status line, the "Reconciliation with existing terms" note, and the PR table updated — former PR 2 ("remaining core properties, once the placement decision lands") is dropped from the sequence entirely, since Option 1 means there is nothing left to build for those 10 fields. The separate `assertsMetadataFor`/`Document` provisional note is now explicitly distinguished from this resolved decision, not conflated with it |

### Verification

No new terms were minted — this was a documentation/decision change, not a vocabulary change. Re-ran every gate
to confirm nothing regressed:

| Check | Result |
| --- | --- |
| Term count | **11** (unchanged) |
| `validate_ontology.py` (module, then all five) | pass |
| **HermiT** | pass — `reason exit code: 0` |
| ROBOT `report` | 0 ERROR (unchanged) |
| `generate_docs.py` / `mkdocs build` | clean |

### Next steps

1. **Update the extraction pipeline / `build_extraction_profile.py`** to write the 10 fields onto `dm:` properties
   directly, per this decision — this is the actual remaining work, and it lives outside the ontology.
2. **Decide where pre-write validation for these 10 fields lives** — pipeline code or a SHACL shape run before
   the write. Option 1 does not supply this for free; it was an accepted trade-off, not a solved problem.
3. **Consider tracking the `Document`-vs-`DrawingSheet` gap as its own issue**, independent of this decision.
4. Pass 3 (SKOS enumerations), the extraction ORSD, and the field-frequency survey remain as previously recorded.

---

## 2026-08-13 (review round 1) — PR #66 changes requested; 14 terms → 11

**Issue:** [RES-89](https://bhmlrnd.youtrack.cloud/issue/RES-89) · **PR:** [#66](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/66) · **Branch:** `res-89-aec-titleblock-tbox`

### CI came back green; the blocker was human

HermiT consistent, ROBOT 0 ERROR, compat-diff reported 14 non-breaking `TERM_ADDED` at MINOR level. **Alessio
Lombardi requested changes**, and separately Ahmed Zaalouk left five recommendations on
[Discussion #61](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/61) which Alessio agreed with in
full.

### What was asked, and what was done

| Request | Source | Action |
| --- | --- | --- |
| `DocumentType` definition is long and vague, and defines by reference to other concepts rather than saying what it is | PR review | **Withdrawn to a later pass**, with the trio `DocumentType` / `DocumentTypeScheme` / `hasDocumentType` |
| A controlled vocabulary with no values listed is unusable — *"otherwise how do we use this?"* | PR review | Same withdrawal. Agreed as a general rule: **a scheme ships with its concepts or it does not ship.** Recorded in §10 acceptance criteria |
| Are all three organisation properties needed? `hasLegalOwner` is probably not something a title block expresses | PR review (Alessio + Tianyang Huang) | **`hasLegalOwner` withdrawn**, deferred pending the field-frequency survey |
| Consider `describes` / `defines` / **`asserts`** instead of `has*` | PR review | **Adopted.** `hasClient` → `assertsClient`, `hasOriginator` → `assertsOriginator`, recorded as the naming convention for all future value-bearing properties |
| Why not list values as classes, like `dm:LayoutContentType`? | PR review | Answered in **Discussion #64 §6** with a three-way comparison (classes / `owl:oneOf` / SKOS) rather than the two-way one that was there |
| Defer any field appearing on <~40% of sampled sheets | Discussion #61 (Zaalouk 1, Alessio agreed) | **Adopted as an acceptance criterion** (§10). Makes the survey a gating input, not a nice-to-have |
| Don't implement the manufacturing-heritage fields | Discussion #61 (Zaalouk 2) | Already 🟠 in the assessment; now recorded as **do not implement** in §11.2 |
| Minimal standards per use case; ICDD as the anchor for cross-sheet document links | Discussion #61 (Zaalouk 3) | Recorded in §10. **Note this changes ICDD's status** — see below |
| Use ROBOT to catch conflicting/redundant terms | Discussion #61 (Zaalouk 3) | Already in place and run: 0 duplicate labels across the merged suite |
| Separate Titleblock ontology linked to `aec_drawing_metadata` | Discussion #61 (Zaalouk 4) | Already the shipped design |
| Target the 29 🟢 Core terms, defer the 20 marginal; use `dano:depicts` to link out rather than import | Discussion #61 (Zaalouk 5, Ahmed agreed) | See the stale-ratings problem below |

### Two things worth recording beyond the mechanical changes

**1. "Build the 29 🟢 Core terms" was an instruction pointing at stale ratings.** Ahmed's reply on #61 says to
build the first pass from the 🟢 Core set. But the use-case/DANO review had already downgraded three of those
rows to 🔴 Redundant — `Discipline`, `scale` and `hasNorthPointOrientation` — and §11.1 had **not** been
updated. Building "the 29 core" as #61 then read would have minted three duplicates, which is precisely what
Zaalouk's own point 3 warns against.

Fixed: #61 now carries a **red banner** at the top of §11.1 and a new **§11.2 "Revisions to the assessment —
current position"** listing every change with its driver. The original emoji are kept for traceability but §11.2
is marked authoritative. *A rating table that people build from is a live instruction, and it has to be corrected
the moment the assessment moves.*

**2. ICDD's status has flipped, and this is not yet reflected in the decision record.** The demotion said
alignment was "conditional on a stated ICDD/openCDE deliverable requirement". Zaalouk point 3b makes ISO 21597-1
the anchor for the document-to-document links UC-03 needs, and Alessio agreed — **so the condition has been
met.** The ~4 alignment axioms should now be scheduled rather than deferred. Left as a next step rather than
changed unilaterally, because it is a scope addition.

### Also unaddressed by the review

Neither reviewer engaged with the two structural findings in the PR body: the **UC-01 placement contradiction**
(Alessio's *"isn't this already what we proposed?"* on Zaalouk's point 4 suggests he read it as agreement, but the
finding is that UC-01's *implementation* puts the data on the sheet, accepted in his own G2 review) and the
**~40-terms-without-a-competency-question** traceability gap. Both remain open and both are more consequential
than anything fixed in this round.

### Verification after the changes

| Check | Result |
| --- | --- |
| `validate_ontology.py` (module, then all five) | pass |
| Term count / completeness | **11 terms**; every property has label + domain + range + comment; no dangling references to removed terms |
| **HermiT** | **pass — `reason exit code: 0`** |
| ROBOT `report` | **0 ERROR**; 11 `missing_definition` WARN + 1 INFO, matching pre-existing practice |
| `generate_docs.py` / `mkdocs build` | clean |

### Next steps

**Not done deliberately:** no reply was posted to the PR review — Ahmed will handle that conversation.

1. **Post the review reply**, covering the five actions above, the SKOS three-way answer, and resurfacing the two
   unaddressed structural findings. Tag Zaalouk and Tianyang, whom Alessio asked for opinions.
2. **The placement decision** — still the highest-value open item; determines whether the first pass stays at 11
   terms or grows to ~29.
3. **Schedule the ICDD alignment axioms** now that UC-03 supplies the requirement.
4. **Run the field-frequency survey** — now formally gating every marginal term under the <40% rule.
5. **Pass 3:** `DocumentType` and the remaining schemes, landing complete with their concept values.
6. **Extraction ORSD**, or cut to use-case demand.

---

## 2026-08-11 (implementation) — initial `aec_titleblock.ttl`; PR policy changed

**Issue:** [RES-89](https://bhmlrnd.youtrack.cloud/issue/RES-89) · **Branch:** `res-89-aec-titleblock-tbox`

### Policy change

**No PR is opened until `src/aec_titleblock.ttl` carries an initial version of the vocabulary.** Decided by
Ahmed. Rationale: a docs-and-plumbing-only PR cannot be judged — a reviewer has no terms to look at — and
invites a rubber stamp, which is the failure the one-PR-per-pass rule exists to prevent. The first PR now
bundles the documents, the pass-1 plumbing and the initial terms; later PRs stay one per pass.

### What was written — 14 terms

| Kind | Terms |
| --- | --- |
| Classes | `Organization`, `DocumentType` (+ `DocumentTypeScheme` as a `skos:ConceptScheme`) |
| Object properties | `assertsMetadataFor`, `hasClient`, `hasLegalOwner`, `hasOriginator`, `hasDocumentType` |
| Datatype properties | `organizationName`, `supplementaryTitle`, `sheetNumber`, `numberOfSheets`, `planKey`, `dimensionUnits` |
| Annotation property | `extractionHint` |

### The selection rule, and why it matters

**A term is in this version only if it has no counterpart anywhere in `aec_drawing_metadata`.** Everything that
overlaps an existing `dm:` term — identifier, title, scale, paper size, revision code, issue date, the three
person roles, the status properties — is **deferred, and listed in the TTL's own footer** rather than minted.

This is what lets an initial version exist *without* pre-empting the unresolved §1.1 placement decision. Nothing
in this file is a second vocabulary for an existing concept, so nothing needs withdrawing whichever way that
decision goes. The footer also records the five terms dropped as redundant and why, so the omissions are legible
to someone reading the module rather than only to someone reading the plan — which matters, because "why is
`scale` missing?" is otherwise a reasonable and time-wasting question.

**Provisional choices, flagged in the file header rather than buried:**

- Domains are `dm:Titleblock`, consistent with the module's stated purpose.
- `assertsMetadataFor` ranges over `dm:DrawingSheet`, **not** a newly minted `Document` class — minting a
  competing `Document` would deepen the UC-01 placement conflict rather than settle it, and the sheet is the unit
  UC-01 established as searchable.
- At `0.1.0` a reversal costs a rename, not a migration. That is what the pre-1.0 version is for.

**One consequence worth recording:** `Discipline` was dropped in favour of `dcommon:Discipline`, but nothing in
the TTL references `dcommon:` — doing so needs an `owl:imports` of `aec_domain_common`, which would pull the
whole module chain (`domain_common` → `common_symbols` → `drawing_metadata`) into a module that currently sits
directly below `drawing_metadata`. **That import question is unresolved and is noted in the TTL footer.** It was
not visible until the term was actually dropped.

### Verification

| Check | Result |
| --- | --- |
| `validate_ontology.py` on the module | **pass** |
| `validate_ontology.py` on all five | **pass** — no regression |
| Every property has label + domain + range + comment | **pass** — checked programmatically via rdflib, 0 incomplete |
| Duplicate `rdfs:label` across the merged suite | **0** — the ROBOT `duplicate_label` signal that would flag accidental `dm:` overlap is clean *by construction*, which is the selection rule paying off |
| `generate_docs.py` | **5/5 clean** |
| `mkdocs build` | **clean** |
| **`run_reasoning.sh` (HermiT)** | **PASS — `reason exit code: 0`.** Java 17 (Temurin) installed to run it; merged 5-module suite is consistent with no unsatisfiable classes. The blocking gate is now green |
| ROBOT `report` | **0 ERROR** after a fix (below). Remaining from this module: 14 `missing_definition` WARN + 1 `missing_superclass` INFO — both types match 213 / 19 pre-existing rows, so this module follows existing repo practice rather than diverging |

### The reasoner caught a defect in the plan, not the module

Worth recording because it would have scaled. The first draft of the TTL followed the property template in
Discussion #64 §7, which showed `rdfs:label "checked by"@en, "geprüft von"@de`. ROBOT's `report` raises
**`multiple_labels` as an ERROR** for any term with more than one `rdfs:label` — 4 ERRORs from just two
properties.

Fixed in three places rather than one, because fixing only the file would have left the trap in place:

- **the module** — one English `rdfs:label`; German moved to `skos:altLabel`, where the extractor wants it
  anyway, so nothing is lost;
- **Discussion #64 §7** — the template corrected, with the rule added to the "easy to get wrong" list. Written
  the old way, the full ~40-property vocabulary would have produced roughly **80 ERRORs**;
- **`AGENTS.md`** — the authoring conventions now state the one-label rule explicitly, next to the existing
  label-uniqueness rule it complements.

This is the first thing the reasoning gate has caught that static validation could not, which is a small
argument for running it before every PR rather than relying on CI.

### Changes made

| Surface | Change |
| --- | --- |
| `src/aec_titleblock.ttl` | 14 terms; header records the provisional choices and the UC-01 conflict; footer lists deferred, dropped and later-pass terms |
| `changelogs/aec_titleblock.md` | `[Unreleased]` rewritten from "no domain terms yet" to the actual term list, the selection rule and the dropped terms |
| `docs/modularization/aec_titleblock-build-plan.md` | New §1 "Current state of `src/aec_titleblock.ttl`"; PR table rebuilt around the new policy (PR 0 + PR 1 merged); stale "before any `.ttl` is written" status and pass-0 wording corrected; sections renumbered |
| [Discussion #64](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/64) | Status line updated; §5 gains the initial-version block and the PR policy; pass-0 row now records that §1.1 is a choice between two *reviewed* architectures because of the UC-01 finding |
| [RES-89](https://bhmlrnd.youtrack.cloud/issue/RES-89) | Progress comment with the term list, the selection rule, the verification table and the open §1.1 question |
| `AGENTS.md`, [Discussion #64](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/64) §7 | One-`rdfs:label` rule added / property template corrected after the ROBOT finding |

### Next steps

1. ~~Run HermiT~~ — **done, passes.** Temurin 17 installed; `bash scripts/run_reasoning.sh` reproduces CI locally.
2. **Open the first PR** (documents + plumbing + these 14 terms). File the GitHub issue first, per MAN-A-3.
3. **§1.1 with UC-01's owner and Alessio** — blocks pass 2 (the overlapping core properties), not this PR.
4. Then pass 3 (SKOS concepts for `DocumentType` and the other schemes), which depends on nothing open.
5. Apply the vocabulary-review deltas to [Discussion #61](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/61) §11.1 — still outstanding from the review entry below.

---

## 2026-08-11 (review) — title-block vocabulary vs the use cases and DANO

**Issue:** [RES-89](https://bhmlrnd.youtrack.cloud/issue/RES-89) · **Branch:** `res-89-aec-titleblock-tbox`
**Deliverable:** `docs/modularization/titleblock-vocabulary-review.md`

Two external tests of the 73 proposed terms that the internal §11.1 assessment could not apply: do they serve
the use cases in `docs/uc-orsd/`, and has [DANO](https://rub-informatik-im-bauwesen.github.io/dano/) already
built the drawing-analysis half.

### The finding that matters most — it is not a redundancy question

**UC-01 is "Titleblock-Based Drawing Search", it is already implemented, and it made the opposite architectural
decision to RES-A-9 finding 2 — deliberately and under review.** Its ORSD design note states that
`metadata:Titleblock` models the *visual region* while the information goes on `DrawingSheet` as datatype
properties, and that "the two layers coexist independently". Change G2 in v0.3 records this as an alignment
decision accepted in Alessio's PR review.

So the ~12 `dm:` term overlaps that Discussion #64 §1.1 treats as an accidental collision **are the UC-01
deliverable**. §1.1 is not "reconcile with terms that drifted in" — it is "choose between two reviewed
architectures", and option C would break UC-01's CQ SPARQL. The review proposes a **fourth option**: keep
sheet-level as the *validated* layer and use titleblock-level only for unvalidated extraction output, promoting
sheet-ward on validation — a pipeline stage rather than a permanent parallel vocabulary, which is arguably what
finding 2 actually described. **Needs UC-01's owner in the room before pass 1.**

### The second structural finding

**~40 of the 73 terms have no competency question behind them, from any written use case.** Every title-block
field a current use case needs is already implemented in `dm:`. The demand for the rest comes from the RES-A-13
extraction experiment, which the LOT pipeline does not model — so the repo's own stated rule ("every OWL term
traces back to a use case need", `docs/uc-orsd/README.md`) cannot justify them. Two honest fixes: write an
extraction ORSD with real CQs (recommended — it legitimises the provenance layer and `conflictsWith` in one
stroke), or cut to use-case demand.

### Three new redundancies, and one gap

| Term | Was | Now | Why |
| --- | --- | --- | --- |
| `Discipline` | 🟢 Core | 🔴 Redundant | `dcommon:Discipline` is a full hierarchy UC-01 reuses; UC-01 **dropped** a `disciplineCode` string (G3) because `rdf:type` checks give automatic sub-discipline rollup. A flat SKOS scheme loses that |
| `scale` | 🟢 Core | 🔴 Redundant | `dm:hasScale` (string, UC-01) + UC-07 `scaleRatio` (decimal) already cover it. The field stays core; the term is duplication |
| `hasNorthPointOrientation` | 🟠 Marginal | 🔴 Redundant | UC-07's `northArrowAngle` is the same measurement, better specified (datum stated), and UC-07 explicitly rejects modelling the arrow as an entity |
| *extraction timestamp* | absent | 🟢 **Core — add** | `dano:inferredAt`. Re-extraction comparison is impossible without one |

Also: `DocumentType` must state in its comment that it is **not** `LayoutContentType` — UC-01 deleted its own
`DrawingType` for exactly that duplication (G4), and this would repeat it. And the three-way status split is
**standards-driven, not CQ-driven**: UC-01 answers its status CQs with a single `StatusCode`. Legitimate, but say
so rather than presenting it as a requirement.

### DANO

`https://w3id.org/dano`, CC BY 4.0, RUB (same group as `exdoc`). 16 classes / 12 object / 7 datatype properties,
scoped to CV-based drawing analysis. **Maintenance: created 2025-03-11, last pushed 2025-07-15** — quiet ~13
months, 5 stars, no releases, but a permanent `w3id.org` IRI. **Borrowable, not dependable.**

It covers the §10 provenance layer substantially: `hasConfidence`, `inferredFrom`, `inferredBy` +
`inferredWith` (actor split from algorithm — a better decomposition than ADIRO's single `extractedByModel`),
`inferredAt`, `hasGeometry`, `hasIfcRepresentation`. All the `inferred*` properties are **strings**, which
independently corroborates the §11.1 verdict that `MLModel` is over-modelled — and suggests `SourceFile` may be
too. `hasValidationStatus` and `conflictsWith` have no DANO equivalent and stay ADIRO-unique.

**`dano:DrawingElementMeta` + `hasMeta` is a worked reification pattern** — direct evidence for the pass-5
RDF-star-vs-reification decision, from a peer group that hit the same problem and chose reification. Note its
asymmetry: confidence on the element, inference metadata on the meta-object. Worth copying or rejecting
deliberately, not by accident.

**Recommendation: align to `dano:`, do not import it** — importing drags 16 drawing-element classes into a suite
with a blocking DL gate for the sake of seven datatype properties.

DANO also matters **outside** RES-89 and this should not be lost: `SectionSymbol` / `refersTo` /
`isReferredToBy` overlap **UC-03**; `Dimension` / `DimensionLine` / `hasGeometry` overlap **UC-07**; `depicts` /
`isDepictedBy` could parent **UC-06**'s `depictsMaterial`; and `TextField` / `TextElement` / `isText` are
complementary to the title-block work — `dano:` for what the CV saw, `tb:` for what it means.

### Consequences

- Mint shrinks from ~48 to roughly **44**, plus a new timestamp term.
- **Discussion #61 §11.1 has NOT been updated** with these deltas — they are listed in §4 of the review
  document. Apply before #61 is used for pass-0 review, or the ratings there will mislead.
- Seven decisions requested, listed in §5 of the review. Two need Alessio and UC-01's owner; the rest are
  mechanical.

### Method limits, stated in the document

UC-01 and UC-06 ORSDs read in full; UC-03 and UC-07 via their entity and traceability sections; DANO from its
generated specification, **not** its raw TTL — confirm domains/ranges before writing any alignment axiom.
**UC-02, UC-04 and UC-05 have no ORSD at all**, so "no use case needs this" means *no written use case*. UC-05
(contractor design comparison) could plausibly need `conflictsWith` and the assertion-level model — so this
review can under-state demand, not over-state it.

---

## 2026-08-11 (governance) — GitHub becomes the source of truth for ADIRO documentation

**Decision by:** Ahmed Elnagar · **Branch:** `res-89-aec-titleblock-tbox`
Prompted by not wanting to maintain two copies of the same document — a drift risk flagged when the Discussions
were first published earlier the same day.

### The decision

**GitHub is the source of truth for everything ADIRO-related.** Design notes and research write-ups are
maintained as **GitHub Discussions**; repo documentation under `docs/`. YouTrack remains the **issue tracker**,
and the KB for material that must stay internal.

The four YouTrack articles are **frozen, not deleted** — deletion was considered and rejected: it would have
destroyed content, orphaned `RES-A-13`'s children, and broken every link created earlier the same day. Each is
retained so links resolve, with its title prefixed `[FROZEN → GitHub Discussion #NN]` and a notice appended.

| Frozen article | Maintained at |
| --- | --- |
| `RES-A-9` | [Discussion #61](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/61) |
| `RES-A-21` | [Discussion #62](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/62) |
| `RES-A-22` | [Discussion #63](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/63) |
| `RES-A-23` | [Discussion #64](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/64) |

**`RES-A-13` (extraction test plan) stays internal and stays maintained in YouTrack.** It carries client and
project names, corpus statistics and security-classification material, so it is not publishable. It remains the
parent of the notes now published as #62 and #63.

### The licensing reversal — read this before publishing standards content

The published copies were originally **trimmed**: `RES-A-9` §6 reproduced the ISO 7200 field list, and ISO text
is licensed while this repo is public. That trim has been **reversed on instruction** — #61 now carries the full
ISO 7200 mapping with **field names and obligation status**, under an explicit licensing notice at the top of the
page stating that only clause numbers, field names and obligation status are reproduced, that no normative text,
definition, figure, dimension or layout is, and inviting a rights holder to open an issue.

**Two things to be honest about:**

1. **A notice is not a licence.** Whether this is fair use is a judgement for Buro Happold, not something a
   disclaimer settles. **Worth Alessio confirming.** If the answer is no, the fix is to restore the reduced
   table (clause number → ADIRO property → type → range), which is what #61 carried before.
2. **The repo rule had to change to match.** `AGENTS.md` and the design note both said "paraphrase and cite,
   never reproduce, because ADIRO is public". `AGENTS.md` now carries a narrower rule: published pages may cite
   clause numbers and reproduce field names and obligation status under a licensing notice, but never normative
   text, definitions, figures, dimensions or layouts — and `rdfs:comment` in the TTL still paraphrases, never
   quotes. Policy and practice now agree; they briefly did not.

### What was NOT restored, deliberately

The instruction quoted the ISO-table point. The other redactions are a **different risk class** —
client confidentiality rather than standards licensing — so they were left out of the public copies and remain
only in the frozen YouTrack articles:

- the named client organisation used as the worked example in #62 / #63;
- the internal job-number reference;
- the German VS grades stated as governing specific project drawing stock;
- a named reviewer's handle in the #63 decision record.

Restoring these is a client-disclosure decision, not a formatting one. **Not done without an explicit
instruction naming them.** Flagged to Ahmed.

### Changes made

| Surface | Change |
| --- | --- |
| Discussion #61 | §11.1 inventory extended with a fourth column **critically assessing every term** (🟢 core / 🟡 useful / 🟠 marginal / 🔴 redundant). Result: of **73** terms only **29 are core**, 19 useful, **20 marginal** and **5 redundant** — so the real mint is ~48, not 73. Five to drop outright: `Sheet`, `hasAnnotationBlock`, `pageNumber`, `numberOfPages`, `paperSize`. The marginal set clusters in three groups (ISO 7200 manufacturing heritage; IFC completeness; identifier fragments that are parser output rather than extraction targets), plus `ContainerState`, which is never printed on a sheet. Ratings are flagged as a **pre-registered prediction** for next step 3 to test, not a decision taken |
| Discussion #61 | New **§11.1 consolidated inventory** — every class and property in one table with its source (standard clause / external vocabulary / **ADIRO**-minted) and what it denotes in ADIRO's own words: 18 classes, 29 object properties, 24 data properties. Also reconciled the §11 headline counts, which said “~20 / ~20 / 13” — an estimate that predated writing out §4 and §10 |
| Discussions #61–#64 | Mirror headers **inverted** — each now states it is the authoritative version and that the YouTrack copy is frozen. #61 gains the standards-licensing notice and the restored ISO 7200 table (19 rows, field names + `Obl.`) and the "8 mandatory + 11 optional" detail |
| `RES-A-9`, `RES-A-21`, `RES-A-22`, `RES-A-23` | Title prefixed `[FROZEN → GitHub Discussion #NN]`; freeze notice appended naming the replacement, what still differs, and (for #62/#63) which decisions are still open and where to answer them |
| `AGENTS.md` | New **Team workflow** preamble: GitHub is the source of truth for ADIRO docs; the four articles are frozen; YouTrack stays the tracker and the internal KB. Plus the narrowed standards-publishing rule |
| `docs/modularization/aec_titleblock-build-plan.md` | Every "design authority" reference repointed from `RES-A-23`/`RES-A-9` to Discussions #64/#61; source-of-truth note added |
| `changelogs/aec_titleblock.md`, `src/aec_titleblock.ttl` | Design-authority pointers repointed to Discussion #64 |
| [RES-89](https://bhmlrnd.youtrack.cloud/issue/RES-89) | Header repointed to the Discussions; note that the articles are frozen |

### Known consequences

- **The MCP cannot delete YouTrack articles** (create / get / update / search only), so deletion was never
  available here anyway. Freezing is the better outcome regardless.
- **The freeze notices sit at the *end* of each article body**, because `update_article` can only replace the
  whole content or append. The `[FROZEN → …]` **title prefix** is the reliable signal — it shows in the KB tree,
  in search results and anywhere the article is linked in YouTrack. If a top-of-page banner is wanted, each
  article needs a full-content rewrite.
- **Discussions cannot carry an assignee or a review state.** Reviews of the §1.1 reconciliation are still
  tracked through RES-89; only the document text moved.
- Historical entries in this worklog still cite `RES-A-23 §N` — accurate as written; the freeze notices route a
  reader onward.

---

## 2026-08-11 (latest) — DiCon evaluated: mint, not align

**Issue:** [RES-89](https://bhmlrnd.youtrack.cloud/issue/RES-89) · **Branch:** `res-89-aec-titleblock-tbox`
No `src/` changes. Closes the DiCon next-step opened in the entry below, and with it the last external dependency
in the build plan.

### Method, stated because it bounds the conclusion

**Read:** the `dici:` Information module documentation, the `dica:` Agents module documentation, the DiCon↔ICDD
alignment TTL, and the source repository's commit activity. **Not read:** the raw `Information.ttl` / `Agents.ttl`.

So the "exact match" and "partial" judgements below are solid; the **"absent" judgements mean *absent from the
module documentation*** — strong, but not proof. **If the container-state borrow ever becomes a real
`skos:exactMatch` axiom, read the raw TTL first.**

### What DiCon is

An Aalto University / EU **BIM4EEB** ontology suite (also published as DICO): 10 modules under
`https://w3id.org/digitalconstruction/0.5/`, CC BY 4.0, **BFO-aligned** (classes organised under Basic Formal
Ontology / IAO). It formalises ISO 19650 information management.

**It is dormant:** source repo last pushed **2022-06-30**, still at **v0.5**, never reached 1.0.

### Scored against RES-A-9 §7

| §7 field | In DiCon? |
| --- | --- |
| Container state | ✅ **Exact match** — `dici:hasContainerState` → `dici:InformationContainerState`, named individuals `Initial` / `WorkInProgress` / `Shared` / `Published` / `Archived` |
| Originator | 🟡 Partial — `dici:isCreatedBy` / `isProducedBy`, generic; does not disambiguate originator vs legal owner vs client, which is the hard part |
| Volume/System, Level/Location | 🟡 Conceptual analogues only — `ProductBreakdownStructure`, `LocationBreakdownStructure`; not the printed code strings |
| Suitability S0–S7 | ❌ Absent |
| Discipline | ❌ Absent — `dica:` has role classes (`ProjectLeaderRole`, `SiteManagerRole`, …) but explicitly no discipline vocabulary |
| Type, sequential number | ❌ Absent |

Nothing title-block-specific at all: no title-block region model, **no `Revision` class** (so none of RES-A-9 §5 —
index, date of issue, description, supersession), no scale, paper size, projection method, plan key,
confidentiality, or checked/approved-by. Its one "title-like" property, `hasMessageSubject`, belongs to `Message`.
Its ICDD alignment also makes `ct:Document` a superclass of `dici:Dataset`, which is not a reading to inherit.

### Decision — mint our own

Two costs settle it. Importing DiCon pulls **BFO/IAO into a suite governed by a blocking OWL 2 DL gate**
([RES-36](https://bhmlrnd.youtrack.cloud/issue/RES-36)) — a large, hard-to-debug addition to exactly what that gate
checks, in exchange for one field. And it would be a permanent dependency on a research project finished four
years ago.

**What to take:** the container-state **modelling pattern** only. DiCon represents the four ISO 19650 states as
*named individuals* of a state class — the same shape ADIRO proposed, arrived at independently from the same
clause. Worth citing at review as evidence that individuals-not-enum is the normal reading; now recorded in
RES-A-23 §6. Optionally two or three `skos:exactMatch` axioms later *if* DiCon interop is ever required — the same
on-demand treatment as ICDD. DiCon also carries an `Initial` state that ISO 19650's four do not: noted as a
question, **not** adopted just because DiCon has it.

**Also recorded, because it will be re-asked:** no OWL vocabulary models a title block as the region that asserts
document metadata. Published title-block work is detection/extraction, not semantics. Written up as RES-A-9 §1.4
so the question is not re-opened from scratch.

### Consequences

- **RES-A-23 §11 q9 answered; pass 4 ungated.**
- **Passes 1–4 now have no remaining external dependency.** The only blocks left in the whole plan are internal:
  the §1.1 reconciliation ahead of pass 1, and RDF-star vs reification ahead of pass 5.
- Reuse position, final: **IFC** is the alignment that pays (13 correspondences, vs ~4 for `ct:` and ~1 for
  DiCon); `dcterms:` / `skos:` / `prov:` / lexvo are direct reuse; **ICDD and DiCon are optional on-demand
  alignments** — neither a foundation nor an acceptance criterion.
- The highest-value open *research* task is now RES-A-9 next step 3: sample 20–30 real title blocks and record
  which fields actually appear.

### Changes made

| Surface | Change |
| --- | --- |
| [RES-A-9](https://bhmlrnd.youtrack.cloud/articles/RES-A-9) | DiCon row in §1.2 rewritten with the full evaluation and the method caveat; new **§1.4 "There is no title-block ontology"**; finding 4 notes no external ontology models a revision history; §7 changed from "check DiCon first" to "mint this section"; §8 notes none of these fields exist externally; §9 states IFC is the alignment to build if only one is; §11 summary and next step 2 closed |
| [RES-A-23](https://bhmlrnd.youtrack.cloud/articles/RES-A-23) | §4 split into 4.1 ICDD / 4.2 DiCon (full evaluation, costs, method caveat) / 4.3 reuse priority; §5 pass 4 **ungated** plus a statement that passes 1–4 have no external dependency; §6 gains the container-state corroboration note and the `Initial`-state question; §10 extends "not an acceptance criterion" to DiCon and IFC; §11 q9 struck as answered |
| [RES-89](https://bhmlrnd.youtrack.cloud/issue/RES-89) | DiCon moved from open question to settled; pass 4 ungated; estimate note trimmed |
| Discussions [#61](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/61), [#64](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/64) | Same changes in the redacted public copies |

### Next steps

As in the entry below, minus the DiCon item. The critical path is now entirely internal: **sign off the §1.1
reconciliation (pass 0)**, answer q7 (`dm:DrawingRevision` sufficiency) and q8 (SHACL shapes location), then open
PR 0. The un-run HermiT gate (no Java on this machine) remains the one verification gap before a PR.

---

## 2026-08-11 (later) — prior-art check: ICDD demoted, module separation confirmed

**Issue:** [RES-89](https://bhmlrnd.youtrack.cloud/issue/RES-89) · **Branch:** `res-89-aec-titleblock-tbox`
No `src/` changes — this entry is a **decision and documentation** round following a prior-art review.

### What prompted it

The question "are there title block ontologies already?" — asked before ~40 properties get minted. Worth
recording the answer, because it is the kind of thing that gets re-asked.

### Findings

**There is no dedicated title-block ontology.** Nothing models a title block as *a region that asserts document
metadata* — the [RES-A-9](https://bhmlrnd.youtrack.cloud/articles/RES-A-9) finding-2 distinction. Published work
on title blocks is detection/extraction, not semantics. The decision to mint stands.

Three things that *do* exist, and how they changed the plan:

| Candidate | Verdict |
| --- | --- |
| **ISO 21597-1 (ICDD)** `ct:` | **Demoted.** The normative `Container.rdf` is publicly resolvable at `https://standards.iso.org/iso/21597/-1/ed-1/en/Container.rdf` — it was never an acquisition problem. More importantly it is **container and file mechanics plus party provenance**: `Party`/`Person`/`Organisation`, `Document` + 5 subclasses, `ContainerDescription`, `Linkset`, and `filename`/`filetype`/`format`/`checksum`/`creationDate`/`modificationDate`/`priorVersion`/`nextVersion`/`createdBy`/`modifiedBy`/`publishedBy`. **No `title`/`identifier`/`description` of its own** (those come from `dcterms:`), no `checkedBy`/`approvedBy`, and it spells `Organisation`. It supplies almost none of the ~40 content fields. |
| **DiCon** — Digital Construction Ontologies, `dici:` Information module, CC BY 4.0 | **New candidate.** Formalises ISO 19650 information containers, aligned to ISO 21597-1 / IFC / BFO / PROV-O. May already cover the [RES-A-9 §7](https://bhmlrnd.youtrack.cloud/articles/RES-A-9) ISO 19650 layer that ADIRO would otherwise mint by hand. *Assessed from the specification landing page only at this point — evaluated properly in the entry above.* |
| **RUB `exdoc`** — ICDD extension | **Not relevant.** Extends ICDD with database-connectivity document types (relational, InfluxDB). Nothing about drawings. |

### Decisions taken

1. **ICDD demoted from "primary source" to "export contract", and de-blocked.** RES-A-9 §1.2 called it "the
   single most important one for ADIRO" and finding 1 said "do not reinvent — subclass and align". That
   overstatement had a real cost: it parked the alignment work behind "obtain the standards" while implying ICDD
   would deliver fields it does not contain. Its genuine value is interchange — a published ICDD ↔ DIN SPEC
   91391-2 mapping means it is what the German CDE ecosystem maps to — so alignment is worth ~4 class axioms
   **when a real ICDD/openCDE deliverable requirement exists**, and not before. **No build pass is blocked on it,
   and it is explicitly not an acceptance criterion.**
2. **Reuse priority reordered:** internal (`aec_drawing_metadata`) → `dcterms:`/`skos:`/`prov:`/lexvo → **DiCon**
   (evaluate before pass 4) → **IFC** (the alignment that pays — 13 usable correspondences in RES-A-9 §9 against
   ~4 for `ct:`) → ICDD last and on demand.
3. **✅ SETTLED — `aec_titleblock` stays a separate module**, agreed by **Ahmed Elnagar and Alessio Lombardi**.
   Two reasons beyond the original three: **ease of publishing** (independently releasable and documented, own
   SemVer line, so a title-block release does not drag the region ontology's version along) and **volume** (the
   supporting classes plus seven SKOS schemes and their concept individuals do not belong in a module describing
   six page regions). This closes the decision RES-A-23 called hardest to reverse. **Corollary:** any ICDD
   class-alignment axioms live in `aec_titleblock`, not pushed back into `aec_drawing_metadata`.
   - *Note:* this does **not** decide the §1.1 reconciliation. Option A reuses `dm:` classes across the module
     boundary via `owl:imports` — normal layering, not a merge. But reason 5 (volume) is worth weighing when
     reviewing §1.1, and that tension is flagged in the article.

### Changes made

| Surface | Change |
| --- | --- |
| [RES-A-9](https://bhmlrnd.youtrack.cloud/articles/RES-A-9) | §1.2 ICDD row rewritten with verified `ct:` local names and an honest scope assessment; new DiCon row; finding 1 rewritten as "align for interchange, not coverage" with the original wording quoted so the change is auditable; §7 gated on the DiCon check; §9 notes IFC is the richer alignment; §11 summary and next steps reordered — next step 1 closed, DiCon added as the new step 2 |
| [RES-A-23](https://bhmlrnd.youtrack.cloud/articles/RES-A-23) | Second revision note; §2 gains reasons 4–5 and a **DECIDED** box; §4 rewritten (ICDD demoted/de-blocked, reuse priority list); §5 drops the deferred alignment pass and gates pass 4 on DiCon; §10 adds "ICDD alignment is not an acceptance criterion" and the compat-diff caveat; §11 q1 struck as settled, q9 (DiCon) and q10 (is there an actual ICDD requirement?) added |
| [RES-89](https://bhmlrnd.youtrack.cloud/issue/RES-89) | Description restructured into settled ✅ / open ⬜ decisions; reuse section reprioritised; pass 4 gated on DiCon; alignment removed from the pass list; estimate note extended to cover the DiCon work |
| Discussions [#61](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/61), [#64](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/64) | Same changes, in the redacted public copies. #62 / #63 touched only for the date fix below |
| `docs/modularization/aec_titleblock-build-plan.md` | New "Settled decisions (do not relitigate here)" block; PR table drops PR 7 (alignment) and gates PR 5 on DiCon |

Also fixed: the `2026-08-10` date stamps in the revised articles and their published copies were wrong by a day —
all work happened `2026-08-11`. Corrected across all four discussions and both articles. This closes the open
thread logged in the previous entry.

### Next steps

Unchanged from the previous entry, with two additions and one removal:

- **Added:** read DiCon's `dici:` module file and decide align-vs-mint for the ISO 19650 layer. Blocks pass 4
  only; passes 1–3 are unaffected. *(Done later the same day — see the entry above.)*
- **Added:** establish whether any ICDD / openCDE deliverable requirement actually exists. If not, the alignment
  axioms stay unbuilt — nobody should build them speculatively.
- **Removed:** "obtain the normative `Container.rdf`" as a blocker, anywhere.

---

## 2026-08-11 — `aec_titleblock` module: plan + pass-1 plumbing

**Issue:** [RES-89](https://bhmlrnd.youtrack.cloud/issue/RES-89) (State: `Backlog` — deliberately not moved to
`In Progress`; see *Open threads*) · **Branch:** `res-89-aec-titleblock-tbox` (off `origin/main` @ `0246450`)
**Design authority:** [RES-A-23](https://bhmlrnd.youtrack.cloud/articles/RES-A-23)

### 1. Discovered that the build spec was out of date

The starting point was [RES-A-23](https://bhmlrnd.youtrack.cloud/articles/RES-A-23), which described this work
as greenfield. Reading the repo contradicted three of its premises:

| RES-A-23 said | Reality in the repo | Consequence |
| --- | --- | --- |
| `aec_drawing_metadata.ttl` is 195 lines, declares `:Titleblock` "and nothing more" — greenfield | **422 lines**, and already declares `:Person`, `:Project`, `:DrawingSheet`, `:DrawingRevision`, `:StatusCode`, `:DrawingPackage` plus ~12 title-block-adjacent properties | ~⅓ of the planned core-field list already exists. Passes 1–2 as specified could not satisfy the "no duplicate terms" acceptance criterion |
| Mint under `github.io`, let the deferred migration sweep it | Already migrated to `w3id.org/adiro` ([RES-98](https://bhmlrnd.youtrack.cloud/issue/RES-98), commit `de857bc`, PR #60) | Mint under w3id directly |
| Incidental defect: `versionIRI` 1.0.0 vs `versionInfo` 2.0.0 | Both read `2.0.0`; agreement is CI-enforced ([RES-66](https://bhmlrnd.youtrack.cloud/issue/RES-66)) | Dropped from scope |

Two further corrections: there is **no `aec_core` module** (referenced by RES-A-23 §2 and §10), and a
**blocking** OWL 2 DL reasoning gate ([RES-36](https://bhmlrnd.youtrack.cloud/issue/RES-36)) has been added
since the spec was written.

**The material finding** is not the stale line counts — it is that the existing properties hang off
`:DrawingSheet` / `:DrawingRevision`, **not** `:Titleblock`. That is the opposite of the domain rule in
[RES-A-9](https://bhmlrnd.youtrack.cloud/articles/RES-A-9) finding 2. The repo therefore holds a *competing
model of the same information*, which makes this a reconciliation exercise rather than a naming clash.

### 2. Updated the authorities to match

- **[RES-A-23](https://bhmlrnd.youtrack.cloud/articles/RES-A-23) revised** — added a revision note listing the
  wrong premises, a new §1.1 carrying the overlap table and three reconciliation options, a **pass 0**, the
  corrected IRI base, the blocking reasoner in §10, and the SHACL/`src/*.ttl` trap in §9. Changed decisions are
  tagged `[revised 2026-08-10]` inline; settled open questions are struck through rather than deleted.
- **[RES-89](https://bhmlrnd.youtrack.cloud/issue/RES-89) description updated** to match, with the corrections
  marked as corrections so the change is auditable.
- **`docs/modularization/aec_titleblock-build-plan.md` added** (new) — the repo-side execution plan. Initially
  it duplicated the reconciliation argument; **trimmed to defer to RES-A-23** as the single design authority,
  keeping only repo mechanics (file checklist, CI gates, PR sequence). 229 → 117 lines.

### 3. Implemented pass-1 plumbing

**Deliberate scope call:** RES-A-23 §5 places **pass 0** (the §1.1 reconciliation) before any TTL, because it
determines which terms get minted. So the module skeleton contains **zero domain terms** — two labelled
placeholder sections mark where classes and properties go and state what is pending. This makes all of the
plumbing testable now without pre-empting sign-off; if the reconciliation lands differently, nothing here needs
withdrawing, only adding to.

*New*

| File | Content |
| --- | --- |
| `src/aec_titleblock.ttl` | Ontology declaration at `https://w3id.org/adiro/aec_titleblock`, `versionIRI …/0.1.0` + `versionInfo "0.1.0"`, `dcterms:*` provenance matching siblings, `owl:imports aec_drawing_metadata`, and `:extractionHint` (the one annotation property the extraction profile needs) |
| `src/aec_titleblock.display.json` | `{"version": 1, "nodePositions": {}}` — populated when classes exist |
| `changelogs/aec_titleblock.md` | `[Unreleased]` skeleton entry, plus an explicit "no domain terms yet, and why" |

*Modified*

| File | Change | Why it matters |
| --- | --- | --- |
| `src/catalog-v001.xml` | added the `aec_titleblock` → local-file mapping | **omitting it breaks offline import resolution in the reasoning CI** |
| `scripts/generate_docs.py` | `'aec_titleblock': 2`, siblings renumbered 3–6 | otherwise it sorts to `999` and the docs order is wrong |
| `mkdocs.yml` | nav entry under `Ontologies:`; `ai/` added to `exclude_docs` | the nav is curated; this worklog is dev docs, not published site content |
| `CHANGELOG.md` | rollup row `aec_titleblock` \| `0.1.0` | |
| `docs/**` | regenerated | mandatory per `AGENTS.md` "Keep in sync"; never hand-edited |

### 4. Verification

| Check | Result |
| --- | --- |
| `validate_ontology.py src/aec_titleblock.ttl` | **pass** |
| `validate_ontology.py` (all 5 modules) | **pass** — no regression |
| `generate_docs.py` | **5/5 clean, no warnings**; emit order confirmed metadata → titleblock → common → domain-common → facade |
| `mkdocs build` | **clean** (only Material's generic MkDocs-2.0 notice) |
| `compat_diff.py --markdown` | new module correctly **skipped** — "no released snapshot to diff against yet" |
| `run_reasoning.sh` (HermiT) | **NOT RUN — no Java runtime on the dev machine.** This is the *blocking* gate. The skeleton is an annotation property plus an import, so it is almost certainly consistent, but this was **not verified**. Install `EclipseAdoptium.Temurin.17.JDK` and run before opening the PR |

Two notes on the verification, both worth carrying forward:

- **"compat-diff reports additive" is not assertable for a brand-new module** — there is no released snapshot to
  diff against. That acceptance criterion only becomes meaningful from PR 2 onward. Do not read the skip as a
  failure. (The forecast also shows all four existing modules heading to MAJOR — that is the pre-existing w3id
  migration, unrelated to this work.)
- **`generate_docs.py` output is not byte-stable.** Regenerating swapped `Detail`/`Section` inside a union class
  in `docs/aec_drawing_metadata.html` — pyLODE set-ordering, semantically identical. It means CI's commit-back
  can produce phantom diffs. Not caused by this work; **worth its own GitHub issue.**

### 5. Published four research notes to GitHub Discussions

Separate task, same session. Copies of the internal ADIRO knowledge-base articles, in the **Ideas** category:

| Discussion | Source article |
| --- | --- |
| [#61](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/61) ADIRO title-block properties — Data vs Object property design | `RES-A-9`, **trimmed** |
| [#62](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/62) Evaluating a predicted KG against a ground-truth KG | `RES-A-21` |
| [#63](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/63) Ground-truth labelling: ontology-bound keys or verbatim captions? | `RES-A-22` |
| [#64](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/64) Building the ADIRO title-block TBox | `RES-A-23` (the revised version) |

Because **this repository is public**, each copy was processed before publishing:

- **Redacted** (verified absent from all four): client and project names, real source filenames, corpus
  statistics, applied security classifications, the InfoSec-concept pointers, the private LLM deployment
  reference, a reviewer's handle, and every `youtrack.cloud` URL.
- **Kept deliberately:** the *name* of the German VS classification scheme, because the
  `ConfidentialityClassification` scheme has to hold those values — what was removed is any statement that BH
  drawing stock is governed by it.
- **`RES-A-9` trimmed** — its ISO 7200 table now maps *clause number → ADIRO property → type → range*, dropping
  the reproduced field names and obligation column, since ISO texts are licensed and this repo is public. A
  header note states the reduction and points to the standards list.
- **Mirror header on each**, naming the source article, the as-of date, and that the canonical version is
  internal — so no one treats the GitHub copy as authoritative.
- Internal IDs left as plain text (not dead links); the four cross-link each other with real URLs.

**`RES-A-13` (the extraction test plan) was deliberately NOT published** — it carries client/project names and
classification material and needs a redaction pass plus sign-off from Alessio. The work, if wanted later, is a
scoped redaction of its dataset sections, not a rewrite.

### 6. Git state

**Everything above is staged but NOT committed** on `res-89-aec-titleblock-tbox`. 19 paths. Nothing pushed; no
PR opened.

### Next steps

**Blocking — before any domain terms are minted**

1. **Sign off the [RES-A-23 §1.1](https://bhmlrnd.youtrack.cloud/articles/RES-A-23) reconciliation (pass 0).**
   Proposal on the table: reuse `dm:` classes as ranges (A) + mint properties as a parallel assertion layer (B)
   + reject deprecate-and-migrate (C). Reviewers on RES-89: `alelom`, `Zaalouk`, `tianyang.huang`.
2. **Answer §11 q7** — is `dm:DrawingRevision` sufficient, or does the fuller
   [RES-A-9 §5](https://bhmlrnd.youtrack.cloud/articles/RES-A-9) revision model need its own class? Two revision
   classes in one imported suite is a real cost.
3. **Answer §11 q8** — where the SHACL shapes live, given that anything matching `src/*.ttl` is treated as an
   ontology module and a SHACL file would fail validation. Cheap to decide now.

**Then**

4. **PR 0** — this branch: worklog + repo plan + skeleton plumbing + the §1.1 decision record. File the GitHub
   issue first (ADIRO is open-source; GitHub → YouTrack is one-way, per
   [MAN-A-3](https://bhmlrnd.youtrack.cloud/articles/MAN-A-3)). Install Java and run the reasoner first if the
   PR should show a green gate.
5. **PR 1** — fill the two placeholder sections: `Organization`, `SourceFile`, `BoundingBox` (if the proposal
   holds) and `assertsMetadataFor`. Note that needs a `Document` concept and `aec_drawing_metadata` has
   `DrawingSheet` but no `Document` — one more thing the reconciliation should settle.
6. **PRs 2 and 3 in parallel** (both depend only on PR 1) — the 17 core properties, and the SKOS enumerations.
   Watch ROBOT `duplicate_label` against `dm:` labels: a hit is the §1.1 signal, not noise.
7. **PR 4** — `scripts/build_extraction_profile.py` with the `tb:`-only filter as a *tested* behaviour, plus the
   shapes. The extraction experiment cannot properly start without this.

### Open threads / caveats

- **RES-89 is still `Backlog`.** Not moved to `In Progress` on purpose: its 16 h / `L` estimate predates the
  §1.1 reconciliation, so it should be re-estimated or the reconciliation split out as its own issue at Sprint
  planning. That is a planning decision, not an implementation one.
- **The blocking reasoning gate has not been run locally** (§4). Highest-priority verification gap.
- **`generate_docs.py` non-determinism** (§4) — unticketed.
- **Date stamps in the revised RES-A-23 and its published copy read `2026-08-10`**; the work was done
  `2026-08-11`. Cosmetic, but it is a factual stamp in published content — worth correcting on the next edit of
  those artefacts.
- **The `aec_titleblock` skeleton is deliberately term-free.** If a future session finds an "empty" module and
  assumes it was left unfinished, read §3 above before adding anything: the emptiness is the pass-0 gate.
