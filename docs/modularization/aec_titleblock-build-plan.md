# `aec_titleblock` — repo-side build plan

**Issue:** [RES-89](https://bhmlrnd.youtrack.cloud/issue/RES-89) (State: `Backlog` at time of writing — not yet started)
**Design authority:** [Discussion #64](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/64) · **Research input:** [Discussion #61](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/61) · **Consumer:** RES-A-13 (internal test plan, not published)
**Branch:** `res-89-aec-titleblock-tbox` · **Status:** PR [#66](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/66) open — 9 terms (§1); placement decision resolved 2026-08-19, Option 1 (see `titleblock-placement-option1-plan.md`); `assertsCrossReferenceNumber` added and three unevidenced standards-derived terms withdrawn, both from field-survey evidence (see `titleblock-field-survey-2026-09.md`)

## What this document is (and is not)

[Discussion #64](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/64) is the **design authority** — the
ontology-engineering decisions (new module vs extension, the reconciliation with terms
`aec_drawing_metadata` already holds, SKOS vs `owl:oneOf`, IRIs, the property template, SHACL rules,
acceptance criteria, open questions). **Read it first, including the revision note at the top.** None of it
is restated here.

> **Source of truth (2026-08-11).** ADIRO documentation is maintained on **GitHub**. The former YouTrack
> knowledge-base articles (`RES-A-9`, `RES-A-21`, `RES-A-22`, `RES-A-23`) are **frozen** and each points at
> its Discussion; do not edit or cite them. Internal YouTrack issues (e.g. `RES-89`) remain the tracking
> system, and `RES-A-13` — the extraction test plan — stays internal because it carries client and
> classification material.

This document is the **repo-side execution plan**: the files each pass touches, the CI gates it must clear,
and the local commands to run. It is deliberately thin — everything that is a *modelling* decision belongs in
Discussion #64, so there is one place to change when a decision changes.

> **Reconciliation with existing terms — RESOLVED 2026-08-19 (Option 1).** `aec_drawing_metadata` already
> declares `:Person`, `:Project`, `:DrawingSheet`, `:DrawingRevision` and ~12 title-block-adjacent properties.
> For the 10 content properties that overlap (drawing number, title, scale, sheet size, revision code, issue
> date, author/checker/approver, status), **`aec_titleblock` reuses `dm:` directly — no `tb:` counterpart, no
> parallel assertion layer.** The classes (`Person`, `Project`, `DrawingSheet`, `DrawingRevision`) were already
> being reused, unaffected by this. Full reasoning and the trade-offs accepted:
> `docs/modularization/titleblock-placement-option1-plan.md`. Recorded in
> [Discussion #64 §1.1](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/64) and in the TTL's
> header/footer. Closes what this document previously called "the largest open decision in the whole plan".

### Settled decisions (do not relitigate here)

- **`aec_titleblock` is a separate module importing `aec_drawing_metadata`** — decided 2026-08-11 by Ahmed
  Elnagar and Alessio Lombardi, on **ease of publishing** (independently releasable and documented, with its own
  SemVer line, so a title-block release does not drag the region ontology's version along) and **volume** (the
  supporting classes plus seven SKOS schemes and their concept individuals do not belong in a module describing
  six page regions). Recorded in [Discussion #64 §2](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/64).
- **Mint under `https://w3id.org/adiro/aec_titleblock#` at `0.1.0`.**
- **ISO 21597-1 (ICDD) blocks nothing.** Earlier drafts deferred all alignment axioms until the normative
  `Container.rdf` was obtained; it is in fact publicly resolvable, *and* `ct:` carries almost none of the
  title-block content fields. Alignment is ~4 additive class axioms, conditional on a real ICDD/openCDE
  deliverable requirement, and belongs **in this module** (the modules stay separate). See
  [Discussion #64 §4](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/64).

## 1. Current state of `src/aec_titleblock.ttl`

**8 terms, all validating.** Written 2026-08-11; revised 2026-08-13 after the first review round on PR
[#66](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/66); `assertsCrossReferenceNumber` added
2026-09-01 and four unevidenced terms withdrawn 2026-09-11/14, all from a four-project field-frequency survey
(§1a, §1b below). `KeyPlan` from the same survey landed in `aec_drawing_metadata`, not here (§1c).

| Kind | Terms |
| --- | --- |
| Class (1) | `Organization` |
| Object properties (3) | `assertsMetadataFor`, `assertsClient`, `assertsOriginator` |
| Datatype properties (3) | `organizationName`, `dimensionUnits`, `assertsCrossReferenceNumber` |
| Annotation property (1) | `extractionHint` |

### 1a. `assertsCrossReferenceNumber` — added 2026-09-01

Ahmed Zaalouk's field-frequency survey of four real BH projects (`docs/modularization/titleblock-field-survey-2026-09.md`)
found that real sheets often print a **second** drawing-numbering system alongside `dm:drawingIdentifier` —
a design-team-internal number, a client/EDMS document number (e.g. Aconex), or a sketch/site-advice reference —
recurring in 3 of 4 sampled projects under different labels. Not in the original 73-term brainstorm. Minted as a
single datatype property, string-valued and stored verbatim rather than parsed into segments, with the observed
labels kept as `skos:altLabel`s and no controlled vocabulary for "which system issued it" (the `DocumentType`
lesson: an empty scheme cannot be reviewed).

The same survey surfaced a second candidate gap — a contractor/consultant/engineer/architect organisation role,
present in all four projects — which was **deliberately parked, not minted**: `assertsOriginator` already covers
the general case, and the four candidate names (`assertsContractor`, `assertsEngineer`, `assertsArchitect`,
`assertsConsultant`) need a team discussion on shape before any of them land. See the survey doc §3.1, §5.

### 1b. Four terms withdrawn 2026-09-11 and 2026-09-14 — the survey cuts both ways

The survey is evidence for removal as well as addition. `supplementaryTitle` (ISO 7200 §5.2.3),
`numberOfSheets` (§5.1.7), `planKey` (DIN SPEC 91391-1) and `sheetNumber` (§5.1.6) appeared in **none** of the
four sampled projects, so none clears the agreed `<40%-of-sheets` rule. All had been minted from a standards
reading rather than from drawings — the same basis the `hasLegalOwner` withdrawal already rejected ("the
standard is not the evidence — the drawings are"). Recorded in the TTL footer §(a3).

Two caveats worth keeping visible:

- **The sheet-position concept is now absent entirely**, not half-modelled. `numberOfSheets` went on 09-11 and
  `sheetNumber` followed on 09-14. Worth stating plainly that **ISO 7200 §5.1.6 is mandatory** in that standard,
  so dropping `sheetNumber` is a deliberate, evidence-led departure from ISO 7200 rather than an oversight. If
  the team wants ISO 7200 conformance as a stated goal, this is the decision to revisit.
- **`planKey` is withdrawn as unevidenced, not as wrong.** The surveyed corpus is UK/US projects and the plan key
  is German practice, so it is a plausible return when German projects are sampled. That is a sampling gap in the
  survey, not a judgement on the term.

### 1c. `KeyPlan` added 2026-09-14 — but to `aec_drawing_metadata`, not here

The survey's "key plan" field (a small locator diagram showing where the sheet's subject sits in the wider
building or site) was minted as **`dm:KeyPlan`**, a `MetadataContainer` subclass beside `Legend` and
`RevisionTable` — *not* as a `tb:` property. The reason is the module split itself: `dm:` models **detectable
visual regions**, `tb:` models **content the title block asserts as text**. A key plan's value *is* the diagram,
so it is a region. Putting it in `tb:` would have made the first `tb:` term that is not an assertable string.

This also matches Ahmed Zaalouk's position on [PR #66](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/66)
(2026-09-10) that `aec_drawing_metadata` should be the repository for metadata, with `aec_titleblock` importing
what it needs.

**Two consequences to flag rather than discover later:**

- **It adds a new CVAT annotation label.** `KeyPlan` carries `labellableRoot true`, and CVAT class labels derive
  from the IRI local name — so the annotation label set changes. Coordinate per KB
  [DATA-A-9](https://bhmlrnd.youtrack.cloud/articles/DATA-A-9).
- **It widens this PR into a released module.** `aec_drawing_metadata` is at `2.0.0`; `aec_titleblock` is not yet
  released. The addition is non-breaking (`TERM_ADDED`) and the module was *already* forecast MAJOR for other
  accumulated unreleased reasons, so the forecast does not move — but a PR scoped to the title-block module now
  touches `dm:`, which reviewers should be told rather than left to notice. Backing it out means reverting
  `src/aec_drawing_metadata.ttl` and its changelog entry, dropping this section and the survey-row correction,
  then regenerating — not a single-commit revert.

**Evidence quality, stated honestly.** The survey records "key plan" on two of four projects at 100% each, but
only one of the two descriptions actually describes a key plan ("denotes the location of the drawing in plan",
value type *Sketch*). The other project's row describes copyright statements and disclaimers, which reads like a
mislabelled cell rather than a key plan. So the real evidence is **one solid project plus one doubtful one**, not
two clean ones. That is still better evidence than any of the four withdrawn terms had (zero), but it is not the
clean 2-of-4 the raw table suggests, and the original survey §2 row — which filed "key plan" under *already
covered by `dm:Note`/`dm:Legend`* — was wrong to lump it with the notes fields on the strength of that
description.

**Naming convention (review feedback):** value-bearing object properties are `asserts<Thing>`, not
`has<Thing>`. A title block states a claim, not a verified fact, and the property name is the cheapest place to
make that visible at every call site — it also keeps `tb:` terms obviously distinct from their `dm:`
counterparts, so the two layers cannot be mistaken for each other.

**Withdrawn in review round 1:** `hasLegalOwner` (a title block does not normally express legal ownership —
deferred pending the survey), and `DocumentType` / `DocumentTypeScheme` / `hasDocumentType` (deferred to a later
pass so the scheme lands *with* its values; an empty controlled vocabulary cannot be used).

**Selection rule:** a term is in this version only if it has **no counterpart anywhere in
`aec_drawing_metadata`**. That is what makes the first PR safe to review before the placement decision — nothing
here is a second vocabulary for an existing concept. The TTL's footer lists, in the file itself, every term
deferred for that reason and every term dropped as redundant, so the omissions are legible to a reader of the
module rather than only to a reader of this plan.

**Provisional choice recorded in the file:** domains for `tb:`-minted properties are `dm:Titleblock`, consistent
with the module's stated purpose, and `assertsMetadataFor` ranges over `dm:DrawingSheet` rather than a newly
minted `Document` class. Neither is decided by the Option 1 placement resolution above — that decision was only
about whether to mint `tb:` counterparts for the 10 overlapping content properties, not about whether ADIRO ever
needs a `Document` class distinct from `DrawingSheet`. That is a separate, still-open gap: two sheets in the same
document set can currently disagree with no node to reconcile them against. See
`titleblock-placement-option1-plan.md` §3, point 4. At `0.1.0` a reversal costs a rename, not a migration.

**Verified — all gates, including the blocking one:**

| Check | Result |
| --- | --- |
| `validate_ontology.py` (module, then all five) | pass, no regression |
| Every property has label + domain + range + comment | pass (checked via rdflib) |
| Duplicate `rdfs:label` across the merged suite | **0** — clean by construction, given the selection rule |
| **HermiT consistency + unsatisfiable classes** | **pass — `reason exit code: 0`** on the merged 5-module suite |
| ROBOT `report` | **0 ERROR.** 11 `missing_definition` WARN + 1 `missing_superclass` INFO from this module, both matching 213 / 19 pre-existing rows of the same type — i.e. consistent with existing repo practice, not a new divergence |
| `generate_docs.py` / `mkdocs build` | 5/5 clean / clean |

Java 17 (Temurin) was installed to run the reasoner; `scripts/run_reasoning.sh` fetches ROBOT to
`.tools/robot.jar` on first use.

**One defect the reasoner caught, and it was in the plan rather than the module.** The first draft of the
TTL followed the property template's `rdfs:label "x"@en, "y"@de` form and ROBOT flagged 4 ERRORs
(`multiple_labels`). Fixed here — one English `rdfs:label`, German in `skos:altLabel` — and **fixed at
source** in Discussion #64 §7 and in `AGENTS.md`, because written the old way the full ~40-property
vocabulary would have produced ~80 ERRORs.

## 2. Files each pass touches

[Discussion #64 §5](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/64) defines the passes semantically. Here is the
repo-mechanics checklist — several of these are easy to forget and one of them breaks CI if missed.

**Pass 1 (skeleton) — the only pass with repo plumbing:**

| File | Change | Why |
| --- | --- | --- |
| `src/aec_titleblock.ttl` | new | the module |
| `src/catalog-v001.xml` | add `<uri name="https://w3id.org/adiro/aec_titleblock" uri="aec_titleblock.ttl"/>` | **breaks the reasoning CI if missed** — imports resolve offline through this catalog |
| `scripts/generate_docs.py` | add `'aec_titleblock': 2` to `dependency_order` (and renumber the rest) | otherwise it sorts to `999` and the docs order is wrong |
| `mkdocs.yml` | add `- Aec Titleblock: ontologies/aec_titleblock.md` under `Ontologies:` | the nav is curated — see `docs/contribute/adding-ontologies.md` |
| `changelogs/aec_titleblock.md` | new, with an `[Unreleased]` section | the per-module changelog is the source of truth |
| `CHANGELOG.md` | rollup entry | keeps the top-level rollup honest |
| `src/aec_titleblock.display.json` | new (may start as `{"version": 1, "nodePositions": {}}`) | every sibling has one; it is copied into `docs/` and published |
| `docs/**` | regenerate, commit in the same PR | mandatory per `AGENTS.md` "Keep in sync" — never hand-edit generated pages |

**Passes 2–4:** `src/aec_titleblock.ttl` + `changelogs/aec_titleblock.md` + regenerated `docs/` only.

**Pass 5 (provenance):** as above, and blocked on the RDF-star vs reification decision
([Discussion #61](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/61) next step 5). Passes 1–4 are not blocked.

**Also in [RES-89](https://bhmlrnd.youtrack.cloud/issue/RES-89) scope, sequenced after pass 3** (which is when
there is something worth slicing):

- `scripts/build_extraction_profile.py` — generated, never hand-maintained
  ([Discussion #64 §8](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/64)).
- The SHACL shapes ([Discussion #64 §9](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/64)). **Decide the path before
  pass 1:** anything matching `src/*.ttl` is picked up by `scripts/validate_ontology.py`,
  `scripts/generate_docs.py` and `scripts/run_reasoning.sh` as an ontology module, and a SHACL file has no
  `owl:Ontology` declaration or version, so it **fails validation** and would publish as a bogus ontology page.
  Either keep the shapes outside `src/`, or give the file its own `owl:Ontology` header and accept it is
  versioned as a module.

## 3. CI gates every pass must clear

`AGENTS.md` is the authority, and on any conflict the CI files win. Run locally before pushing:

```bash
uv run python scripts/validate_ontology.py src/aec_titleblock.ttl   # after EVERY ttl edit, no exceptions
uv run python scripts/generate_docs.py                              # regenerate docs in the same commit
bash scripts/run_reasoning.sh                                       # the same script CI runs (needs Java 11+)
```

| Gate | Workflow | Blocking? |
| --- | --- | --- |
| Parse, circular-subclass, `owl:Ontology` present, `versionInfo` == `versionIRI` tail == IRI + version ([RES-66](https://bhmlrnd.youtrack.cloud/issue/RES-66)) | `validate-ontology.yml` | **yes** |
| `compat_diff.py` ([RES-67](https://bhmlrnd.youtrack.cloud/issue/RES-67)) — flags a SemVer bump smaller than the change requires; sticky PR comment | `validate-ontology.yml`, `compat-diff-comment.yml` | warn / report-only |
| **HermiT** OWL 2 DL consistency + unsatisfiable-class detection over the merged suite | `ontology-reasoning.yml` ([RES-36](https://bhmlrnd.youtrack.cloud/issue/RES-36)) | **yes** |
| ROBOT `report` (incl. `duplicate_label`) | `ontology-reasoning.yml` | advisory |
| MkDocs build + Pages deploy | `generate-deploy-docs.yml` | on merge to `main` |

Two notes specific to a new module. The reasoner runs over the **merged** suite, so an axiom here can make
another module unsatisfiable — reason locally *before* opening the PR, not after. And ROBOT's `duplicate_label`
check matters more than usual: importing `aec_drawing_metadata` means any `tb:` label colliding with a `dm:`
one surfaces, which is early warning of exactly the
[§1.1](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/64) overlap. Treat such a warning as a design signal, not
noise to suppress.

## 4. PR sequence

**No PR is opened until `src/aec_titleblock.ttl` carries an initial version of the vocabulary.** Documentation
and plumbing alone do not justify a review: a reviewer cannot judge the module without terms to look at, and a
docs-only PR invites a rubber stamp. Decided 2026-08-11.

The first PR therefore bundles what were previously separate PR 0 (documents) and PR 1 (skeleton), plus the
initial term set. Subsequent PRs remain one per pass.

| PR | Content | Depends on |
| --- | --- | --- |
| **1** | **Initial version.** The design and review documents, the pass-1 plumbing, **and an initial `aec_titleblock.ttl`** — the terms that have no counterpart in `aec_drawing_metadata` | — |
| 2 | ~~The remaining core properties, once the placement decision lands~~ — **not needed.** Resolved as Option 1 (§1): those 10 properties are reused from `dm:` directly and require no new `tb:` terms. This PR is dropped from the sequence | — |
| 3 | SKOS enumerations and their concepts | PR 1 |
| 4 | SHACL shapes + `build_extraction_profile.py` | PR 3 |
| 5 | Extension properties | PR 3 |
| 6 | Extraction-provenance layer, including the timestamp | the RDF-star vs reification decision |
| — | Alignment axioms (IFC, `ct:`, `dano:`) — **not a scheduled PR.** Additive; build when a consumer requires it | a real deliverable requirement |

**What "initial version" means here.** It is deliberately the terms that had no `dm:` counterpart at the time —
everything that overlapped an existing `dm:` term was listed as deferred in the TTL's footer rather than minted,
pending the sheet-level (UC-01) vs titleblock-level placement decision. **That decision is now resolved (Option
1, 2026-08-19)** — see `titleblock-placement-option1-plan.md`. The footer entries for those 10 fields now read
"resolved: reuse `dm:` directly" rather than "pending", and no former PR 2 is required to close them out.

ADIRO is open-source, so issues go on **GitHub**, mirrored one-way into RES
([MAN-A-3](https://bhmlrnd.youtrack.cloud/articles/MAN-A-3)).

## 5. Acceptance criteria

[Discussion #64 §10](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/64) is the checklist, and it already incorporates
the repo's CI gates (HermiT blocking, `duplicate_label` as a design signal, the plumbing items in §1 above, and
the duplicate-term criterion as amended by the §1.1 decision). The duplicate-term criterion is now easier to
state: no `tb:` term duplicates a `dm:` term at all, full stop — Option 1 means there is no longer an
assertion-layer exception to carve out. Nothing further is added here.

## 6. Open questions

[Discussion #64 §11](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/64) — the reconciliation (q6) is the top item, and
q8 (where the SHACL shapes live) and q9 (whether RES-89's 16 h / `L` estimate still holds now that the
reconciliation is in scope) both need answers before pass 1 lands. The estimate is a Sprint-planning call.
