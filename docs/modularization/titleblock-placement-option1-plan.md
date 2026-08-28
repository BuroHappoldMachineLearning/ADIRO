# Option 1 — reuse `aec_drawing_metadata` directly for overlapping title-block fields

**Status:** proposal for team review, **not yet decided or implemented**
**Author:** drafted 2026-08-19, following PR [#66](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/66) review
**Decides:** the "placement question" — [Discussion #64 §1.1](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/64), open question 1
**Scope:** only the 10 fields currently listed as "Deferred (a)" in `src/aec_titleblock.ttl` — see §1

---

## 1. What's actually being decided

Ten fields that a title block prints already exist as properties in `aec_drawing_metadata` (`dm:`), attached to `DrawingSheet` or `DrawingRevision`. They were deliberately **not** duplicated into the new `aec_titleblock` module (`tb:`) — the module's footer lists them under "Deferred pending decision 1" — because minting a second copy pre-empts a design question nobody has actually decided.

| Field | Already exists as | Domain (attaches to) |
| --- | --- | --- |
| Drawing number | `dm:drawingIdentifier` | `DrawingSheet` |
| Title | `dm:drawingTitle` | `DrawingSheet` |
| Scale | `dm:hasScale` | `DrawingSheet` |
| Sheet size | `dm:sheetSize` | `DrawingSheet` |
| Revision code | `dm:revisionCode` | `DrawingRevision` |
| Issue date | `dm:issueDate` | `DrawingRevision` |
| Author | `dm:isAuthoredBy` → `Person` | `DrawingRevision` |
| Checker | `dm:isCheckedBy` → `Person` | `DrawingRevision` |
| Approver | `dm:isApprovedBy` → `Person` | `DrawingRevision` |
| Status | `dm:hasStatusCode` → `StatusCode` | `DrawingRevision` |

**Option 1 = do not build `tb:` counterparts for these 10 at all.** When the extraction pipeline reads a value out of a title block, it writes it **directly** onto the existing `dm:DrawingSheet` / `dm:DrawingRevision` properties — the same properties UC-01's search feature already reads. There is no separate "asserted, not yet validated" layer for these particular fields; the extracted value *is* the sheet's/revision's value.

This is the simplest of the three options considered (see the parked alternatives in §6), and the one to evaluate first because it costs the least to build and changes nothing that already works.

---

## 2. What this buys

- **Zero new terms, zero new module surface for these 10 fields.** `aec_titleblock` stays exactly what it is today (`Organization`, `assertsMetadataFor`, `assertsClient`, `assertsOriginator`, and the six datatype properties already shipped in PR #66) — nothing to add, review, or maintain for this slice.
- **No duplication risk.** There is exactly one place a drawing number can live. UC-01's search queries and the extraction pipeline's writes hit the same property, so they can never silently disagree about where the "real" value is.
- **Zero migration cost, zero risk to UC-01.** `aec_drawing_metadata` does not change at all. UC-01's existing, working, reviewed SPARQL queries are completely unaffected — this is the option that touches the least already-shipped work.
- **A structural fact makes this safer than it might sound.** `aec_drawing_metadata` already restricts every `DrawingSheet` to **exactly one** `Titleblock` (`owl:qualifiedCardinality "1"` on `:contains`/`:Titleblock`). So at the schema level, "the sheet's drawing number" and "this sheet's one title block's drawing number" are already the same fact wearing two names — there is no *structural* room for a sheet to have two title blocks disagreeing with each other. The claim-vs-fact risk this whole placement question worries about mostly lives at a different level (see §4), not in the sheet/title-block relationship itself.

---

## 3. What this costs

Stated plainly, because these are the questions the team should push back on.

**1. No per-title-block staging area for these 10 fields.** Under the original design premise (title block *asserts*, value is *promoted* after validation), an extracted value that turns out to be wrong or ambiguous has nowhere neutral to sit — it goes straight into the same property UC-01 searches on. If the extraction pipeline writes a bad drawing number, it is now *the* drawing number until something overwrites it. This is the real trade-off: **simplicity now, in exchange for losing a built-in "quarantine" step for exactly these fields.**

**2. Whatever validation the pipeline needs, it must do before writing, not after.** Because there's no intermediate assertion layer, "check the extracted value before it becomes the sheet's official value" has to happen in the extraction/validation code, or via SHACL shapes run against `dm:` directly. This was always going to be needed somewhere — Option 1 just means it can't be deferred by using the ontology structure to hold unvalidated data.

**3. Confidence and provenance still have nowhere to live for these fields.** This is true under every option (it's the separately-blocked RDF-star vs reification decision — [RES-A-9](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/61) next step 5) but worth restating: even less so under Option 1, because there's no `tb:` triple at all to attach `extractionConfidence` or `extractedFrom` to for these 10 properties. If per-field confidence on the drawing number or the checker's name turns out to matter, this option makes that harder to retrofit later, not impossible.

**4. This does not touch the separate, still-open "one document, many sheets" conflict.** [RES-A-9](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/61) finding 2 also worries about *different sheets in the same document set* disagreeing (e.g. sheet 1's title block says one client, sheet 5's says another) — that's a document-level concern, and ADIRO currently has no `Document` class above `DrawingSheet` at all. Option 1 neither creates nor solves that; it's an existing gap regardless of which placement option is chosen, and should be tracked separately rather than folded into this decision.

---

## 4. What changes, concretely, if the team agrees

**In the ontology:** nothing is added. The four footer entries in `src/aec_titleblock.ttl` currently reading "Deferred pending decision 1" get updated to record the decision and its reasoning — from "not yet decided" to "decided: reuse `dm:` directly, no `tb:` counterpart, see this document." A one-line addition, not a new term.

**Discussion #64** (`§1.1` and `§11 open question 1`) gets updated from "open" to "resolved: Option 1", with a link to this document, so the reasoning is preserved for whoever asks "why isn't there a `tb:drawingNumber`?" in future.

**Downstream — this is where the real work is, and it's outside the ontology:** the extraction pipeline (`RES-A-13`, `build_extraction_profile.py` and whatever consumes it) needs to be told to write extracted values straight onto `dm:DrawingSheet` / `dm:DrawingRevision`, and any pre-write validation (e.g. "does this look like a real drawing number", "is this revision code plausible") needs to live in that pipeline or in SHACL shapes evaluated before the write — since the ontology itself no longer gives you a free "not yet trusted" state to check first.

**RES-89 / the build plan** get a note that "pass 2" (the 10 currently-blocked properties) is now simply *closed* rather than *pending* — there is nothing left to build for this slice, only pipeline wiring.

---

## 5. Questions worth putting to the team alongside this plan

1. Is losing a per-field "unvalidated staging" step for these 10 fields acceptable, given the pipeline will validate before writing anyway? Or is that exactly the safety net the original design wanted, for exactly these fields (drawing number, revision, sign-off names)?
2. Does anyone have a concrete near-term need for per-value confidence/provenance on the drawing number, revision code, or sign-off names specifically? If yes, Option 1 makes that retrofit harder later.
3. Should the "one document, many sheets can disagree" gap (§3, point 4) become its own tracked issue now, independent of this decision?

---

## 6. Alternatives parked, for comparison

Not developed further here, but named so the team can weigh Option 1 against them rather than in a vacuum:

- **Option 2 — permanent parallel layer.** Mint `tb:` counterparts for all 10 (e.g. `tb:assertsRevisionCode`), kept alongside `dm:`'s versions indefinitely, with an explicit (manual or scripted) promotion step from one to the other.
- **Option 3 — temporary staging layer.** Same shape as Option 2, but framed and documented as scratch space only: extraction writes to `tb:`, a validation step promotes to `dm:` and the `tb:` triple becomes an audit trail rather than a permanent second source of truth.

Both keep the claim-vs-fact distinction Option 1 gives up, at the cost of building and maintaining the promotion logic that Option 1 avoids entirely.

---

## 7. Recommendation

**Adopt Option 1 for these 10 fields**, on the grounds that: it costs nothing to build, it changes nothing UC-01 already relies on, and the schema-level one-title-block-per-sheet constraint means the risk it's giving up is smaller than it first appears. The genuine cost — no built-in quarantine step before a value becomes "official" — should be an explicit, acknowledged trade-off the team signs off on, not something decided by default.

If per-value confidence/provenance turns out to matter for these specific fields once real extraction runs happen, that is the point to revisit toward Option 2/3 — not before.
