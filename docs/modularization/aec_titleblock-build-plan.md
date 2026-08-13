# `aec_titleblock` — repo-side build plan

**Issue:** [RES-89](https://bhmlrnd.youtrack.cloud/issue/RES-89) (State: `Backlog` at time of writing — not yet started)
**Design authority:** [Discussion #64](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/64) · **Research input:** [Discussion #61](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/61) · **Consumer:** RES-A-13 (internal test plan, not published)
**Branch:** `res-89-aec-titleblock-tbox` · **Status:** initial `aec_titleblock.ttl` written (14 terms, §1); first PR not yet opened

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

> **Reconciliation with existing terms.** `aec_drawing_metadata` already declares `:Person`, `:Project`,
> `:DrawingSheet`, `:DrawingRevision` and ~12 title-block-adjacent properties, and they hang off
> `:DrawingSheet`/`:DrawingRevision` rather than `:Titleblock`. That is the largest open decision in the whole
> plan and it is owned by **[Discussion #64 §1.1](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/64)** (proposed:
> reuse the classes, mint the properties as a parallel assertion layer, reject migration), and it is
> complicated by the UC-01 finding in `titleblock-vocabulary-review.md` §2.1. **The initial TTL sidesteps it**
> by minting only terms with no `dm:` counterpart (§1), so the decision is still open and still owed. Do not
> resolve it from this file.

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

**Initial version written 2026-08-11 — 14 terms, all validating.**

| Kind | Terms |
| --- | --- |
| Classes (2) | `Organization`, `DocumentType` (+ `DocumentTypeScheme` as a `skos:ConceptScheme`) |
| Object properties (5) | `assertsMetadataFor`, `hasClient`, `hasLegalOwner`, `hasOriginator`, `hasDocumentType` |
| Datatype properties (6) | `organizationName`, `supplementaryTitle`, `sheetNumber`, `numberOfSheets`, `planKey`, `dimensionUnits` |
| Annotation property (1) | `extractionHint` |

**Selection rule:** a term is in this version only if it has **no counterpart anywhere in
`aec_drawing_metadata`**. That is what makes the first PR safe to review before the placement decision — nothing
here is a second vocabulary for an existing concept. The TTL's footer lists, in the file itself, every term
deferred for that reason and every term dropped as redundant, so the omissions are legible to a reader of the
module rather than only to a reader of this plan.

**Provisional choice recorded in the file:** domains are `dm:Titleblock`, consistent with the module's stated
purpose, and `assertsMetadataFor` ranges over `dm:DrawingSheet` rather than a newly minted `Document` class.
Both are flagged in the TTL header as provisional pending decision 1. At `0.1.0` a reversal costs a rename, not
a migration.

**Verified — all gates, including the blocking one:**

| Check | Result |
| --- | --- |
| `validate_ontology.py` (module, then all five) | pass, no regression |
| Every property has label + domain + range + comment | pass (checked via rdflib) |
| Duplicate `rdfs:label` across the merged suite | **0** — clean by construction, given the selection rule |
| **HermiT consistency + unsatisfiable classes** | **pass — `reason exit code: 0`** on the merged 5-module suite |
| ROBOT `report` | **0 ERROR.** 14 `missing_definition` WARN + 1 `missing_superclass` INFO from this module, both matching 213 / 19 pre-existing rows of the same type — i.e. consistent with existing repo practice, not a new divergence |
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
| **1** | **Initial version.** The design and review documents, the pass-1 plumbing, **and an initial `aec_titleblock.ttl`** — the terms that have no counterpart in `aec_drawing_metadata`, so the module is reviewable without pre-empting the unresolved placement question (the settled-decisions block above) | — |
| 2 | The remaining core properties, once the placement decision lands | PR 1 + decision 1 |
| 3 | SKOS enumerations and their concepts | PR 1 |
| 4 | SHACL shapes + `build_extraction_profile.py` | PR 3 |
| 5 | Extension properties | PR 3 |
| 6 | Extraction-provenance layer, including the timestamp | the RDF-star vs reification decision |
| — | Alignment axioms (IFC, `ct:`, `dano:`) — **not a scheduled PR.** Additive; build when a consumer requires it | a real deliverable requirement |

**What "initial version" means here.** It is deliberately the terms that are *uncontested*: everything whose
meaning overlaps an existing `dm:` term is listed as deferred in the TTL's footer rather than minted, because the
sheet-level (UC-01) vs titleblock-level placement is unresolved — see
`titleblock-vocabulary-review.md` §2.1. That keeps the first PR reviewable and reversible: nothing in it needs
withdrawing whichever way the placement decision goes.

ADIRO is open-source, so issues go on **GitHub**, mirrored one-way into RES
([MAN-A-3](https://bhmlrnd.youtrack.cloud/articles/MAN-A-3)).

## 5. Acceptance criteria

[Discussion #64 §10](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/64) is the checklist, and it already incorporates
the repo's CI gates (HermiT blocking, `duplicate_label` as a design signal, the plumbing items in §1 above, and
the duplicate-term criterion as amended by the §1.1 decision). Nothing further is added here.

## 6. Open questions

[Discussion #64 §11](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/64) — the reconciliation (q6) is the top item, and
q8 (where the SHACL shapes live) and q9 (whether RES-89's 16 h / `L` estimate still holds now that the
reconciliation is in scope) both need answers before pass 1 lands. The estimate is a Sprint-planning call.
