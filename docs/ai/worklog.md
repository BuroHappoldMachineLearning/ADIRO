## 2026-10-20 - The file, the page and the agents in the ontology

Implemented [#192](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/192) in full (the maintainer asked for the whole issue, not only the design page). `aec_provenance` gains `DrawingFile`, `FilePage` and
the agents `Party`, `Person`, `Organisation` (moved from `aec_drawing_metadata`, new IRIs; `Party` is their disjoint union), with the file and page properties; the classes are subclasses of
local stubs of the ISO 21597-1 edition-1 terms, the properties are related to ICDD, Dublin Core and DCAT by `skos:closeMatch` only (every ICDD property is functional). `aec_geometry`: a `CoordinateFrame`
keeps only `coordinateSpace`, `unit`, `profileRef` and points to its page with `describesPage` (`pageIndex`, `frameArtifactRef`, `pdfRotationDeg`, `displayWidthPt`, `displayHeightPt` leave it:
BREAKING). `aec_drawing_metadata`: `isOnPage` added; `Person`, `Organisation` and `hasCoordinateFrame` removed; the now-unused import of `aec_geometry` dropped. UC-01 ORSD v0.9 (FR 9, CQ group 9);
`tests/test_file_and_page_model.py` pins the structure and the alignment rules, and the recorded queries CQ 9.1 and 9.3 run on small data. Display configs pruned of the removed terms.
Also fixed a changelog accident from the merge of #189: its entries had landed under the released `[5.0.1]` heading (the tag does not contain them) and are back under `[Unreleased]`.
Not verified: the IFC document-information IRI (open point on the design page), the rendering of the new pages in OntoCanvas, and the `uc01-merged-for-visualization.ttl` copy, which still shows the old structure.
Released with the module rename of [#171](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/171).

## 2026-10-20 - Authorship on the drawing and the revision, and `assertsRevision`

Implemented the ontology half of [#179](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/179) and [#69](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/69)
(approved by the maintainer). `isAuthoredBy`, `isCheckedBy` and `isApprovedBy` now have the union domain `DrawingSheet` or `DrawingRevision`, since
the title block's author is the drawing's and a revision can be made by someone else; `assertsProject` and `assertsPackage` (`Titleblock` to `Project` / `DrawingPackage`, added at the maintainer's request: the title block's claim differs from `belongsToProject` / `belongsToPackage`, the filing; CQ 2.3, 2.4, 8.3, 8.4; a package is optional), `assertsRevision` (`RevisionTable` to `DrawingRevision`)
records which printed table a revision was read from. UC-01 ORSD v0.8 (CQ 3.4, 4.4, 4.5 with their queries, the amended "Person vs Role" note,
open issue G12); `tests/test_uc01_competency_queries.py` runs the recorded queries on small data. The version impact is MAJOR, because the
compatibility check reads any domain change as potentially breaking although a widening invalidates no statement; it goes into the MAJOR cut
planned with [#170](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/170) and [#171](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/171).
`issueDate` widens the same way (decided with the maintainer; "date authored" is its `skos:altLabel`), and only the author is required (checker and approver are optional). A drawing that records no author is read as authored by its revisions' authors (decided with the maintainer; a path in CQ 4.4 and in the shape, not an OWL chain, which would add revision authors to a drawing that records its own); the fallback is for the author only. `data-validation/uc01-authorship.shacl.ttl` is the shape for CQ 4.4 (a Warning; its property shape carries its own severity, because SHACL does not pass a node shape's severity down). Not done: telling "the extraction missed the author" from "the drawing names none" (the vocabulary of [#187](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/187)). Merge the pending PATCH Release PR before this one: this change turns the next cut into a MAJOR.

## 2026-10-20 - The post-release deploy failed on a stale checkout and raised no alert

First release since [#173](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/173) was fixed: the snapshots were committed (the bot-token push works), but the
deploy dispatched by `backup-version.yml` failed (`Commit and push documentation`: add/add conflict on `docs/aec_drawing_metadata/5.0.0/aec_drawing_metadata.html`), so the site
and the badges stayed on the old versions. Cause: a `workflow_dispatch` run is queued behind the push run (concurrency group) but checks out the commit `main` had when it was
dispatched, so it regenerated pages the first run had already committed. Repaired by dispatching the deploy again from the current `main`. Second finding: the alert
watcher ([#175](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/175)) never saw the failure, because the run had been dispatched with `GITHUB_TOKEN` (actor `github-actions[bot]`) and GitHub starts
no `workflow_run` workflow for such a run; the runs started by a person or by the ADIRO Bot did reach it (compared by actor). Fix ([#190](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/190)): `generate-docs` checks out `github.ref_name`;
`backup-version.yml` dispatches with the ADIRO Bot token; `tests/test_workflow_tokens.py` keeps both (it fails without the fix). Not verified: the ADIRO Bot token's right to dispatch
workflows from `backup-version.yml` (the release workflow already dispatches that way), and an alert on a real post-release failure: both show at the next release.

## 2026-10-20 - Data validation: SHACL shapes outside the ontology modules

Implemented [#168](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/168). Decided with the maintainer: a root folder `data-validation/`
(not `shapes/`, which is SHACL jargon; not `src/`, whose top-level `*.ttl` are read as ontology modules by the docs generator, the validator,
the reasoner and the release scripts) with files named `<topic>.shacl.ttl`. First file: `uc03-composition.shacl.ttl` with the three UC-03
composition rules (severity Violation). `scripts/validate_data.py` runs them with pySHACL, reading the ontology as background so a subclass
counts as its superclass; `tests/test_data_validation.py` (14 tests) shows each rule accepting and rejecting, and checks every named ADIRO term
exists. `--with pyshacl` added to the two CI pytest commands. New page `docs/contribute/data-validation.md`, `AGENTS.md` entries.
Not done: the "no author" shapes of [#179](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/179) (they wait for its ontology half and
for [#187](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/187)), publishing the folder on the site, and a run over real data (there is
no ABox yet, [#22](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/22)).

## 2026-10-20 - Example images: DrawingSheet, one layout per Layout image, and the UC-03 reference classes

Implemented [#177](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/177) and [#164](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/164) in
`scripts/synthetic_example_images.py`. `DrawingSheet` gets three sheets (one, three and six layouts; the six-layout one mixes large and small
layouts, as a real sheet does), `Layout` gets three single-layout images (`Layout_02` to `_04`: plan, section, detail), and the four UC-03
classes each get a drawing note with the named part boxed. `Layout_01.png` is still drawn and committed (byte-identical to before) in a new
`ARCHIVED` registry, because an earlier release names it; it is no longer linked from `Layout`, and `DrawingSheet_02.png` is the same
picture. Verified: the image tests (84), the strict image validation (`ENFORCE_EXAMPLE_IMAGES=1`, `ENFORCE_ARCHIVED_IMAGES=1`), the version
impact (PATCH, annotation changes) and a look at the rendered images. Not verified: the rendering on the published pages. Changelog under
`[Unreleased]`.

## 2026-10-20 - Version-impact comment links each change to the PR diff

Implemented [#183](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/183). Each change in the comment now links to its line in the
PR's "Files changed" view (`.../pull/<n>/changes#diff-<sha256 of the path>R<line>`, `L<line>` on the old side for a removed term) as well as
to the file at the head commit. The anchor rule was checked against a real link from the user (SHA-256 of `docs/aec_geometry.ttl`). Two more
variables in both workflows carry the pull request number and the base repository (the fork flow's PR is in the base repository, the file in the
fork). Verified: 29 tests, and a run with `COMPAT_LINK_PR=180`. Not verified: GitHub opening the anchor for a line the diff does not show (an
unchanged first line of a term), or for a diff GitHub collapses as large; the file link is the fallback for both.

## 2026-10-20 - Version-impact comment names the changed annotation and links its line

Implemented [#181](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/181) in `scripts/compat_diff.py`: `annotation_details` names the
annotation behind an `ANNOTATION_CHANGED` (label, comment, example images; domain, range, superproperty of an annotation property),
`locate_lines` finds the term's line and each annotation's line by reading the Turtle text, and `to_markdown` renders a GitHub blob link
at the PR head commit. The classification and the bump are unchanged. Wired through `COMPAT_LINK_REPO` / `COMPAT_LINK_SHA` in
`compat-diff-comment.yml` and `pr-comments-fork.yml` (the fork flow points at the fork's repository). A removed term and a term whose line
is not found stay unlinked. Verified: 26 tests, and a run on the real `bboxXYXY` change gave a link to line 80. Not verified: the
comment on a live PR, and the fork flow. The lookup assumes the repository's Turtle style (the subject at the start of a line, the
rest indented); a different layout loses the link, not the report.

## 2026-10-20 - Navigation: Ontologies first, design decisions under Specification and use cases

Implemented [#176](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/176). The menu is Introduction, Ontologies, Specification,
Contribute. `docs/design-decisions/` moved to `docs/specification/design-decisions/` (suite-wide pages); the three UC-03 notes moved to
`UC-03/design-notes/` and the title-block review and field survey to `UC-01/design-notes/`. Files moved without redirects (decided by the
maintainer: nothing published cites the old addresses), so the old page addresses no longer open. Every internal link was rewritten;
`mkdocs build --strict` and `pytest tests` pass. The two repository paths in `src/aec_geometry.ttl` were replaced (the `bboxXYXY`
`rdfs:comment` now cites issue #91; changelog entry under `[Unreleased]`, an annotation change). Not verified: the rendered menu in a
browser (checked the built labels and order only). The use-case ORSDs were not re-versioned: no content changed.

## 2026-10-20 - Terminology: "drawing", not "sheet"

Recorded the maintainer's rule in `AGENTS.md` (ontology authoring conventions): say "drawing" for the thing ADIRO describes and
keep "sheet" for the paper format; `DrawingSheet` and the terms built on it keep their IRIs. Fixed the one line in the module
list that said "sheet". Not done: the other hand-written pages and the issues still say "sheet" in places; they are changed when
they are next edited. Whether `DrawingSheet` itself should be renamed is a separate, MAJOR decision, not made here.

## 2026-10-20 - Alert when a release or publishing workflow fails

Nothing reported the failed releases of 19 October ([#173](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/173)): the only
alert, in `verify-prior-versions`, depends on the deploy job that was skipped. Added `.github/workflows/alert-on-failure.yml`
(a `workflow_run` watcher of the docs deploy, `backup-version.yml` and the Release PR workflow) that opens one tracking issue per
workflow as the ADIRO Bot, comments while it keeps failing and closes the deploy and Release PR issues when a run passes.
The YAML parses; the workflow cannot run before it is on `main`, so the first real failure is the test. Decided: the snapshot
issue is closed by hand, because a success for one tag does not clear another. Not done: alerting on a failure that never
starts a run (a disabled workflow).
Also added a "Build status" column to the README (build & tests, release PR, snapshot, reasoning, and a count of open
`ci-alert` issues), each badge linking to its own section of `docs/contribute/build-status.md`, which explains what it
shows and what red means and links to the workflow's runs. The badge URLs were fetched from shields.io and render; the snapshot badge has no `branch=main`
because a snapshot started by a release reports the tag as its branch. Label `ci-alert` created on the repository.

## 2026-10-19 - Releases did not publish: CI pushes to `main` rejected by the ruleset

Investigated why the site and the README badges showed the previous versions after the 19 October cut ([#173](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/173)).
Cause: the ruleset "main PRs" (created 12:52 UTC, edited 13:02 UTC) requires a pull request and lists only a user as a bypass
actor, so the `Commit and push documentation` step and the five `Commit and push snapshot` steps are rejected with `GH013`.
The deploy is therefore skipped and `versions/` has no snapshot for any of the five releases. Verified from the run logs, the
site's `badges/aec_drawing_metadata.json` (still `4.0.1`) and the `versions/` listing. This change records the dependency in
`AGENTS.md`. Adding bypass actors (the ADIRO Bot, the admin roles, other apps) did not help: a re-run of `backup-version.yml`
for `aec_provenance-v1.0.1` was still rejected with `GH013`, because the default `GITHUB_TOKEN` (the GitHub Actions app)
cannot be a bypass actor. Fix: both workflows push with the ADIRO Bot app token (a bypass actor), and their commits carry
`[skip actions]`. Not verified until the PR is merged: that the app-token push is accepted (the workflow files on `main`
are what run).

## 2026-10-19 - Check existing issues and Discussions first

Add the rule "Look before you write" to `AGENTS.md` (team workflow) and the Claude Code skill
`check-existing-work`: search issues (open and closed), PRs and Discussions, and read the threads with their
comments, before a new task, when picking up an issue and before creating an issue or Discussion. The search
commands in the skill were run against this repository (issues, PRs and Discussions return hits; a Discussion
and an issue thread were read). The Cursor adapter inherits the rule through `AGENTS.md`. Docs-only change.

## 2026-10-19 - Merge with a merge commit only

Add the rule to `AGENTS.md` (contributor workflow, step 7): PRs are merged with a merge commit, never squashed or
rebased, the Release PR included. The reasons: squash and rebase discard the branch structure and rewrite the
hashes quoted in reviews, and the Release PR workflow (`release-pr.yml`) does not depend on the merge method (it
finds a merged cut from the declared version and tags `$GITHUB_SHA`). The repository settings were changed to
allow only merge commits (squash and rebase merging off). Docs-only change; no ontology touched.

## 2026-10-16 - Review changes to the UC-03 semantic references

Replace `hasSheetNoMention` / `hasLayoutNoMention` with `contains` and a typed mention, and rename the mention
classes `DrawingIdentifierMention` / `LayoutIdentifierMention` (an identifier is often alphanumeric, and `No`
reads as a negation). Mark the five new classes `isComputerVisionLabel`. Generalise `inlineAppearsOn` to
`appearsOnLayout` on `ReferenceExpression`. Write the composition rules in the provenance profile as validation
rules, not OWL axioms (open-world reasoning would infer an anonymous mention or merge distinct individuals);
the shapes are tracked in #168. Defer a bare layout-identifier reference class with #38 and #20. Tests and the
CQ 4.2 query lookup were tightened. Repository tests and ontology validation pass locally; the reasoning
check is not run locally.

## 2026-10-15 - Independent review corrections to the UC-03 export profile

Clarify that final accepted extraction branches determine expression admission and source geometry;
provisional/abstained observations stay in evidence. Keep accepted source number mentions when target
resolution fails. Require a distinct assembly activity for each execution, with actual timing and pinned
code/configuration. These are application-profile clarifications; no TTL axiom or release version changed.
Repository tests and strict documentation build are rerun for this follow-up.

## 2026-10-15 - UC-03 semantic occurrences and provenance profile

Port the approved semantic proposal onto current main, preserving later suite and annotation-tooling changes.
Add reference expressions, source number occurrences and direct accepted targets under #95; document the
batch/evidence profile under #96. Separate semantic resolution admission from precise navigation geometry:
unlocalisable reconstructed text blocks may retain an independently accepted sheet resolution without
invented geometry. Preserve existing graphical Layout relations and defer navigation vocabulary.

Parser, repository tests, regenerated documentation and strict site build passed locally.
HermiT consistency/unsatisfiable-class checks and ROBOT passed using an isolated official JRE;
the local environment initially lacked Java. Browser visual QA remains for review because no
browser surface was connected; generated HTML structure and strict links were checked. No private instance
data or client drawings are included in this repository. Module release versions remain unchanged.

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

## 2026-10-17 — Rebase the UC-03 semantic profile after the text-field changes

**Issues:** [#95](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/95), [#96](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/96). **PR:** [#151](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/151). **Branch:** `codex/uc03-semantic-profile-20261015`.

**Changed:** rebased all four existing commits onto `main` at `8402f32`, including the merged text-field changes from [#163](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/163). Kept both sides of the metadata changelog conflict. The use-case index retains UC-01 v0.7 and UC-03 v0.6. The original tip, `b9c6533`, is preserved locally as `codex/backup-pr151-before-rebase-20261017`. No ontology changes beyond the existing branch and the updated base were introduced.

**Verified:** ontology validation; regenerated all six ontology documentation pages; 259 tests passed, one skipped; strict MkDocs build; enforced HermiT consistency/unsatisfiable-class and OWL 2 DL checks; ROBOT report found no violations. The source and test files match the automatic merge of the original branch and the new base. Existing missing-description and Pillow deprecation warnings remain.

**Next:** inspect remote checks on the updated PR before the maintainer's merge decision. Release versions and the deferred geometry/navigation scope are unchanged.

## 2026-10-16 — #162: rebased on `main`, YouTrack ID out of the commits, consumer-neutral wording ([#162](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/162))

**Branch:** `feat/162-labellable-text-fields`, rebased on `main` after [#165](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/165) (worklog conflict only: both entries kept, newest first) and force-pushed.

**Changed:**
- The two branch commits are reworded to carry only the GitHub issue number, as [#165](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/165) requires.
- Consumer-neutral wording, as [#165](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/165) requires: the changelog, the test docstring, `usage-of-restrictions-for-cardinality.md` and the 2026-10-15 entry below no longer name a downstream consumer, its display names or how it walks the graph. The changelog says that downstream consumers that derive labels from ADIRO may need adjustments, and the restrictions are justified by what they mean (the class names the properties it can carry).
- Review point on sub-property entailment: the claim that a `hasScale` query also returns `drawingScale` / `layoutScale` values now names its condition (with sub-property entailment). Without a reasoner a sheet's scale is read with `hasScale|drawingScale` and a layout's with `hasScale|layoutScale` (changelog, UC-01).
- Where a scale is printed, decided by the author: `drawingScale` is the scale of the sheet as a whole, usually in the title block and also in a general note outside any layout (judged from context at extraction, not by the ontology). A layout's scale is **not** copied into `drawingScale`: a sheet can gain layouts, and a scale copied from the first one detected would stop being true. A layout that prints no scale gets no `layoutScale`; "NTS" / "As shown" are recorded verbatim. The `drawingScale` and `layoutScale` comments and hints say so; UC-01 gets a "where a scale is printed" table in §2.2, CQ 1.4–1.7 (the scale that applies to a layout, sheets with no scale, layouts whose scale cannot be determined, layouts at a different scale from their sheet), the SPARQL for CQ 1.3–1.7 in §5, and the traceability rows. The fallback to the sheet's scale for a layout without one is a query result ("assumed from sheet"), never an asserted value.
- Review point on `ScaleField`, taken in this PR: `aprov:mapsToFieldProperty` of `ScaleField` is now `:drawingScale`, not `:hasScale`. `ScaleField` belongs to `TitleblockFieldScheme`, which covers title-block fields only, and a scale extracted from the title block is the sheet's. Mapping it to the parent left the labelled `drawingScale` never populated by extraction and let one fact be recorded under two properties. The reason given on 2026-10-15 (`aprov:assertedBy`'s comment cites a layout-corner scale) is an illustration in another module, not a use of `ScaleField` by a layout. Two new rule tests in `tests/test_labellable_text_fields.py` check that every labelled `DrawingSheet` property is the promotion target of a title-block field kind and that none is promoted to `hasScale`; both failed before the change, on the assertion. `compat_diff.py` reports no change for the mapping.
- Rule test (review): `test_every_labelled_datatype_property_is_named_by_a_restriction_on_its_owner` finds every datatype property marked `isComputerVisionLabel true` in the graph and checks that its owner class names it in a restriction, so a labelled property added without one fails; a second test adds one in memory and checks that the rule catches it.
- Review question "why these six": the selection rule is written in `usage-of-annotation-properties.md`. A datatype property is marked when a use case needs the printed field located on the drawing, not only its value read, decided per use case; `sheetSize`, the revision fields and the dates stay unmarked until a use case needs to locate them. No new property is marked here.
- Review question on `sheetSize`: its comment and `skos:altLabel "drawing size"@en` say why it keeps "sheet"; the UC-01 row and history note it. "Drawing size" is not added as a term.
- Review point on `UC-01/uc01-merged-for-visualization.ttl` and UC-01's v0.3 history line: checked. The visualisation file is a snapshot aligned with ORSD v0.3 (it has no `layoutIdentifier` / `layoutTitle`, and `hasScale` still has the pre-widening domain), so its content is not updated; a header comment now says so. The UC-01 line is a v0.3 history entry and is left as written.

**Deferred:** the scale in a layout's own caption has no field kind (it is not a title-block field), and a scale outside the title block may be the sheet's (a general note) or a layout's, which only the context decides. The maintainer decided on [#166](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/166) that no layout-caption field kind is added for now (option C: no use case needs promotion yet, and `layoutIdentifier` and `layoutTitle` have no field kind either); a new scheme for layout-caption fields, not a widened `TitleblockFieldScheme`, is the route if one is needed. The `aec_provenance` `assertedBy` comment, which cited a layout-corner scale, is reworded in this PR (a sentence, with an `[Unreleased]` entry in `changelogs/aec_provenance.md`), so this PR touches `aec_provenance` as well as `aec_drawing_metadata`. The issue lists `TitleblockFieldScheme` as out of scope: only an existing mapping is re-pointed, at a property this PR adds, and no field kind is added or renamed.

- Second review round: the "which properties are marked" paragraph names UC-03 (and no longer says "identity fields"; the detection method stays private); CQ 1.3 and CQ-I 2 state that they return only sheets with a sheet-level scale; the `assertedBy` example in `aec_provenance` is reworded, with an `[Unreleased]` entry. `compat_diff.py`: `aec_provenance` 1 change (`ANNOTATION_CHANGED` on `assertedBy`, PATCH, next version 1.0.1); `aec_drawing_metadata` 14 changes, as before.

**Verified:** `uv run python scripts/validate_ontology.py` `[OK]`; `uv run python scripts/generate_docs.py` 6/6 (the pyLODE page, `.ttl` and ontology page carry the new wording); `uv run --with pytest pytest -q` 252 passed, 4 skipped; `uv run mkdocs build --strict` OK. The five UC-01 scale queries were run once with rdflib, without a reasoner, on a small example (the script is not kept in the repository). **Not run:** `scripts/run_reasoning.sh` (no local Java; the PR's reasoning check covers it).

**Next step:** the reply to the second review round; [#166](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/166) is closed by the maintainer once the decision is recorded.

## 2026-10-16 — AGENTS.md: no YouTrack IDs in commits or branches, review labels, consumer wording

- Paragraph 4 of the PR-description rules now also covers commit messages and branch names: they carry the GitHub issue number, never a YouTrack ID (the YouTrack copy is an internal mirror, never edited; an internal issue linked to public work is not referenced). 25 earlier commits on `main` carry `RES-` IDs; history is not rewritten.
- "Downstream label consumers": the instruction to coordinate with the maintainers of a named pipeline is replaced by "say in the changelog that downstream consumers may need adjustments", without naming a consumer, its configuration or display names.
- "Reviewing a pull request": a finding verified by reading the code needs no confidence label; only *reproduced* and *suspected* are written.
- Not verified: nothing to run (documentation only). The same wording still has to be carried into the team's `tools:orientation` and `tools:public-repo-hygiene` skills (separate repository, not changed here).

## 2026-10-15 — Labellable text fields: `layoutScale`, `drawingScale`, and six properties marked as labels ([#162](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/162))

**Branch:** `feat/162-labellable-text-fields`, based on `main` at `2ff0acc`. Not committed yet.

**Changed:**
- `src/aec_drawing_metadata.ttl`: new `layoutScale` (domain `Layout`) and `drawingScale` (domain `DrawingSheet`), both `rdfs:subPropertyOf :hasScale`, range `xsd:string`, with a comment and an `extractionHint`. `isComputerVisionLabel true` on `drawingIdentifier`, `drawingTitle`, `drawingScale`, `layoutIdentifier`, `layoutTitle`, `layoutScale`; `hasScale` unmarked and otherwise unchanged. One "can have" restriction per property (`owl:minQualifiedCardinality 0`, `owl:onDataRange xsd:string`) on `DrawingSheet` and `Layout`. `isComputerVisionLabel`'s comment now covers "class or datatype property" (and the section comment above it says so); `isComputerVisionOptionalLabel`'s comment is left about classes, since no property carries it. `layoutTitle`'s extraction hint now says `layoutScale '1:5'` instead of `hasScale`.
- `changelogs/aec_drawing_metadata.md`: `[Unreleased]` Added (the two properties; the restrictions) and Changed (the annotation's scope, the six labels and the note that downstream consumers may need adjustments; the hint).
- `tests/test_labellable_text_fields.py`: the six are labelled datatype properties of their owner with range `xsd:string`, each named by a min-0 `owl:onDataRange xsd:string` restriction on the owner, and `hasScale` is unlabelled and the parent of both scales.

**Decided here:**
- `:ScaleField aprov:mapsToFieldProperty :hasScale` is **left as it is**. The field kind is not only a title-block field: `aprov:assertedBy`'s comment uses it for a scale asserted by the title block *and* by a layout corner, told apart by the asserting region, so mapping it to `drawingScale` would be wrong for the layout case. `hasScale` remains correct for both, and the issue puts `TitleblockFieldScheme` out of scope. A region-aware promotion (title block → `drawingScale`, layout → `layoutScale`) would be a separate issue. **Reversed in review on 2026-10-16** (see that entry): `ScaleField` is a title-block field, so it maps to `drawingScale`.
- `hasScale`'s comment does not mention the two sub-properties (the brief and the issue keep it unchanged). Adding one sentence pointing at them would be an annotation-only (PATCH-level) change if a reviewer asks for it.
- No script or test assumes `isComputerVisionLabel` is only on classes: `compat_diff.py` reads the flags on every term kind (it reports the four existing properties as `LABELLING_CHANGED`), and ttl2md renders the annotation and the `onDataRange` restrictions on a property's and a class's page (checked by rendering the module). Nothing changed there.

**Verified:** `uv run python scripts/validate_ontology.py` (also with `BASE_REF=origin/main`) — every module `[OK]`, only the standing facade #87 warning. `compat_diff.py --markdown --base-dir <main's src>` (as the PR comment workflow runs it): `aec_drawing_metadata` 13 changes, MAJOR-level — 6 `RESTRICTION_ADDED`, 4 `LABELLING_CHANGED`, 2 `TERM_ADDED`, 1 `ANNOTATION_CHANGED`; next version 5.0.0, as before this change. `compat_diff.py` (warn mode): no inconsistency. `uv run --with pytest --with pillow python -m pytest tests -q` 221 passed, 1 skipped; ttl2md tests 30 passed. **Not run:** `scripts/run_reasoning.sh` (HermiT + ROBOT DL profile) — no Java on this machine; the PR's reasoning check is the first run. Docs not regenerated (a later step), hand-written specification not updated (a later step).

**Deferred to the maintainers (open questions in the issue, implemented here with the issue's proposed defaults):**
1. Restriction form — `owl:minQualifiedCardinality 0` (adds only the class-to-property edge), rather than `someValuesFrom` (too strong) or `maxCardinality 1` (an unneeded constraint), or no restriction (the class would not name the property).
2. Annotation scope — `isComputerVisionLabel` extended to datatype properties, rather than a separate annotation for text fields.
3. Version impact — `LABELLING_CHANGED` and `RESTRICTION_ADDED` are potentially breaking (MAJOR unless review says otherwise); `[Unreleased]` is already MAJOR because of the [#141](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/141) rename, so this adds no further bump if released together.
4. `hasScale` kept, not deprecated, domain unchanged; narrowing it would be a `DOMAIN_CHANGED` in its own issue.

**Docs regen and spec sync (same day):** `src/aec_drawing_metadata.display.json` got diagram positions for `drawingScale` and `layoutScale` (next to `hasScale` / `layoutTitle`); `uv run python scripts/generate_docs.py` then changed only the `aec_drawing_metadata` generated files under `docs/` (page, pyLODE HTML, `.ttl`, `.display.json`). UC-01 is now v0.7 (MAJOR in substance, attributes added; 0.x draft): `drawingScale` / `layoutScale` added to the attributes table, FR 1 derived terms and traceability matrix, `hasScale` CQs left as they are (valid by sub-property entailment); `use-cases/README.md` rows updated. UC-03 needed no change (`layoutIdentifier` / `drawingIdentifier` are unchanged apart from the label flag). `usage-of-annotation-properties.md` and `usage-of-restrictions-for-cardinality.md` (the `owl:onDataRange` form) amended in place. `validate_ontology.py` OK, `mkdocs build --strict` OK, `pytest tests` 221 passed, 1 skipped. Remaining: open the PR (`Closes #162`).

**Next step:** open the PR (`Closes #162`), get the maintainers' answers to the four open questions in the issue, and check the reasoning CI (no local Java).

## 2026-10-15 — The two logos are shrunk (PR [#161](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/161))

- `docs/img/favicon.png` 1254 px, 888 KB → 256 px, 45 KB (site logo and favicon); `docs/img/adiro_banner.png` 1254 px, 1.2 MB → 640 px, 376 KB (shown at 320 px, so 2x for high-density screens). Same names, so no reference changed.
- Verified: `tests/test_diagram_colors.py` (brand colours read from the favicon) passes. Not looked at in a built site.
- Left for the author: whether `docs/brainstorming/ontology_modeling-object_properties.md` is obsolete; trimming old worklog entries.

## 2026-10-15 — The nine unlinked facade images are removed; the git history is left as it is ([#149](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/149))

**Decided (maintainer):** (3) the nine images under `docs/img/aec_facade_domain/` are removed, now that the synthetic curtain-wall sections of [#152](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/152) cover the same terms; (4) the git history is **not** rewritten: it would take too much effort and the images were open source.

**Changed:** `docs/img/aec_facade_domain/` deleted (nine PNGs; no term, page, script or archived release referenced them, checked by search). `docs/img/` keeps the banner and the favicon. No takedown entry: they were never an `exampleImage` value of any term.

**Verified:** a search for any reference to the folder or to its file names finds none outside this log. **Not verified:** the published site still serves them at the old addresses until the next deploy removes them.

**Next step:** with this merged, #149 is complete (steps 1 and 2 in #150 and #153, 3 here, 4 decided).

## 2026-10-15 — `exampleImage` becomes a sub-property of `foaf:depiction` ([#157](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/157))

**Branch:** `feat/157-foaf-depiction`, based on `main` after the [#154](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/154) PR merged.

**Changed:**
- `src/aec_drawing_metadata.ttl`: `@prefix foaf:`, `foaf:depiction a owl:AnnotationProperty` (with a label, so ROBOT's `missing_label` stays quiet) and `:exampleImage rdfs:subPropertyOf foaf:depiction`. FOAF is not imported.
- Guard 1, `scripts/validate_ontology.py` (`find_foaf_problems`): an error if a module imports FOAF or types `foaf:depiction` as anything but an annotation property; `tests/test_foaf_guard.py`.
- Guard 2, `scripts/run_reasoning.sh`: ROBOT `validate-profile --profile DL` over the merged modules. Found while testing: HermiT through ROBOT does **not** notice the punning (reason exit code 0 with FOAF's object property merged in), so the profile check is needed. The profile report also lists 181 standing "Use of undeclared ..." violations (SKOS and DCTERMS annotation properties, `skos:Concept`, `xsd:date`): a backlog of missing declarations, not punning. Those lines are filtered out; any other violation (here "Cannot pun between properties") is added to `reason.out`, fails the reasoner gate and shows in the QC comment. Declaring the SKOS / DCTERMS terms would let the filter go; not done here.
- `scripts/compat_diff.py`: a changed super-property of an **annotation** property is an `ANNOTATION_CHANGED` (PATCH), not a `SUPERPROPERTY_CHANGED` (MAJOR), like its domain and range (the spec line and a test updated). The new term `depiction` counts as `TERM_ADDED`; the module is MAJOR anyway because of the labelling rename pending since #141.
- Guidance page (a section on the standard property and on not importing FOAF), `AGENTS.md`, changelog.

**Verified:** `run_reasoning.sh` clean (rc 0, ROBOT report "No violations found"); with a FOAF `owl:ObjectProperty` injected into `src/` the script exits 1 under `ENFORCE=1` and names the three "Cannot pun" violations (the injected file removed afterwards); full pytest run. **Not verified:** the CI run of the reasoning workflow with the new step.

**Not done:** the claim in the issue that OMO / Cell Ontology use `foaf:depicted_by`-style declarations was taken from the request, not checked.

## 2026-10-15 — Archived releases keep their example images; a takedown serves a placeholder ([#154](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/154))

**Branch:** `feat/154-archived-example-images`, based on `feat/151-more-synthetic-images` (the [#152](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/152) PR, unmerged when this was written).

**Changed:**
- `scripts/example_images.py`: a removed term's image stays where it is (no `deletedAfterV…/` folder, no move); the unused-file check accepts a file that an archived release names (`snapshot_values` reads every `versions/<module>/*/<module>.ttl`, also the earliest ones, which declare the property under the Pages host and hold relative IRIs resolving to site paths). New findings: `archived-missing` (an address an archived release names that no file, rename or takedown would serve; advisory for the first release cycle, blocking once `ENFORCE_ARCHIVED_IMAGES=1` is set in `validate-ontology.yml`: flip it after the first Release PR passes with it), `name-reused` (a name an archived release gives to another term; blocking), `takedown-reuse` (a current file with a taken-down name; blocking), `takedown-placeholder` (a version with no placeholder; blocking), `takedown-version` (advisory).
- `takedowns.txt` lines are `<path> <reason> after=<x.y.z>`; `stage()` serves the placeholder `removed/after-v<x.y.z>.png` at each taken-down path, also a legacy site path (`docs/img/aec_drawing_ontology/` is git-ignored), and a rename no longer serves a taken-down name again. The twenty #149 entries carry `after=4.0.1`.
- `scripts/synthetic_example_images.py` draws the placeholder per removal version; `scripts/check_prior_versions.py` fetches every example image an archived release names after a deploy (image content type; the placeholder at a takedown), with retries, as it does for display configs.
- The bot's "removed term's image still in place" suggestion is gone (a removed term's image now stays, so there is nothing to ask).
- Guidance page, `AGENTS.md`, `assets/README.md`, tests (`tests/test_archived_example_images.py`).

**Verified:** full pytest run (245 tests with matplotlib and Pillow), `validate_ontology.py` (no example-image finding: all 80 archived values of `aec_drawing_metadata` are covered), `stage()` into a temporary folder (the legacy paths get the placeholder). **Not verified:** the post-deploy check against the live site (first run after the next deploy); `mkdocs build --strict`.

**Left for later:** a hash manifest per release to catch an image replaced in place under the same name.

## 2026-10-15 — Synthetic example images for more terms ([#152](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/152))

**Branch:** `feat/151-more-synthetic-images`, based on `main` once #148 and #150 had merged. Extends [#149](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/149).

**Changed:**
- `scripts/synthetic_example_images.py` now draws 30 images in four modules (the registry `DRAWINGS` is keyed by module; the output root is `assets/`). New: `KeyPlan`, `Perspective`, `Layout` (one sheet with three labelled layouts) in `aec_drawing_metadata`; `Dimension`, `Grid`, `ReferenceSymbol` in `aec_common_symbols`; `ISection`, `CHS`, `RHS`, `SectionChannel`, `TopHat` in `aec_domain_common`; `DGU`, `MineralWool`, `Transom`, `Gasket`, `Sealant`, `Bracket`, `ShelfAngle`, `Firestop` (one curtain-wall section at a slab edge, the term filled red) and `Mullion` (plan section) in `aec_facade_domain`. The palette went from 16 to 32 colours (a thin red part was quantised to brown), so the ten earlier PNGs changed bytes, not content.
- The four TTLs link them with `exampleImage` and an `img:` prefix per module. `rdfs:comment` added to `Mullion`, `Transom`, `MineralWool`, `Sealant`, `Bracket`, `ShelfAngle`; `DGU`'s comment (it repeated its label) rewritten.
- Changelogs of the four modules, `AGENTS.md` and `assets/README.md` (all modules' images are synthetic), tests made per-module.

**Decided / left out:** no image for `Note` (a superclass), `DrawingRevision` (a revision cloud would overlap `RevisionTable`), `Column`/`Beam`/`Slab` (generic), nor the abstract and metadata classes. `SingleGlazing` (named earlier in the discussion) is not a class of the suite. The nine unlinked images in `docs/img/aec_facade_domain/` are not removed: that is still the maintainers' decision on #149, now possible without losing coverage.

**Verified:** full pytest run (229 passed, with matplotlib and Pillow), `validate_ontology.py` (no example-image finding), `compat_diff.py` (only ANNOTATION_CHANGED for the new comments and images), `generate_docs.py` rerun (pyLODE HTML left as committed), every new image viewed. **Not verified:** `mkdocs build --strict` (skipped, memory); the staged copy in the deploy job.

**Next step:** merge the PR; then the maintainers decide the nine facade images and the git history on #149.

## 2026-10-14 — Take down the example images that broke the convention, and replace them ([#149](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/149))

**Branch:** `feat/149-synthetic-example-images`, stacked on `feat/145-example-image-convention` (PR #148, unmerged when this was written). It is the migration PR of [#145](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/145) decision 4, changed in scope by what was found.

**Found:** opening the twenty linked images before moving them showed that 18 of 20 are unredacted third-party drawings (firm logos, professional seals and names, client and project names and addresses, job numbers, CAD file paths in the margin, and in several a copyright notice that prohibits reuse); the other two are old title blocks, partly blacked out. None is cropped to the part it illustrates (the red box marks the part on a whole sheet), five are over 500 KB, and none has a recorded source. The nine unlinked images in `docs/img/aec_facade_domain/` are curtain-wall detail drawings with project drawing numbers, system codes and contractor references (five opened, four are the same family): source unknown, not taken down, left for review.

**Changed:**
- The twenty images are deleted from `docs/img/aec_drawing_ontology/`; their values are dropped; each old path is recorded in `assets/aec_drawing_metadata/exampleImage/takedowns.txt` (the reason codes are indicative).
- `scripts/synthetic_example_images.py` (new, tested): draws ten synthetic example images with fictional content (a title block in two layouts, revision table, legend, plan, section, elevation, detail, schedule, notes), 3 to 16 KB each, no embedded metadata, cropped to the content. They are committed at `assets/aec_drawing_metadata/exampleImage/<LocalName>_NN.png`, and `src/aec_drawing_metadata.ttl` links them with an `img:` prefix. The example-image checks now pass with no finding. The old image URLs no longer resolve, so the pages of earlier releases show no image for these terms (the changelog says so).

**Not done:** a decision on the nine facade images; a decision on the git history (the files remain in it: rewriting a public history affects forks, tags and releases, and is for the maintainers and whoever handles rights); a better set of images (the synthetic ones are plain, and are meant to be improved by editing the script).

**Verified:** full pytest run with and without matplotlib and Pillow (the new tests skip without them), `validate_ontology.py` (no example-image finding, no error), every generated image viewed. **Not verified:** the staged copy in the deploy job (first deploy that carries an image).

**Next step:** merge #148 first, then this; share the review list with the team.

## 2026-10-14 — The example-image convention ([#145](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/145))

**Branch:** `feat/145-example-image-convention`. The decisions are in the issue; this entry is what was built and what was not.

**Changed:**
- `scripts/example_images.py` (new, tested): the convention's checks (value is an absolute `https` IRI in `<module>/exampleImage/`, file name `<LocalName>_NN.<ext>` with a lower-case png/jpg/webp extension and characters valid in a prefixed name, file exists, orphans, case clashes, size 250 KB advised / 500 KB blocking, 1600 px, embedded metadata read from PNG/JPEG/WebP headers, rename entries, the 100/250 MB budget) and the build step `stage`, which copies `assets/<module>/exampleImage/` into `docs/<module>/exampleImage/`, serves each old name of `renames.json` as a copy, and skips takedowns. `generate_docs.py` calls it (replacing its unused `src/images` hook); `docs/*/exampleImage/` is git-ignored so the images are committed once.
- `validate_ontology.py` reports the checks, one message per kind with the guidance link: advisory for value and name findings (the older values), blocking for limits on files, and `ENFORCE_EXAMPLE_IMAGES=1` makes all of it blocking.
- `pr_guidance.py`: a **caution** registry (`Caution`, `cautions()`, red `[!CAUTION]` alert at the top; the first entry is removing or renaming `exampleImage`), a **Suggestions** level for issue types (an example image for each new class, linking the guidance page), and a required finding for the images of a removed term still in place. A caution or a suggestion alone posts the comment.
- `compat_diff.py`: `exampleImage` values count with the labels and comments, so a change of images is an annotation change (PATCH). A domain or range change on an **annotation property** is also an annotation change now (found on this PR's own version-impact comment: adding the range to `exampleImage` was reported as `RANGE_CHANGED`, potentially breaking, although an annotation property's range has no logical effect); object and datatype properties are unchanged.
- The `exampleImage` declaration in `aec_drawing_metadata`: `rdfs:range xsd:anyURI` and the convention in its comment, ending with "How to add an image: see https://w3id.org/adiro/contribute/example-images/". New page `docs/contribute/example-images.md` (linked from the contribute index), `assets/README.md`, the AGENTS.md bullet, the `[Unreleased]` changelog entry.

**Not done (decision 4):** the migration of the existing images and values (the 20 values still point at `…/adiro/img/aec_drawing_ontology/…` and the files are in `docs/img/aec_drawing_ontology/`), so the QC comment shows an advisory finding until then. The `img:` prefix is not declared in the TTL yet, for the same reason (an unused prefix is a finding). The page link in the declaration works once this is deployed.

**Verified:** full pytest run, `validate_ontology.py`, `mkdocs build --strict`, the bot run against a scratch repository. **Not verified:** the rendered caution and suggestions on GitHub (the next PR run shows them), and the staging in the deploy job (it runs in `generate-docs`, before `mkdocs build`, so the images exist when the site is built).

**Next step:** the migration PR (move `docs/img/<folder>/` to `assets/<module>/exampleImage/`, rename to `<LocalName>_NN`, add `renames.json` for the old names, add the `img:` prefix and switch the values); then `ENFORCE_EXAMPLE_IMAGES=1`.

## 2026-10-13 — Rename the labelling annotations ([#141](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/141), step 2 of [#89](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/89))

**Branch:** `feat/rename-labelling-annotations`, stacked on `fix/89-public-prose-and-guard` (PR #139, unmerged when this was written).

**Changed:** `labellableRoot` → `isComputerVisionLabel` and the tool-named property → `isComputerVisionOptionalLabel` in `src/` (all four modules that used them), the `.display.json` files and the two visualisation files under `docs/specification/use-cases/`. The names say which application they serve; another application gets its own pair (decided by the maintainer: qualifier in the name, not a context-valued property). The old properties are removed from `aec_drawing_metadata` rather than deprecated (maintainer decision, 2026-10-14: the never-delete rule is relaxed for annotation properties when the removal is justified, now stated in `docs/contribute/versioning/index.md`; the compat diff reports them as `TERM_REMOVED`, MAJOR). Released snapshots under `versions/` still declare them. All values are unchanged, including the explicit `false` on the eleven discipline classes of `aec_domain_common`.

**Compat diff:** the classifier did not look at annotation values, so the rename showed as MINOR for one module and nothing for the other three. New delta `LABELLING_CHANGED` (potentially breaking, so MAJOR): a boolean flag of the metadata namespace added, removed or changed on an existing term. All four modules require MAJOR with no override in `config/release_overrides.json`. Spec, report schema and tests updated.

**Rejected:** an implication "an optional label is labellable" with a validator check (first built, then removed: the old property meant "shown as an attribute", so the eleven discipline classes are optional labels that are deliberately not labellable; the implication contradicted real data); `rdfs:subPropertyOf` between the two; a context-valued property (`labellableIn` with annotation-context individuals), judged too complex to settle now; an override in `release_overrides.json`.

**Verified:** full pytest run, `validate_ontology.py`, `scripts/run_reasoning.sh`, `compat_diff.py` (MAJOR x4). **Not verified:** the annotation pipeline reading the new names.

**Left alone:** `SS/` (superseded, never edited).

**Decided:** `isComputerVisionOptionalLabel` is the right name for the discipline classes (maintainer): once a layout is identified it can be qualified as an architectural, engineering or other layout by picking a discipline. Recorded as the example in `usage-of-annotation-properties.md`. **Open:** the pipeline switch date.

## 2026-10-14 — Required improvements: group findings by issue type ([#144](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/144))

**Branch:** `feat/140-archive-display-config` (same PR as #140, at the maintainer's request).

**Changed:** `scripts/pr_guidance.py` no longer writes one bullet per term. A finding is a `(kind, item)` pair; `kinds(repo)` is the registry (title, advice, noun per issue type: no definition, shared label, removed module, missing changelog, unused prefix, unused import, closing keyword not linked) and `render` says each type's advice once, then lists the items, collapsed behind `<details><summary>Show the N terms</summary>` when there are more than `COLLAPSE_OVER` (5). A new check adds one `Kind`; an unregistered kind is an assertion error, not a silent drop. Items keep the module and the line link.

**Not changed:** the QC comment (the Important checks table), which already groups by module.

**Verified:** full pytest run (158 passed) with new tests for grouping, the 5/6 boundary, ordering, the unregistered-kind error and every registered kind rendering; the script run against a scratch repository with 7 undescribed terms (collapsed group, single changelog item, previews). **Not verified:** the rendered comment on GitHub (the next PR run shows it).

## 2026-10-14 — Archive each release's display config next to its TTL ([#140](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/140))

**Branch:** `feat/140-archive-display-config`.

**Changed:** `scripts/archive_display_config.py` (new, with tests): `archive` copies `src/<module>.display.json` as it was at the release tag into `versions/<module>/<semver>/`; `backfill` does the same for the existing archives (the tag when there is one, else the commit that archived the TTL, else the current config). `backup-version.yml` calls `archive` for each new release. The deploy workflow now publishes `*.display.json` from `versions/` as well as `*.ttl`. The post-deploy check (`check_prior_versions.py`, job `verify-prior-versions`) also requires every archived config to answer 200 with JSON at `w3id.org/adiro/<module>/<semver>/<module>.display.json`, retrying like the priorVersion check. All 18 existing releases are backfilled (14 from their tag, 4 from the commit that archived their TTL; none needed the current config).

**Decision:** the tracking issue is renamed "Published release IRIs and display configs do not resolve" (maintainer, 2026-10-14; no issue with the old title was open). The four untagged releases take their config from the commit that archived their TTL, not the current config: the current one describes terms and layout the release never had.

**Verified:** full pytest run (153 passed), every archived config parses as JSON. **Not verified:** the workflow changes themselves (no release was cut; `backup-version.yml` is exercised by the next release or by `gh workflow run backup-version.yml -f tag=<tag>`), and that the published URLs answer 200, which only the post-merge deploy shows. The viewer side (it also looks for the config in the wrong place for a version IRI) is alelom/OntoCanvas#136.

**Next step:** after the deploy, open `…/ADIRO/aec_drawing_metadata/4.0.0/aec_drawing_metadata.display.json`; then close the loop on #136.

## 2026-10-13 — Public repo: internal tool name out of the prose, and a guard ([#89](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/89))

**Branch:** `fix/89-public-prose-and-guard`. Steps 1 and 3 of the issue; step 2 (the rename) is open.

**Changed:** the tool name is gone from `AGENTS.md`, the published design and versioning pages, the UC-01 merged visualisation file's property definition, `scripts/run_reasoning.sh`, the released changelog entries and this worklog (history kept, wording made generic). `AGENTS.md` no longer cites the internal KB article or the pipeline's rule names; it keeps the behaviour (the label text comes from the IRI local name, `rdfs:label` only for enumeration values). New `find_internal_names` in `scripts/validate_ontology.py`: a match in a hand-written file is a blocking error and shows as a "public-repo names" row in the QC comment. The names are assembled from parts so the guard's own source does not hold them. `versions/` and generated pages are not scanned. The one identifier that still carries the name is on an allow-list until it is renamed.

**Not done:** step 2, renaming the published property (MAJOR for `aec_drawing_metadata` and a bump for `aec_domain_common`, deprecate-then-replace, snapshots untouched), which needs a name and the pipeline maintainers; and the generated pages and snapshots that still show the identifier.

**Verified:** full pytest run (144 passed), `validate_ontology.py` clean. **Next step:** decide the replacement name; then the rename PR also empties the allow-list.

## 2026-10-13 — AGENTS.md: reviewing a pull request, and issue first then PR ([#137](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/137))

**Branch:** `docs/agents-pr-review-and-issue-first`. Internal tracker item: MAN-37.

**Changed:** `AGENTS.md` gains "Reviewing a pull request" (in-depth review, minor/medium/major labels with an ontology-specific note, findings first, no repetition of the description or bots, public-repo disclosure rule, one review under the reviewer's account signed as the agent, `COMMENT` event) and the issue-first paragraph now says the PR that closes the issue follows. Written generically: no internal tool, client or tracker names. The `pr-review-feedback` skill still fits (it covers answering a review, the new section covers giving one), so it is unchanged.

**Not done here:** the register row in the team plugin repo (`docs/intentional-duplication.md`), which is the second PR of the task.

**Verified:** `mkdocs build --strict`. AGENTS.md is not published. **Next step:** the register PR.

## 2026-10-13 — How to pin a version when labelling data ([#121](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/121))

**Branch:** `docs/pin-a-version-guide`.

**Changed:** `docs/contribute/versioning/index.md` gains "Pinning a version when you label data": which IRI to use when labelling data, referring to a concept and importing a module, and where to get each. Point 4 of the issue, and the part of point 1 that #125 left.

**Decision:** a term has one unversioned IRI in ADIRO, so there is no "pinned term IRI" to copy; the version is pinned at module level by recording the module's versioned IRI with the data. That removes the per-term "copy pinned IRI" proposal (point 2). Not done, and left to the viewer-side work (alelom/OntoCanvas#128): copy buttons on the module page, the pinned IRIs in GitHub Release notes, a pinned column in the ontologies index.

**Verified:** `mkdocs build --strict`. **Not verified:** the rendered table layout.

**Next step:** none for ADIRO; #121 is closed by this PR.

## 2026-10-13 — Remove the unused `aec_common_symbols` import; classify import changes ([#134](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/134))

**Branch:** `fix/unused-common-symbols-imports`.

**Changed:**
- `src/aec_domain_common.ttl` and `src/aec_facade_domain.ttl` no longer `owl:imports` `aec_common_symbols` (neither uses one of its terms). Nothing in the suite imports `aec_common_symbols` now.
- `scripts/compat_diff.py`: an added or removed `owl:imports` is `IMPORTS_CHANGED` (non-breaking, PATCH). It was unclassified, so an imports-only change produced no release. Spec, report schema, versioning index and release-process updated; the old test that asserted "imports alone are no delta" is replaced.
- Changelog `[Unreleased]` entries for both modules; generated docs regenerated (dependency diagrams, landing page).
- Hand-written: UC-01 ORSD v0.5 → v0.6 and UC-03 ORSD v0.4 → v0.5 (§7 diagram corrected: it drew a linear chain through `aec_common_symbols` that was never the import graph; MINOR), the use-case README rows, and the import lines of the early modularization page.

**Versioning:** both modules already have a pending PATCH (`owl:priorVersion`), so one cut gives 2.0.1 → 2.0.2 each; two PATCH-level changes in one release are one increment.

**Verified:** full pytest run (139 passed), `validate_ontology.py` (the two unused-import warnings are gone), `mkdocs build --strict`. **Not verified:** the reasoner (`run_reasoning.sh`, left to CI), and the rendered page layout of the changed spec pages.

**Left alone:** `docs/aec_drawing_metadata.html` regenerated with only pyLODE ordering noise, so not committed.

**Next step:** merge before Release PR #127 is merged, so the change rides in the same cut.

## 2026-10-13 — The Release cut PR lists the merged PRs behind the release ([#132](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/132))

**Issue:** [#132](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/132). **Branch:** `feat/release-pr-merged-prs`. The maintainer asked for the Release PR to list every
PR that goes into the release, kept current as more PRs merge while it is open.
**Changed.** `scripts/prepare_release.py`: `merged_changes` gathers, per module, the PRs (or bare commits) that changed its ontology file since its last tagged
release, by reusing `release_notes.collect_changes` with the range ending at `HEAD` (the release is not tagged yet), and `body` renders a "Pull requests in this
release" section between the bump table and the checklist. A first release, or a previous release that was never tagged, says there is no list. `release-pr.yml`:
the "Plan the next release" step gets the bot token for the `gh api` lookups. **No new update mechanism was needed:** the workflow already rebuilds the description
from `main` and edits the PR on every push to `main`, so a PR merged while the Release PR is open appears on the next rebuild. A PR that changed several modules
is listed under each. Docs: `release-process.md`, `AGENTS.md`. **Verified:** 117 tests (new: the section, the empty and no-list cases, the gathering, `_tag_exists`
against a real git repo) and the real description generated from the repository today: each of the four pending modules lists
[#123](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/123). **Not verified:** the bot's rebuilt description on GitHub (it is rebuilt on the next push to `main`
after this merges), and the token's access to the PR lookups from the workflow. **Next step:** after the merge, open the rebuilt Release PR and check the list.

## 2026-10-13 — QC comment: findings inside the table, ROBOT by rule, no internal IDs ([#130](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/130))

**Issue:** [#130](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/130). **Branch:** `feat/qc-comment-table`. The maintainer asked for the `<details>` of each
finding to sit inside the "Repo-specific checks" table, and for a review of the rest of that comment.
**Changed.** `validate_ontology.py` `write_markdown`: each row has plain right-aligned Errors and Warnings counts and a separate left-aligned Findings column with one `Show` dropdown (errors, then warnings; the status icon is tied to the module name with a non-breaking space so a wide Findings cell cannot split them; the layout was checked by rendering the comment through GitHub's Markdown API and a GitHub stylesheet) (a `<details>` in the cell;
findings are escaped, since an IRI in angle brackets would be swallowed as an HTML tag and a pipe would end the cell), and the separate "Details" block is gone.
The undescribed-terms warning links the backlog ([#87](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/87)) and says how to list every term.
New `scripts/qc_comment.py` composes the whole comment (it was ~50 lines of shell in `ontology-reasoning.yml`, untestable): the ROBOT report as a count per level
and rule instead of 25 raw TSV rows (the INFO `missing_superclass` rows are noise, so they are only counted), ERROR and WARN rows listed with readable
names and capped, the full report kept as a `reasoning-out` run artifact and linked, shorter header and footer. The internal tracker ID and link are gone from the
comment, and from the version-impact comment's footer. **Decisions.** Details per module row (the finding messages are plain strings; a per-warning headline/body
split would need every check to change its output). **Follow-up at the maintainer's request (same PR):** the sections are renamed and reordered (verdict, **Important checks** = the repo's own,
**Minor checks** = ROBOT, then the former introduction collapsed as "About these checks"), each with a one-line "executed via" note, and the "reasoner blocks"
and "ROBOT stays advisory" notes moved to the start of the sections they concern; the verbose count lines are gone (the tables say it); and the ROBOT table is one row
per rule with a `Show` preview in a left-aligned Findings column: near-duplicate subject-only rows are grouped by module (25 `missing_superclass` rows became five
lines, with a one-line explanation of the rule; rows that carry a value are listed one per row, capped). `missing_superclass` is ROBOT's INFO for a class with
no asserted superclass, expected for root classes. **Then, same PR:** `missing_superclass` removed from `config/robot_report_profile.txt` (a test ontology run through ROBOT with our profile showed that a class asserted
under `owl:Thing` does satisfy the rule, but that axiom says nothing and the compatibility diff would read an added superclass as a change, a MAJOR bump; the rule is an
OBO convention that does not fit ADIRO's by-design roots and the PROV/GeoSPARQL stubs, and only produced a standing list nobody acts on); `AGENTS.md` records the
decision next to the profile rules and `tests/test_robot_profile.py` keeps it out. The "Executed via `scripts/validate_ontology.py`. The reasoner blocks: …" note
moved into "About these checks" (the word "too" dropped). Locally ROBOT now reports no violations, so the Minor checks read "No findings". **Not done (ideas):** marking which warnings are new in the PR (needs a comparison with the base; the
"Required improvements" comment covers what a PR introduces); ordering modules with findings first; internal IDs remain in workflow *source* comments (not
posted anywhere). **Verified:** 125 tests (new: the table, the composer), the composer on the real local reasoning output, and the live comment on this PR
(see the PR). **Not verified:** fork PRs (they get the job summary, not the comment).

## 2026-10-13 — Release PR did not commit the README badge links ([#128](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/128))

**Issue:** [#128](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/128). **Branch:** `fix/release-pr-stages-readme`. The first Release PR cut after
the README badges existed ([#127](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/127)) failed `validate`: `test_each_badge_links_to_the_release_page_of_the_declared_version`.
Cause: `prepare_release.py apply` bumps the README badge links, but `release-pr.yml` staged `src changelogs CHANGELOG.md AGENTS.md config/release_overrides.json`
only, so `README.md` was changed in the bot's working tree and never committed; the PR shipped new versions with the old links. It surfaced now because the
badge links are new and the repository tests only recently began to run on PRs ([#120](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/120)).
**Changed:** `README.md` added to the `git add` line, and `tests/test_release_pr_workflow.py` fails when any file `apply_plan` changes is not covered by that
line (it failed on exactly `README.md` before the fix). **Verified:** the new test (red before, green after) and the full suite (111 passed). **Not verified:**
the bot's regenerated Release PR on GitHub (it is rebuilt on the next push to `main` after this merges). **Next step:** merge; check that #127 is rebuilt with the
README change and its `validate` passes; then merge the Release PR.

## 2026-10-13 — Version dropdown and a documentation page per ontology version ([#124](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/124))

**Issue:** [#124](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/124). **Branch:** `feat/versioned-ontology-docs` (a separate PR from
[#123](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/123), at the maintainer's request). The requirement: each ontology page has a top
dropdown listing every version, showing the selected version and "(latest)" or "(X available)", and the *whole page* follows the selected version, so
documentation pages are maintained per version, not just the ontology files.

**Changed.** `scripts/ontology_versions.py` (pure): the version list (archived releases plus the version declared in `src/`, numerically ordered), the
status label, the `<details>` dropdown with relative links, and the search-exclusion front matter. `scripts/generate_docs.py`: `_ontology_page` builds a
page for one version (latest from `src/`; each earlier release from its archived snapshot into `docs/ontologies/<module>/<version>.md`, with that
version's title, TTL/pyLODE/OntoCanvas links on its `w3id.org/adiro/<module>/<version>` IRI, term reference and dependency diagram), stale pages are
removed, and `generate_version_documentation` writes pyLODE HTML per earlier release to `docs/<module>/<version>/<module>.html` (next to the archived
Turtle). `docs/stylesheets/extra.css`: the dropdown, styled as an outlined `.md-button`. Eight earlier-release pages were generated (`aec_drawing_metadata` 2.0.0 and 3.0.0, and the 1.0.0 and 2.0.0 of `aec_common_symbols`, `aec_domain_common`, `aec_facade_domain`). `AGENTS.md` and the
versioning docs describe it. Follow-up at the maintainer's request: the dropdown shares **one row** with the three existing buttons (a
`div.adiro-actions` wrapper in Markdown span mode, so the icons and links still work; tighter padding, 0.66 rem text and a 0.4 rem gap so four buttons fit
the ~690 px content column, measured at 668 px; they still wrap on a narrow screen), and the metadata bullets show **Versioned IRI** instead of **Version**
(`ttl2md` renders the versioned IRI when the ontology declares one and keeps the bare version as the fallback, with a test; `ttl2md`'s own 30 tests pass).

**Decisions.** The version the latest page documents gets no duplicate page; a cut whose snapshot is not taken yet is the latest. Version pages are left
out of the nav, the ontologies index and the search. Links are relative so they work under any base path. Pure logic lives in its own module because the
CI test job has no pyLODE (the page-generation test stubs it). An earlier release's pyLODE HTML is generated once and then kept: the release never changes, and pyLODE does not
order some output stably (two runs on the same file, even with the same `PYTHONHASHSEED`, can swap two links), so regenerating would add noise to every deploy
commit; `generate_docs.py --refresh-versions` regenerates them (found when rebasing: three pages differed by one swapped pair of links). **Rejected:**
whole-site versioning (`mike`), because modules version independently.

**Verified.** Tests (generation, stale removal, nav/index, the selector, pyLODE calls); `mkdocs build --strict`; the selector HTML survives Markdown intact;
no earlier-version page is in the search index; screenshots (Chrome headless) of the latest page, an earlier page, and the dropdown open, light scheme.
**Not verified:** the deployed site, the post-deploy link check on the new pages, dark mode, and a narrow (mobile) viewport.

**Next step.** After merge, check the deployed page of one module (the dropdown links, the earlier page, its pyLODE HTML link). When #123's patch releases
land, each module's dropdown gains its new latest version on the next deploy.

## 2026-10-13 — Every release names all earlier versions with `owl:priorVersion` ([#122](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/122))

**Issue:** [#122](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/122). **Branch:** `feat/prior-versions`. Requested by the
maintainer so OntoCanvas (which reads only the open file and the latest release, and does not follow a chain) can list and open earlier versions.

**Changed.** `scripts/prepare_release.py`: `apply` writes one `owl:priorVersion` per earlier archived version (all of them, from
`versions/<module>/`, numerically ordered) into each released module's header, and a new `priors` command does the same for the declared
version (the one-time migration here, and the hand-made cut). `scripts/compat_diff.py`: header annotations other than versionIRI, versionInfo
and imports are one pseudo-symbol, `ONTOLOGY_HEADER_CHANGED` (non-breaking, PATCH), because a header-only change was invisible to the classifier and
produced no release. `scripts/validate_ontology.py` (blocking): each prior is a version IRI of the module, earlier than the file, archived with
a matching `owl:versionIRI`, and every earlier archive is listed. `scripts/check_prior_versions.py` + a `verify-prior-versions` job in
`generate-deploy-docs.yml`: after a deploy each IRI must answer 200 with Turtle and serve the release it names (retries for a lagging deploy). A failure also opens one tracking
issue ("Published owl:priorVersion IRIs do not resolve", opened as the ADIRO Bot with a `GITHUB_TOKEN` fallback, commented on while deploys keep failing, closed by
the first deploy that passes; not for a cancelled run or a non-default branch), the same pattern as the reasoner check on `main`, because a red run only notifies
whoever merged.
Applied to `aec_drawing_metadata`, `aec_common_symbols`, `aec_domain_common`, `aec_facade_domain` with `[Unreleased]` entries, so the bot's Release
PR will cut four PATCH releases (4.0.1, 3.0.1, 2.0.2, 2.0.2). Docs: `docs/contribute/versioning/` (new section "Naming earlier versions with
`owl:priorVersion`", manual-cut step, design decision), the compat spec and report schema, `AGENTS.md`.

**Decisions.** (1) PATCH release, as the maintainer asked. (2) `aec_provenance` and `aec_geometry` have no earlier release, so nothing to name and no
release. (3) `aec_drawing_metadata` 1.0.0 was never published (no archive; its w3id IRI and the old host IRI both 404; its header named a host IRI
that was never served), so it is not listed and not archived. (4) The four pre-w3id archives (`aec_common_symbols`, `aec_domain_common`,
`aec_facade_domain` 1.0.0; `aec_drawing_metadata` 2.0.0) declare a host-form `owl:versionIRI` that itself 404s, so "resolves" and "the target's
versionIRI equals it" cannot both hold literally: the w3id IRI (which resolves) is named, and validation accepts the legacy form as the declared IRI
of the same version. Archives are never edited. **Rejected:** naming the legacy host IRI (it does not resolve).

**Verified.** Full suite with the CI command (92 passed, including new tests for the writer, the validation and the resolution check); a simulated
cut on a throwaway copy gives `aec_drawing_metadata` 4.0.1 naming 2.0.0, 3.0.0 and 4.0.0 with validation 0 errors and nothing left pending;
`check_prior_versions.py` run live: all eight IRIs resolve; `mkdocs build --strict` passes; reasoner clean locally. The tracking issue was exercised end to end by running the job's exact steps from a
scratch workflow (a failing check opened the issue and still failed the job, a second failure commented, a passing run closed it as completed; the test issue was
mirrored to the tracker and resolved on close). **Not verified:** the `verify-prior-versions` job in its real post-deploy context (it only runs after a deploy
to `main`; the scratch copy dropped the deploy dependency and the default-branch guard), and the OntoCanvas acceptance until the patch release is deployed.

**Next step.** Merge; the Release PR bot then proposes the four patch releases; merge it; after the deploy confirm
`curl -sL -H "Accept: text/turtle" https://w3id.org/adiro/aec_drawing_metadata | grep priorVersion` lists 2.0.0, 3.0.0 and 4.0.0 and that OntoCanvas shows the
versions menu.

## 2026-10-09 — Agent guidance: contributor workflow in AGENTS.md; stale Cursor hold removed

**Issue:** none (requested by the maintainer while preparing the team announcement of the release process and the ADIRO Bot).
**Branch:** `docs/agent-contributor-workflow`.

A review of what the repo tells agents found: only two Claude Code skills exist (`deploy`, `pr-review-feedback`), the conventions
live in `AGENTS.md` (read by Claude Code through `CLAUDE.md` and by Cursor through its rule), neither skill mentioned the Release PR
bot, the PR comments or the override file, nothing told an agent to act on the bot's "Required improvements" or to leave versions and
overrides alone, and `.cursor/rules/general.mdc` still said TBox edits were on hold pending RES-27 although `AGENTS.md` lifted that hold.
Changed: a short "Contributor workflow" section in `AGENTS.md` (the order of work, including reading and acting on the bot's comments
and not touching versions or overrides by default, with an exception only for a good reason that follows clearly from the change and is
stated in the PR description, as the maintainer decided); a pointer to it in the `deploy` skill; the stale hold removed from the
Cursor rule. Follow-up in the same PR, after asking how the Cursor hold went stale: it was a summary copied into the Cursor rule on
2026-08-04 (the commit that made `AGENTS.md` canonical), not updated when the hold was lifted on 2026-08-06; and
`.cursor/rules/description.mdc` (March, always on) still described a pre-`AGENTS.md` five-layer structure. Now `general.mdc` is an
import plus one sentence, `description.mdc` is deleted (superseded by `AGENTS.md` "Purpose"; history keeps it), the `deploy` skill's
"In brief" paragraph is replaced by links to the `AGENTS.md` sections, the one Cursor-only rule (helper scripts under `scripts/`
with tests, `uv`) moved into `AGENTS.md`, and `tests/test_agent_adapters.py` fails if `CLAUDE.md` or a Cursor rule grows past 25 lines
or loses its `@AGENTS.md` import. Also, at the maintainer's request, the PR-description rules were deduplicated against the
shared team skills (`tools:pr-descriptions`, `tools:pr-issue-links`): `AGENTS.md` keeps the closing-keyword essentials (the repo is public
and the plugin is private, so outside contributors cannot read the skills) and every ADIRO-specific rule (bot comments, now three;
OntoCanvas preview link; keeping tracker IDs out of public text), and drops the generic style items; the `w3id.org/adiro` rule moved here
from the shared `youtrack` skill, whose repo-specific bullets were removed in the `ai-plugins` PR
([#14](https://github.com/BuroHappoldMachineLearning/ai-plugins/pull/14)), which now also fails CI if a shared skill names a repo.
Review fixes: the `w3id.org/adiro` rule keeps an explicit exception for a branch preview (which must use the raw branch URL);
the adapter test now requires every Cursor rule to import `AGENTS.md`; the `deploy` skill's restated steps (which had already drifted:
"new" terms where `AGENTS.md` says "new or edited") became a bare pointer; and `validate-ontology.yml` now runs `tests/` on the PR,
because they ran only on a push to `main` (a failing test, including the new guard, could merge first). **Verified:** the test suite with the
CI command (72 passed, including the 3 that need pillow); no gate covers the prose, and an agent's behaviour
was not tested. **Not done /
deferred:** a dedicated Claude Code skill for the contributor workflow (a section in `AGENTS.md` reaches every tool; add a skill only
if Claude Code agents still miss it). **Next step:** none planned; the maintainer decided not to trial an agent against the new section
and to trust it. If an agent is later seen skipping the changelog entry, the definition or the bot comments, add a dedicated skill.

## 2026-10-09 — README: latest-release badge per module

- **Branch:** `readme-release-badges`.
- **Changed:** the README header now shows the ADIRO banner on the left (`<img align="left">`, no table) and one badge per module on the right, each reading the latest GitHub Release for that module (`img.shields.io/github/v/release/…?filter=<module>-v*&sort=semver`), so they update themselves when a release is published. `tests/test_readme_badges.py` fails if a module in `src/` has no badge or a badge names a module that no longer exists; `AGENTS.md` lists the badge among the things a new module needs.
- **Decision:** dynamic shields.io badges over generated static ones — nothing to maintain on release. Trade-off: shields prints the whole tag (`aec_provenance-v1.0.0`) as the pill text, because the tags are prefixed; the label is omitted to avoid repeating the module name. The alternative (a generated JSON per module behind a shields "endpoint" badge, giving a clean `aec_provenance | 1.0.0`) was not built.
- **Revised after review:** the badges now read generated per-module JSON (`scripts/release_badges.py` → `docs/badges/<module>.json`, latest *released* version from `versions/`, shields endpoint schema) for a clean `aec_provenance | 1.0.0`; each badge links to the module's documentation page, not its release. The Release notes (`scripts/release_notes.py`, used by `backup-version.yml`) now carry the SemVer bump, previous → this version, a documentation link, a compare link, the changelog section and the PRs that changed `src/<module>.ttl` since the previous release.
- **Review fixes ([#110](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/110)):** (1) `backup-version.yml` gets `pull-requests: read` (the commit→PR lookup needs it; without it every lookup silently fell back to bare commits) and `release_notes.py` now prints a `::warning::` when a lookup fails or `gh` is missing instead of degrading silently; (2) mocked-`_run` tests for `collect_changes` (git range and ontology-file path, duplicate-PR suppression, bare-commit fallback, failed lookup warns, no `gh`, first release makes no calls); (3) the *Release badges* section moved after the whole *What runs automatically* section it had split. The permission itself is not verified on GitHub until the first release after the merge (the warning will show if it is not enough).
- **Verified:** tests pass (50). The endpoint badge renders `aec_provenance: 1.0.0` from the branch's raw JSON. `release_notes.py` run locally against real releases (`aec_facade_domain` 2.0.1, `aec_drawing_metadata` 4.0.0) produces correct output. **Not verified:** how GitHub renders the README layout; the badges' final URL (the JSON is on the site only after this merges and deploys); the changed `backup-version.yml` step on GitHub (the workflow checks out `main`, which lacks the new script until the merge). Centring: GitHub strips CSS, so a centred unit with left-aligned badges needs a table (GitHub draws thin cell borders on it) or a fixed `hspace` (not responsive); the maintainer chose the **centred table with borders**, so the README header is now `<table align="center">` (banner cell + badge cell, `align="left"` `valign="middle"`), replacing the floated-image layout.

---

## 2026-10-09 — Release process docs: scenarios and step-by-step for bump overrides

`docs/contribute/versioning/release-process.md`: the one-paragraph "Examples" under "Overriding a bump or holding a module" became two
linkable subsections, "When to use an override" (a scenarios table: meaning changed with no structural footprint, release one module
and hold another, hold everything, signal a bigger change; plus what an override is not for) and "Applying an override, step by step".
Wording checked against `scripts/prepare_release.py` (the Bump / Driven-by columns, the Held back line, the "no effect" notes, the
close-when-nothing-pending comment, what the cut consumes). Pushed directly to `main` at the maintainer's request (docs only). Not yet
exercised on GitHub: the maintainer plans to test the override file themselves.

## 2026-10-09 — Reasoner now runs on `main` after every ontology push ([#104](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/104))

**Issue:** [#104](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/104). **Branch:** `ci/reasoner-on-main`
([PR #118](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/118)).

New `.github/workflows/reasoning-main.yml`: on push to `main` touching `src/**.ttl` (or the catalog, the reasoning script, the ROBOT
profile, itself) and on manual dispatch, it runs `ENFORCE=1 bash scripts/run_reasoning.sh` over `main`, so two PRs that each passed
alone but conflict together are caught. Design choices: a separate small workflow rather than extending `ontology-reasoning.yml`
(that one is built around PR comments and the base ref); blocking from the start because the suite is clean (no backlog to tolerate),
where "blocking" can only mean a red run plus the failure notification, since the merge has happened; no comment (no PR), the result
goes to the job summary; `cancel-in-progress` because only the latest `main` matters. Verified locally (`ENFORCE=1` run, rc 0) and on
GitHub through a scratch branch that also triggers the workflow: a clean suite passes, and a deliberately unsatisfiable class fails
the run (HermiT named `ZzUnsat`, exit 1, summary step still wrote). Added at the maintainer's request: a failing run opens one tracking issue ("Ontology reasoning fails on
main", created with the ADIRO Bot token so the one-way issue mirror picks it up; falls back to `GITHUB_TOKEN` if the app token
cannot be created), comments on it while later runs keep failing, and closes it when a run passes; a cancelled run leaves it alone.
Verified end to end on a scratch branch (open on the first failure, comment on the second, closed as completed by the passing run;
the test issue was mirrored to the tracker and resolved on close). `AGENTS.md` and `release-process.md` updated. Review fixes: a manual
run is pinned to the default branch (a dispatch could otherwise reason over a feature branch while reporting on `main`), and the
tracking-issue steps use `!cancelled()` instead of `always()` (a run cancelled by a newer push can already have written `reason.rc` and
would overwrite the issue after the newer run recorded the current state).

**Not verified:** the `workflow_dispatch` path (it needs the workflow on `main` first), and the real `main` push path (only a scratch
branch trigger was exercised); the cancelled-run behaviour is reasoned from the Actions semantics, not exercised.
**Rejected:** a warn-only phase (no backlog to tolerate). **Next step:** merge #118; then watch the first push-to-`main` run, start one
manual dispatch and confirm it reports on `main`, and revisit whether the tracking issue is too noisy only if failures turn out frequent.

## 2026-10-09 — Bot work closed out: fork path verified, #106 closed, ideas moved to a Discussion

After [#111](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/111) merged, the fork workflow was tested on a real fork
(`alelom/ADIRO`, two throwaway PRs, both closed unmerged, fork branches deleted; the fork repo itself still exists under the
maintainer's account): a normal fork PR got the version-impact and "Required improvements" comments from the bot with the preview
link on the fork's branch, and the reasoner's report went to the job summary; a PR carrying a symlink as `src/x.ttl` was refused
at the data step and posted nothing. Result recorded on [#113](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/113)
(closed). Not exercised on GitHub: a fork that deletes a module (unit tests only), and removal of a legacy `github-actions[bot]`
comment. [#106](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/106) was closed with its body rewritten to state what
shipped; the remaining ideas are in [Discussion #116](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/116) for
public input. Guidance comment later changed to: title "Required improvements", plain bullets, no intro paragraph, and it exists
only while something needs fixing (previews ride along with the improvements).

## 2026-10-09 — ADIRO Bot posts all PR comments; new PR guidance comment ([#106](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/106))

Agreed with the maintainer: all three PR comments are authored by the ADIRO Bot, the guidance comment is one
summary comment (no inline threads yet), and the first slice includes preview links, the closing-reference check and
the changelog check ([#105](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/105)).

- `scripts/pr_guidance.py` + `.github/workflows/pr-guidance.yml`: flags only what the PR itself touches (graph diff
  against the base), so it never repeats the [#87](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/87) backlog;
  skips the Release PR (`release/next`). Checks: no `rdfs:comment` (with a line link), duplicate `rdfs:label`, no
  `[Unreleased]` entry, newly unused `@prefix`/`owl:imports`, unregistered `Closes #N` (GraphQL, after a 10 s wait for
  GitHub's index), OntoCanvas link per touched module that declares classes.
- `.github/actions/sticky-comment`: the repost-on-change / edit-in-place logic that the two existing workflows each
  carried, now shared. Matches the comment by hidden marker and author; removes older `github-actions[bot]` copies
  best-effort so no duplicate remains. `compat-diff-comment.yml` and `ontology-reasoning.yml` now mint the app token
  (`continue-on-error`, so a token failure never fails the reasoner gate) and use it.
- `AGENTS.md`: new workflow bullet; the "one sticky QC comment" rule gets the guidance comment as an explicit exception.
- Fork PRs: `.github/workflows/pr-comments-fork.yml` (`pull_request_target`, forks only) posts the version-impact and
  guidance comments. Safety rules are in the file header: base-branch code only, fork `src/` + `changelogs/` taken as data
  after refusing symlinks, merge-base comparison, untrusted text only via env vars. The QC comment is not repeated for
  forks (Java reasoner on untrusted input in a privileged context was judged not worth it): the `reason` job still gates
  and its report goes to the job summary. `pr_guidance.py` gained `--head-repo` and `--worktree`; the sticky action
  gained `pr-number` / `head-sha` inputs. **Untestable before merge** (`pull_request_target` runs the base branch's copy):
  needs a real fork PR.
- Review round on PR #111 (Copilot, 8 findings, all valid): the sticky action now deletes only this bot's duplicates and
  the legacy `github-actions[bot]` copy (never another user's comment that quotes the marker); every app token is
  down-scoped (`permission-pull-requests: write`); `pr-guidance.yml` checks out the PR head, not the merge commit;
  touched-term detection now includes blank-node (restriction/list) subgraphs; deleted or renamed modules are no longer
  skipped; and the changelog check moved into `validate_ontology.py` as [#105](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/105)
  specifies (advisory, `ENFORCE_CHANGELOG=1` blocks, shown in the QC comment), with the guidance comment only rendering it.
  `validate-ontology.yml` / `ontology-reasoning.yml` now fetch full history and pass `BASE_REF`.
- Second review round on #111 (4 more, all valid): `compat-diff-comment.yml` / `ontology-reasoning.yml` now keep `GITHUB_TOKEN` read-only (the app token owns commenting); the fork workflow makes `src/` + `changelogs/` exactly the fork's trees (a path checkout only overlays, hiding deleted modules); the `release/next` skip applies only to this repository's branch, not a fork's.
- Third review round on #111 (2 more, both valid): a failed base diff in the changelog check is now a row in the QC results and an error under `ENFORCE_CHANGELOG=1` (it no longer fails open); `compat_diff.py` analyses a module the PR deleted or renamed as all-removed (MAJOR, verdict `MODULE_REMOVED`) and builds its module list from the base as well, and both comment workflows now list the BASE's `src/*.ttl` for the snapshot, so a deletion is no longer invisible (this also fixes the same gap in the same-repo version-impact comment).
- Fourth review round on #111 (1, valid): `pr_guidance.py` loaded the base content from the branch tip while listing changed files
  by merge-base, so edits that landed on the base after the PR branched were treated as the PR's own. It now resolves the merge base
  once and uses it for both (regression test with a real two-branch history).
- Verified: 61 unit tests pass; the script ran against a real past diff; all workflow/action YAML parses. **Not
  verified until the PR runs:** the app token's comment permission on PRs, deleting the old `github-actions` comments, the
  fork skip.
- Deferred (kept in #106): inline review comments/suggestions, specification-sync reminder, public-repo hygiene, stale
  Release PR nudge, plain-language version impact, LLM-drafted definitions.

## 2026-10-09 — Release notes: summary line first, link bullets straight after (no header)

Requested by the maintainer: the "PATCH release · 2.0.0 → 2.0.1 · Compare" line (or "First release") is now the
first text of every Release page, followed directly by the three link bullets with no "Relevant links" header.
`scripts/release_notes.py` `render` reordered; test and `release-process.md` updated. The bot needs no workflow
change: `backup-version.yml` already calls the script. Verified by the unit tests; all ten existing Releases were
regenerated with `gh release edit`. Supersedes the ordering in the entry below.

## 2026-10-09 — Release notes start with Relevant links; badges link to the release page

- **Changed (pushed directly to `main` at the maintainer's request):** each Release body now starts with a **Relevant links** block in this order — the module's documentation page (`…/ADIRO/ontologies/<module>/`), `Ontology (latest)`, `This version` (w3id) — with no "Canonical URLs" header, trailer or duplicate title; the summary line keeps the bump, previous → this and the compare link. The README badges link to the release page of the module's latest version again (reversing the earlier choice of the documentation page); `prepare_release.py` bumps those links at the release cut, and `tests/test_readme_badges.py` fails if a link does not match the module's declared version (compared with `src`, not `versions/`, so it holds in the window between merging a Release PR and the snapshot landing).
- **Back-edited:** the notes of all ten existing Releases were regenerated with `release_notes.py` and applied with `gh release edit` (no deploys triggered). That exposed a bug in my first version: the earliest *tagged* releases (e.g. `aec_drawing_metadata` 3.0.0, `aec_common_symbols` 2.0.0) were labelled "First release" because only git tags were consulted, although earlier versions existed. The previous version is now the highest of the tags **and** the changelog `## [x.y.z]` headings; the compare link and PR list appear only when the previous release is tagged, otherwise a one-line note says why. The ten Releases were then regenerated again with the fix.
- **Verified:** 54 tests pass; `release_notes.py` output checked locally for `aec_facade_domain` 2.0.1, `aec_drawing_metadata` 3.0.0, `aec_common_symbols` 2.0.0 and `aec_provenance` 1.0.0. Live Release notes are refreshed by re-running `backup-version.yml` for a tag.

---

## 2026-10-09 — Releases: let "Latest" follow the newest release

- **Changed:** removed `--latest=false` from `gh release create` in `release-pr.yml`, and marked `aec_facade_domain-v2.0.1` as Latest by hand. With one "Latest" slot for several independent module streams, `--latest=false` left the badge (and the repo front-page Releases box) stuck on `aec_facade_domain-v2.0.0` from August; it now means "most recent release". Pushed directly to `main` at the maintainer's explicit request (a one-flag change), not via a PR. Not yet seen in a real release: the next Release PR merge is the first run without the flag.

---

## 2026-10-09 — Describe four facade terms; first real run of the Release PR bot ([#87](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/87), partial)

- **Branch:** `describe-facade-terms`.
- **Changed:** added `rdfs:comment` to `Gasket`, `Firestop`, `CavityBarrier` and `Louvre` in `aec_facade_domain` (plain-language, consistent with their place in the taxonomy; no standards text), with a changelog entry; regenerated `docs/`. Annotation-only → PATCH (2.0.1). Leaves 76 undescribed terms in this module.
- **Why now:** an innocuous real change to exercise the Release PR bot end to end ([#99](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/99)): after merge `release-pr.yml` should open "Release cut: aec_facade_domain 2.0.1" (ready, not draft, because the changelog entry exists); merging that PR should publish the Release, start `backup-version.yml` from the `release` event, push the snapshot and dispatch the Pages deploy ([#100](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/100)).
- **Verified:** `validate_ontology.py` valid (pre-existing warnings only); `compat_diff.py` requires PATCH and `prepare_release.py plan` shows `aec_facade_domain` 2.0.0 → 2.0.1. Reasoner/ROBOT not run locally (CI runs them on the PR).
- **Next step:** watch the bot run after merge; record what each step did, and close #100 if the deploy dispatch fires.

---

## 2026-10-09 — Release PR bot ([#99](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/99))

- **Branch:** `release-pr-bot`.
- **Added:** `scripts/prepare_release.py` (`plan` / `apply` / `body` / `tags`, reusing `compat_diff.analyze_module`), `tests/test_prepare_release.py` (8 tests), `.github/workflows/release-pr.yml` (job `tag` publishes merged release cuts and dispatches `backup-version.yml`; job `release-pr` rebuilds `release/next` and opens/updates/closes the PR, as a draft while a pending module's `[Unreleased]` is empty). `backup-version.yml` now retries the snapshot push up to 3 times (several tags are dispatched together). `release-process.md` and `AGENTS.md` describe the flow.
- **Identity (supersedes the `GITHUB_TOKEN`-only decision below):** after discussion the workflow acts as the **ADIRO Bot** GitHub App (org-level app installed on this repo; secrets `ADIRO_BOT_APP_ID`, `ADIRO_BOT_PRIVATE_KEY`; bot account `adiro-bot[bot]`, logo = the site favicon), via `actions/create-github-app-token`. App-token events start other workflows, so the Release PR gets the normal PR checks and a published Release starts `backup-version.yml`; the explicit dispatch was dropped, the in-job validation kept as a fail-fast check. Verified end to end on a scratch branch (since removed): PR authored by `adiro-bot`, commits by `adiro-bot[bot]`, `validate`/`reason`/`comment` checks ran on the PR, draft → ready on adding a changelog entry, closed with branch deleted on revert. Other bot features: [#106](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/106).
- **Original decisions (the first bullet's token reasoning is superseded):** `GITHUB_TOKEN` only (no PAT) — validation runs inside the job because the bot PR starts no PR checks, and `backup-version.yml` is dispatched explicitly. PATCH-only changes also open the PR. Empty changelog → draft, not a failure. The `AGENTS.md` versions line and the `CHANGELOG.md` rollup are rewritten by the script, not left as a checklist item.
- **Override added after review:** `config/release_overrides.json` maps a module to one value — `"patch"`/`"minor"`/`"major"` (raises the bump, never lowers it below the classifier; consumed by the cut) or `"hold"` (leaves the module out until deleted). Chosen over separate `bump`/`hold` keys so there is one thing to remember. Invalid entries fail the workflow. 8 further tests (16 in `tests/test_prepare_release.py`).
- **Empty `[Unreleased]`:** keep the draft as the fallback; the early check at PR time is tracked in [#105](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/105).
- **Decision recorded in docs:** the Release PR does not re-run the reasoner (see `release-process.md` → Design decisions); the real gap — a PR's reasoner check is not repeated after another PR merges — is tracked in [#104](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/104).
- **Verified:** 26 tests pass; `plan` and `tags` report nothing pending on current `main`. End to end on GitHub, using a scratch branch (workflow temporarily triggered on it, since `workflow_dispatch` needs the file on the default branch) with one annotation change in `aec_facade_domain` and then reverted: (1) pending change + empty changelog → draft PR `Release cut: aec_facade_domain 2.0.1` opened (#102, since closed), body correct, diff = version/IRI/changelog heading/rollup/`AGENTS.md` line; (2) changelog entry added → same PR updated, turned ready for review, warning gone; (3) change reverted → PR closed with a comment and `release/next` deleted. All three runs green. Scratch branch and PR #102 removed.
- **Review fixes ([#103](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/103) review):** (1) completion is idempotent — `tags` now lists every merged cut with no snapshot under `versions/` (not "no git tag"), and the workflow creates the Release or re-dispatches `backup-version.yml` if the Release exists; (2) `release/next` is deleted when nothing is pending even if its PR is already merged (verified on GitHub with a stray branch). The create-vs-re-dispatch shell branch has not been run on GitHub. (3) Both jobs now run only on the default branch (`if: github.ref == refs/heads/<default>`), so a manual `workflow_dispatch` on a feature branch cannot publish tags or force-push to `release/next`; verified on GitHub with a scratch branch whose push trigger was enabled — both jobs skipped, nothing published.
- **Process:** added the `pr-review-feedback` skill (`.claude/skills/pr-review-feedback/`) and an `AGENTS.md` section "Responding to PR review feedback": when a review link is pasted, evaluate each comment, ask when unsure, fix on the PR branch, reply with the commit, resolve fixed threads, leave declined ones open.
- **Not verified:** the `tag` job's real path (merge a Release PR → `gh release create` → dispatch `backup-version.yml` → snapshot → Pages deploy). `tags` is unit-tested and returns nothing on current `main`; the first real Release PR merge is the first run of it, and also the first real exercise of the [#100](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/100) deploy dispatch after a *new* snapshot.

---

## 2026-10-09 — Fix snapshot → Pages deploy in `backup-version.yml` ([#100](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/100))

- **Changed:** `backup-version.yml` now dispatches `generate-deploy-docs.yml` after pushing a snapshot (a `GITHUB_TOKEN` push does not trigger it); `git pull --rebase` before the snapshot push; new `workflow_dispatch` trigger with a `tag` input so the job can be started for an existing tag (needed by the Release PR bot, [#99](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/99)); `actions: write` permission; tag read via `env` instead of inline expression. `release-process.md` updated to match.
- **Follow-up in [#101](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/101):** the deploy dispatch was made **unconditional** (no longer only when a snapshot was pushed). *Considered and chosen:* a re-run for a tag with an existing snapshot then still redeploys Pages, which repairs a release whose deploy was missed (the 2026-08-10 situation) and makes the step testable without a new release; cost is one extra docs build per re-run, and the deploy publishes `main` HEAD rather than the tagged commit (same as any push). *Rejected:* dispatching only when a snapshot was pushed — a re-run would say "nothing to do" and leave a missed deploy broken. Restoring the condition is a one-line change (`if: steps.push.outputs.pushed == 'true'` plus the output) if re-runs prove frequent. Verified by running the job from the PR branch: [backup-version run 37945555974](https://github.com/BuroHappoldMachineLearning/ADIRO/actions/runs/37945555974) started [deploy run 37945620215](https://github.com/BuroHappoldMachineLearning/ADIRO/actions/runs/37945620215), green through `deploy` and `check-links`. `AGENTS.md` (Versioning → "Releases are per-module") now documents the dispatch, per its "This file ↔ CI" rule, after review feedback on #101.
- **Verified (partly, before the follow-up):** `workflow_dispatch -f tag=aec_domain_common-v2.0.1` ran green end to end (tag parse, tag/version check, snapshot, release-notes edit). The snapshot already existed, so nothing was pushed and the new "Publish the snapshot to GitHub Pages" step was **skipped** — the `GITHUB_TOKEN` dispatch of `generate-deploy-docs.yml` is **not yet exercised**. [#100](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/100) stays open until the next real release shows a deploy run started by the snapshot job.
- **Next step:** Release PR bot ([#99](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/99)).

---

## 2026-10-09 — Cut the backlog release (metadata 4.0.0, common_symbols 3.0.0, domain_common 2.0.1, provenance/geometry 1.0.0)

- **Why:** a UC-03 consumer (an annotation-tool import) needed `layoutTitle` and `hasScale` on `Layout`, merged on `main` but never tagged; `main` still declared `aec_drawing_metadata` 3.0.0, so two different files shared one version label. Tracked for automation in [#99](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/99); a related snapshot-deploy bug in [#100](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/100).
- **Changed:** bumped `owl:versionInfo` / `owl:versionIRI` per the compat-diff required bump (`aec_drawing_metadata` MAJOR — `isRevisionOf` removed; `aec_common_symbols` MAJOR — `appearsOn`/`isReferencedBy` removed; `aec_domain_common` PATCH — annotation-only; `aec_provenance` and `aec_geometry` first release at their declared 1.0.0); moved each `[Unreleased]` under a dated heading; updated the root `CHANGELOG.md` rollup and the versions line in `AGENTS.md`; regenerated `docs/`. `aec_facade_domain` has no pending change (required bump NONE) and is not released.
- **Fixed:** the stale "All additive → MINOR (3.1.0)" note in `changelogs/aec_drawing_metadata.md`, which contradicted the breaking removal recorded in the same section; reworded to MAJOR 4.0.0. Removed the "baseline, not yet cut" stub from `changelogs/aec_provenance.md`.
- **Verified:** `validate_ontology.py` clean (pre-existing warnings only), `compat_diff.py` reports every module `OK`, `pytest tests` 18 passed. The reasoner was not re-run: no axioms changed, only version strings and changelogs.
- **Known gap:** `backup-version.yml` pushes snapshots with `GITHUB_TOKEN`, which does not trigger the Pages deploy ([#100](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/100)); the deploy is dispatched by hand after the snapshots land.
- **Next step:** Release PR bot ([#99](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/99)) and the `backup-version.yml` fix ([#100](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/100)). Tell the UC-03 consumer the versions to import.

---

## 2026-10-06 — Fix the two failing "Generate and Deploy Documentation" runs

- **Issue:** none filed (CI maintenance). **Branch:** `main` (uncommitted at time of writing).
- **Failures:** run 37488574638 (`generate-docs`) — bot's `git push` rejected non-fast-forward because a second
  push to `main` (`a2ee7dc`) landed ~40 s after the first (`4884917`) while it was generating; deploy and
  check-links were skipped. Run 37488671653 (`check-links`) — lychee exit 2 solely from 5 timeouts on
  `https://www.gnu.org/licenses/gpl-3.0.html` (pyLODE footer on every page); 0 real errors.
- **Changed:** `generate-deploy-docs.yml` — added a `concurrency` group (no cancel) so runs serialise, and
  `git pull --rebase` before the bot push; lychee gets `--max-retries 3 --retry-wait-time 5 --timeout 30`;
  `.lycheeignore` excludes `www.gnu.org/licenses/` (flaky from runners, pyLODE-generated, not ours).
- **Verified:** diagnosis from run logs only; fixes **not** exercised — needs a push to `main` to confirm.
- **Next step:** after merging, confirm the next two back-to-back pushes both go green.

---

## 2026-10-02 — Describe the generic undescribed terms (#87, partial)

**Branch:** `describe-easy-terms` · **PR:** (draft) · partial progress on [#87](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/87)

### What changed

Added `rdfs:comment` to the **50 generic undescribed terms** the validator flags — the 47 in
`aec_domain_common` (materials, facing materials, section shapes, generic shapes, symmetry, structural
properties/components/members, disciplines) and the 3 `OrientationValue` individuals in
`aec_drawing_metadata` (`Horizontal`/`Vertical`/`Undefined`). Each is a short plain-language definition
consistent with the term's place in the taxonomy. Inserted by a one-off script (each label matched exactly
once). Changelogs updated.

**Deliberately skipped:** the **80 specialised facade terms** (`aec_facade_domain`) — curtain-wall systems,
glazing units, framing members, etc. — which need domain knowledge to define accurately. Left for a facade
expert / a later pass.

Opened as a **draft** PR for review: some of the softer domain_common guesses (`Function`, `Restraint`,
`Chord/bracing`, `Upstand`, `Masterplan`) may want tweaking or removing.

### Verified

- `validate_ontology.py` → `aec_common_symbols`, `aec_domain_common`, `aec_drawing_metadata` now at **0**
  undescribed; only `aec_facade_domain` (80) remains. `generate_docs.py` → 6/6. `ENFORCE=1 run_reasoning.sh`
  → consistent + satisfiable, ERROR 0 / WARN 0 / INFO 25 (unchanged — annotation-only).

### Next step

Review the draft; adjust/remove any definitions; decide whether/when to tackle the facade terms.

## 2026-10-01 — Add `:ProjectNumberField` and `:SheetSizeField` to the title-block scheme

**Branch:** `add-projectnumber-sheetsize-fields` · **PR:** (open) · post-merge follow-up to #76

### Why

`aec_drawing_metadata` already declared `:projectNumber` and `:sheetSize` as datatype properties, but neither
had a `TitleblockFieldScheme` concept pointing at it (no `aprov:mapsToFieldProperty`), so an extraction pipeline
had no way to discover them. Both are common printed title-block fields (Project No. pairs with Project Title;
sheet size is a standard `A1`/`A0` field).

### What changed (`src/aec_drawing_metadata.ttl`, additive)

- Added `:ProjectNumberField` (→ `:projectNumber`) and `:SheetSizeField` (→ `:sheetSize`), following the exact
  pattern of the existing field concepts (`skos:definition`, `@en`/`@de` `prefLabel`/`altLabel`, `inScheme`,
  `expectedRange xsd:string`, `mapsToFieldProperty`; `skos:example` `A1`/`A0` for sheet size). Changelog updated.
- German synonyms (`Projektnummer`, `Blattgröße`, `Format`) are **provisional** — not verified against real
  sheets the way the existing ones are; flagged in the PR for review.

### Verified

- `validate_ontology.py` → metadata OK (only the pre-existing `Horizontal`/`Undefined`/`Vertical` enum
  warnings). `generate_docs.py` → 6/6. `ENFORCE=1 run_reasoning.sh` → consistent + satisfiable, ERROR 0 / WARN 0
  / INFO 25 (unchanged — the two new SKOS concepts add no violations). No altLabel collisions.

### Next step

Open the PR; it runs clean through `validate-ontology.yml` and the reasoner gate.

## 2026-09-28 — New `aec_geometry` module (bounding boxes + coordinate frames); Croissant evaluation

**Issue:** [#90](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/90), [#91](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/91) · **PR:** #76 · **Branch:** `aec-provenance-model`

### Why

MLE-364 needs title-block field **localisation** (bounding boxes), and the review of Tianyang's UC-03 three-layer
design (MLE-A-7: Semantic/Geometry/Provenance, GeoSPARQL-aligned geometry, `aec_provenance`-reusing provenance)
showed a clean shared model. Plus the Croissant evaluation (#91) concluded Croissant is dataset-level metadata
(complementary to per-assertion `aec_provenance`), with one near-term impact: borrow its bounding-box `format`
convention. The workshop decisions: new `aec_geometry` module; the bbox is a **provenance-bearing class** (who
made it — model vs human — and with what confidence, separate from the value's confidence).

### What changed

- **New `src/aec_geometry.ttl` (v1.0.0)** — `BoundingBox` (`⊑ geo:Geometry` and `aprov:InferredEntity`; shape as
  `bboxXYXY` string, `XYXY` aligned to Croissant), `CoordinateFrame` (unit, `coordinateSpace` = `page_display_pt`
  fixing origin/axes, artifact/page, rotation, profile), `inCoordinateFrame`, `hasBoundingBox`. GeoSPARQL reused
  as a local stub (option 1A; WKT/spatial queries deferred, #36). Imports `aec_provenance`.
- **`aec_provenance`** — added `:InferredEntity` (⊑ `prov:Entity`); `FieldAssertion ⊑ InferredEntity`; re-homed
  the domains of `hasInferenceMeta` and `hasConfidence` from `FieldAssertion` to `InferredEntity` so a bounding
  box carries the same provenance/confidence. Fixes the confidence-on-geometry domain concern UC-03 flagged.
- **`aec_drawing_metadata`** — imports `aec_geometry`; adds `hasCoordinateFrame` (`DrawingSheet` →
  `CoordinateFrame`). A field assertion links to its box via `aec_geometry:hasBoundingBox`.
- **Plumbing:** `catalog-v001.xml`, `generate_docs.py` sort order (geometry=1), `CHANGELOG.md` rollup, new
  `changelogs/aec_geometry.md`, `AGENTS.md` module + version lists.
- **New design doc** `docs/design-decisions/croissant-comparison.md` (#91) committed earlier this session and
  linked in the PR body.
- **New design doc** `docs/design-decisions/geometry-coordinate-frames.md` — a worked ABox example (title-block
  region → `BoundingBox` → `CoordinateFrame`; a `FieldAssertion` with its own confidence) plus a coordinate-frame
  explainer (page_display_pt vs native-PDF vs raster, origin/axes, rotation/DPI). Inspired by the presentation in
  Tianyang's UC-03 HTML (MLE-A-7). `mkdocs build --strict` clean. The idea of embedding an OntoCanvas iframe on
  every module page, and enriching the ontologies index with a responsibilities narrative, are filed as a docs
  follow-up rather than done here.
- **Scope:** UC-01 only. UC-03-specific geometry (CoordinateTransform, crop/symbol metrics, clickable/navigation
  geometry) deliberately left out; the module is named so UC-03 slots in without conflict.

### Verified

- `validate_ontology.py` → 6/6 valid (only pre-existing warnings). `generate_docs.py` → 6/6.
  `ENFORCE=1 run_reasoning.sh` (HermiT 17, 6 modules) → consistent + satisfiable, exit 0; ROBOT ERROR 0 / WARN 0
  / INFO 25.

### Next step

Update the PR body (add `aec_geometry` to the ontology changes + an OntoCanvas preview row). Then the inference
side can localise the title-block region (its bbox); and the UC-03 work extends `aec_geometry` with its transform/navigation
geometry.

## 2026-09-25 — Reverse the DAnO decision: remove the compatibility layer; comparison stays documentation-only

**Issue:** [#77](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/77) · **PR:** #76 · **Branch:** `aec-provenance-model`

### Why

At the 2026-09-25 BH/BCU workshop, Mohamed Ragab (@MohamedRagabAnas) argued that embedding a DAnO crosswalk
*in the ontology* risks confusing users, and that the comparison is better kept as GitHub documentation only.
@alelom agreed. This **reverses** the decision this PR had recorded (an optional `aec_dano_alignment.ttl`
annotation-level compatibility layer). Decision re-recorded on #77 and on the PR.

### What changed

- **Removed** `src/aec_dano_alignment.ttl` and its generated docs (`docs/aec_dano_alignment.{ttl,html}`,
  `docs/ontologies/aec_dano_alignment.md`) and `changelogs/aec_dano_alignment.md`.
- **Config:** dropped the module from `src/catalog-v001.xml`, the sort-order map in `scripts/generate_docs.py`,
  and the `CHANGELOG.md` rollup row. Regenerated docs (now 5 modules; mermaid diagrams + indexes no longer
  mention it).
- **Hand-written docs brought in line** (documentation-only comparison; no shipped artifact / module / minted
  `:closeMatch`): `docs/design-decisions/dano-comparison.md`, `external-ontology-imports.md`,
  `changelogs/aec_provenance.md`, `AGENTS.md`, `docs/specification/ORSD_v1.3.md`, and the UC-01/UC-03 module
  hierarchy diagrams + version-history entries. Spec-doc versions were **not** re-bumped — these are edits within
  the same unreleased PR, so the existing version-history entries were corrected in place. `#81` (staleness check
  for compatibility-layer mappings) is now **moot** → to be closed.

### Verified

- `validate_ontology.py` → 5/5 valid (only pre-existing warnings: an unused import and the #87 undescribed
  enums). `mkdocs build --strict` → clean. `ENFORCE=1 run_reasoning.sh` (HermiT 17, 5 modules) → consistent +
  satisfiable, exit 0; ROBOT report ERROR 0 / WARN 0 / INFO 23. Residual grep → no remaining claim that a
  layer/module/minted property ships.

### Next step

Continue the remaining PR #76 items. Then: the in-depth Croissant-vs-PROV-O comparison (#91) and reviewing
Tianyang's UC-03 three-layer overview (MLE-A-7) — several of its provenance ideas (bounding boxes, #90) are
shared with UC-01 and should be folded in before merge.

## 2026-09-24 — Close the inference-consumption gaps on the field scheme (G1–G3)

**Issue:** [MLE-364](https://bhmlrnd.youtrack.cloud/issue/MLE-364) epic (sub-tasks B4/MLE-376, B5/MLE-377; RES-108) · **PR:** #76 · **Branch:** `aec-provenance-model`

### Why

A review of PR #76 against the MLE-364 inference sub-tasks found the ontology core (`aec_provenance` +
`TitleblockFieldScheme`) directly consumable — concept IRI = `adiro_uri`, `prefLabel`/`altLabel`(`@en`/`@de`) =
`key_name`/`key_synonyms`, `skos:example` = `example_values`, `FieldAssertion` = the ABox target; all 14
`mapsToFieldProperty` targets and both `expectedRange` classes exist — but with three gaps that would have
forced a second ADIRO round-trip mid-inference:
- **G1** — B5 (MLE-377) binds unmatched keys to a `UnidentifiedField` red-flag kind that did not exist.
- **G2** — B4 (MLE-376) HALTs on a synonym colliding with an altLabel of a *different* field kind, but the
  scheme itself shipped a collision: `"Verfasser"@de` on both `:OriginatorField` and `:DrawnByField`.
- **G3** — MLE-364/RES-108 asks the public source basis of each synonym/example to be recorded; the TTL had none.

### What changed (`src/aec_drawing_metadata.ttl`, additive)

- **G1** — added `:UnidentifiedField` (`skos:Concept`, with `skos:definition`), deliberately **not**
  `skos:inScheme :TitleblockFieldScheme` so it is a valid `aprov:assertsFieldKind` target but never a field the
  pipeline searches for. It carries no `mapsToFieldProperty` (no promotion).
- **G2** — dropped `"Verfasser"@de` from `:OriginatorField` (kept `Planverfasser`@de there); `Verfasser` now
  denotes only `:DrawnByField`. Added a `skos:note` on the scheme stating the uniqueness contract B4 relies on.
- **G3** — added a `skos:scopeNote` on the scheme recording the public/private content policy and that per-item
  `dcterms:source` follows once the anonymised dataset (RES-108/RES-104) is public.
- Also added a one-line `skos:definition` to **every** field-kind concept (feeds B3's prompt `description`;
  clears them from the `#87` undescribed-terms backlog).
- Changelog `[Unreleased]` updated; still a **MINOR** (additive) bump on top of the pending 3.x line, except the
  breaking inverse removal already recorded (MAJOR 4.0.0 at the cut).

### Verified

- `validate_ontology.py` — all 6 modules OK; metadata now down to the 3 pre-existing enum individuals
  (`Horizontal`/`Undefined`/`Vertical`) as the only undescribed terms.
- `generate_docs.py` — 6/6 regenerated.
- `ENFORCE=1 run_reasoning.sh` (HermiT 17) — consistent + satisfiable, exit 0; ROBOT report ERROR 0 / WARN 0 /
  INFO 23 (advisory, unchanged).

### Next step

Re-anchor the PR #76 body to the MLE-364 epic and note advancement of #65/#67/#69 + the RES-108 classification
still owed off-repo. Then the inference side (ml-cad-assistant) can start B1 against the shipped scheme: `adiro_uri`
= the concept IRI, unmatched → `:UnidentifiedField`, confidence written directly to `aprov:hasConfidence`
(the interim JSON-envelope step in MLE-377 is now obsolete since the provenance module lands in this PR).

---

## 2026-09-21/22 — DAnO settled: no import, an optional compatibility layer; specification realigned

**Issue:** [#77](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/77) (mirrored to
[RES-110](https://bhmlrnd.youtrack.cloud/issue/RES-110)) · **PR:** #76 · **Branch:** `aec-provenance-model`

### Why

The published external-import rule listed DAnO as undecided, and
`docs/design-decisions/titleblock-vocabulary-review.md` recommended **aligning** ADIRO's provenance properties
to `dano:`. Meanwhile `aec_provenance` on this branch had **minted parallel terms** — the opposite. A published
page and a module in flight disagreed, and the review that made the recommendation had read DAnO from its
generated specification, explicitly flagging that domains and ranges needed confirming first.

### What changed

- **Verified against the raw `dano.ttl`** (fetched from `https://w3id.org/dano`, HTTP 200). The recommendation
  does not survive: no `rdfs:subPropertyOf` alignment to any DAnO provenance term is available. DAnO's
  `inferred*` are **datatype** properties while ADIRO's are **object** properties (ill-typed, non-DL, the gate
  rejects it); `dano:inferredAt` ranges over `xsd:date`, disjoint from ADIRO's `xsd:dateTime` (inconsistency);
  `dano:hasConfidence` carries `rdfs:domain dano:DrawingElement` (would entail every `FieldAssertion` is a
  drawing mark). Only the first fails locally — the other two are silent behind an undeclared stub and surface
  for anyone merging ADIRO with DAnO, which is the audience an external IRI serves.
- **New `src/aec_dano_alignment.ttl`** — an optional compatibility layer, seven `skos:closeMatch` mappings,
  imports the core, **nothing imports it**. No ADIRO core module mentions DAnO. Reason is lifecycle and scale,
  not logic (see the correction below).
- **Minted `metadata:depicts`, then withdrew it on 2026-09-22.** It was justified by suite ORSD CQ 5.2 /
  OI-1, which sits in CQG 5 and is traced to neither UC-01 nor UC-03, the two use cases this PR is scoped to.
  It also had no consumer and pre-empted two that exist: UC-06 specifies `depictsMaterial` and UC-07
  `depictsElement`, both with domain `Drawing` rather than the `DrawingElement` CQ 5.2 frames. OI-1 is open
  again. The conflation of the suite's CQ numbering with the use cases' own is what let it in - see #86.
- **New `docs/design-decisions/dano-comparison.md`** — per-term verdicts plus the reasoning, stated **per ADIRO
  module** rather than in the aggregate.
- **Corrected `external-ontology-imports.md`**: split option 1 into 1A (reuse the external IRI as a stub) and
  1B (mint our own and relate); fixed advice that re-imposed the problem it described (the MIREOT section told
  readers to escape a too-narrow domain with `rdfs:subPropertyOf`, which inherits that very domain); added the
  test for when a core module may reference an external vocabulary at all.
- **Corrected `titleblock-vocabulary-review.md`** — superseded-in-part banner and the three places its
  recommendation is reversed.
- **ORSD edited in place** (NFR 2, NFR 3) and **UC-07 gains §7.5**.
- **Specification realigned (2026-09-22).** Three documents contradicted or omitted what ships. **UC-03 design
  decision 1** said provenance lives "upstream/elsewhere" — a statement about one query-layer module read as
  though it settled the matter for the suite; amended, with the parsing/OCR half intact. **UC-01** described
  only one of the two ways a title-block value can now be carried; gained a design note, an `aec_provenance`
  row in §7 and open issue G11. **Both use-case module-hierarchy diagrams** were labelled "unchanged" and
  showed four modules. **ORSD** now records that CQG 2/3/4 are what justify `aec_provenance`, and the
  structural gap that the suite CQGs and per-use-case CQs never reference each other (#86).
- **`AGENTS.md`** gains the two conventions whose absence caused all of the above: **ADIRO is a suite** (with
  the module list corrected from "four"), and **Ontology ↔ specification** — the existing docs rule only ever
  covered *generated* pages, which is why pyLODE output was regenerated diligently while the ORSD and use
  cases went stale.

### Decisions taken

- **Mint, do not align.** Every DAnO mapping is annotation-level; the DAnO IRIs are declared nowhere in ADIRO
  and appear only as annotation values.
- **Crosswalks live in an optional layer, not the core.** Because an unreleased third-party vocabulary should
  not force a version bump on a module downstream consumers pin, and because crosswalks to DiCon, ifcOWL, BOT
  and GeoSPARQL would otherwise accumulate in two core files.
- **ADIRO individuals are detections, not idealised drawing constructs** (#84). `dano:Dimension`'s exact
  cardinalities would infer undetected parts into existence on clipped historical sheets, making CQ 2.1
  unanswerable. Completeness belongs in SHACL over a finished extraction, not in OWL over detections.

### Corrected mid-flight (recorded because the wrong version was briefly committed)

- **Two claims were overstated and then fixed.** The compatibility layer was justified partly by ADIRO's own
  "pin the core, not a merged alignment graph" advice. That does not hold for annotation-only mappings: SLME
  locality is defined over logical axioms and `skos:closeMatch` is not one, so inlining them would have
  endangered nobody. The honest reasons are lifecycle and scale. Separately, the layer was described as
  matching "the shape DAnO uses for GeoSPARQL" — DAnO *inlines* its GeoSPARQL stubs; GeoSPARQL is the one
  shipping core plus alignments.
- **An earlier framing of ADIRO and DAnO as occupying "different layers" was wrong for the suite.** It holds
  for the title-block vocabulary it was written about. `aec_common_symbols` sits squarely in DAnO's layer and
  is currently the **thinner** of the two (3 classes against 8). The comparison page says so.

### Verified

- `uv run python scripts/validate_ontology.py` — **all 6 modules valid**.
- `ENFORCE=1 bash scripts/run_reasoning.sh` — HermiT **consistent + satisfiable, exit 0**; ROBOT `report`
  **ERROR 0**, WARN 242, INFO 23. Identical to the pre-change run but for one new `missing_definition` row on
  `:depicts` (the repo-wide advisory). **No report row mentions `skos:closeMatch` or any `dano:` IRI** — the
  undeclared external IRIs are absorbed as annotation values exactly as intended.
- `uv run mkdocs build --strict` — passes, so every new cross-reference resolves.
- `uv run python scripts/generate_docs.py` — run; regenerated artefacts committed separately.

### Next step

Issues filed for everything deliberately not solved here: **#79** (does `aec_common_symbols` adopt a
drawing-mark decomposition, for UC-03/UC-07), **#80** (define the CQ 5.2 / OI-1 linking property when a
consumer needs it), **#85** (direct properties vs `FieldAssertion` — when is a value promoted, do the direct
properties deprecate), **#86** (suite ORSD and use-case ORSDs do not reference each other),
**#81** (staleness check for compatibility-layer mappings — a hazard the separation introduces), **#82**
(ORSD v1.2 reuse-justification section), **#83** (DisplayElement/DescriptionElement split), **#84**
(detections-not-drawings). [RES-68](https://bhmlrnd.youtrack.cloud/issue/RES-68) needs a note that its
SLME-extraction premise does not apply to DAnO.

---

## 2026-09-18 — External-import strategy clarified, ported to GitHub, and made normative in the repo

**Issue:** [RES-68](https://bhmlrnd.youtrack.cloud/issue/RES-68) / [RES-59](https://bhmlrnd.youtrack.cloud/issue/RES-59) · **Branch:** `docs/external-import-strategy`

### Why

Discussion [#71](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/71) ("External import strategy
discussion (MIREOT vs SLME)") read as if the MIREOT-vs-SLME question were still open. It is not — it was decided
on 2026-08-03 in KB RES-A-12 and has been normative in `docs/contribute/versioning/` since. #71 is in fact the
**review deliverable for RES-59**, answering the four open questions that the decision deliberately left open;
Zaalouk resolved RES-59 on 2026-09-17 pointing at Discussions #70 and #71. The title caused the confusion.

### What changed

**Off-repo (done first, because the repo docs cite them):**

- **KB RES-A-12 ported to [Discussion #74](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/74)**
  and closed as *resolved* (it records a decision, not an open question). Per MAN-8, GitHub is the source of
  truth for ADIRO decisions; the note contained no client/project/security-classification detail, so it could be
  published as-is. The ported version is **more current than the original**: decision marked ratified, the four
  open questions answered, the `BOT`/`STAR` correction folded in, and a third option added (below).
- **RES-A-12 frozen** in YouTrack with a pointer stub, matching the RES-A-9/21/22/23 precedent. *The YouTrack MCP
  exposes no delete operation, so the article is frozen rather than deleted* — flag if actual deletion is wanted.
- **Clarifying comment posted on #71** covering the three corrections below.
- **[#77](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/77) opened** — DAnO import-vs-align.
- **RES-68 unblocked**: `Backlog` → `Open`, description rewritten with the ratified rule and the cleared blockers.

**In-repo:**

- **New `docs/design-decisions/external-ontology-imports.md`** — the short normative rule, pointing at #74 for the
  reasoning. No `.pages` file in that folder, so awesome-pages picks it up automatically.
- **`docs/contribute/versioning/index.md`** §Imports and **`versioning-vs-odk.md`** retargeted off the now-frozen
  RES-A-12 and onto the new page + #74, and updated to name the stub-alignment option.
- **`versioning-vs-odk.md` §Import handling reassessed from "Par." to a deliberate divergence.** Adding
  stub-alignment as the *preferred* option moves us off ODK's norm, which treats an SLME extract as the normal
  reuse path and discourages definition-less terms. The row now says so, and names the cost, rather than
  claiming parity — the earlier "Par." predated the third option and would have hidden the amendment.

### Substantive corrections made to #71

1. **`BOT`/`STAR` were inverted.** #71 recommended `BOT` to avoid pulling BFO/PROV/CCO in behind a GeoSPARQL term.
   Per the ROBOT docs, `BOT` is the method that includes the seed's *super-classes*; `STAR` is the minimal one
   that does not. `STAR` is the mitigation, `BOT` is the risk. The `STAR` default therefore stands unchanged.
2. **SLME is not non-deterministic.** It is deterministic for a fixed input; the variable is *which graph you feed
   it*. Verified that **GeoSPARQL core (v1.1.1) has no `owl:imports` and none of the BFO/PROV/CCO/`locn:`/`schema:`
   alignment axioms** — those sit in a separate, non-imported file. The whole re-homing hazard in #71 §4 is
   conditional on merging a file we have no reason to merge. Encoded as "pin the core file, not a merged graph".
   Nuance retained: upward `subClassOf`/`subPropertyOf` alignments are ⊤-local and dropped by `STAR`, but
   `owl:equivalentClass` alignments are neither ⊥- nor ⊤-local and *would* survive `STAR`.
3. **MIREOT cannot fix a domain mismatch.** Its third URI asserts a local *superclass* only. The DAnO cases are
   therefore mint-and-align cases, not MIREOT cases.

### New: a third option that the original MIREOT-vs-SLME framing missed

The WIP `aec_provenance` module (branch `aec-provenance-model`) already uses **local typing stubs +
`rdfs:isDefinedBy`, with no `owl:imports` and no extraction**, so the module stays self-contained and the
reasoning CI resolves offline via `catalog-v001.xml`. This is the same conclusion the title-block review reached
independently for DAnO — *"align to `dano:`, do not import it"*. Added to #74 and the new docs page as **option 1**,
ahead of SLME and MIREOT.

### Verified

- `dano.ttl` fetched directly: `hasConfidence rdfs:domain dano:DrawingElement` (while `DrawingElementMeta`'s
  comment claims confidence) and `depicts rdfs:domain dano:DisplayElement` with no range — both #71 claims hold.
  This also closes the stated method caveat in `titleblock-vocabulary-review.md`, which read DAnO from its
  generated specification rather than its raw TTL.
- GeoSPARQL core fetched from `http://www.opengis.net/ont/geosparql` and checked for `owl:imports` and
  alignment terms — none present.
- `BOT`/`TOP`/`STAR` semantics taken from the ROBOT `extract` documentation, not from memory.

**Not run:** no `.ttl` changed, so `validate_ontology.py`, `generate_docs.py` and the reasoning gate were not
exercised. This is a docs-only change. The `aec_provenance` WIP on the other branch was **read but not touched**.

### Deferred / rejected

- **DATA-A-10 not ported.** It is an ABox-versioning proposal covering DVC, annotation-tool schemas and project datasets —
  private-pipeline material, and partly superseded by RES-27. Note that `AGENTS.md` cites it as the versioning
  "rationale", which is a questionable citation now; left alone as out of scope.
- **RES-A-13 / RES-A-17 / DATA-A-9 not ported.** Pipeline- and annotation-tool-internal; DATA-A-9 specifically documents how
  the private ml-pipeline parses ADIRO, which `AGENTS.md` keeps internal by design.
- Did **not** edit `docs/design-decisions/index.md` to list the new page — awesome-pages generates that nav.

### Next step

1. Merge this branch (docs-only).
2. Settle [#77](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/77): does `aec_provenance` supersede
   DAnO's provenance terms outright, reducing the DAnO question to `depicts`/`isDepictedBy` only?
3. RES-68 is now unblocked but has no external term to import yet — it stays `Open` until #77 lands or GeoSPARQL
   is un-deferred ([#36](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/36)).
## 2026-09-18 — New foundational module: aec_provenance (reified assertions + PROV-O provenance)

**Issue:** [Discussion #72](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/72) (field-kind +
assertion/provenance model); drives the ml-drawing-assistant epic
[MLE-364](https://bhmlrnd.youtrack.cloud/issue/MLE-364). · **Branch:** `aec-provenance-model`

### What changed
- Added `src/aec_provenance.ttl` — a new **foundational, domain-neutral** module (v1.0.0) for representing an
  inferred/extracted value as a first-class **`FieldAssertion`** carrying its own provenance: `assertedBy`
  (which region asserted it), `hasInferenceMeta` → `InferenceMeta` (`inferredBy`/`inferredWith`/`inferredFrom`/
  `inferredAt`), `hasConfidence` (decimal on the individual — no RDF-star), and `hasLiteralValue` /
  `hasValueEntity` / `capturedCaption`. **PROV-O-aligned** (`prov:wasAttributedTo` / `wasDerivedFrom` /
  `generatedAtTime` / `Agent`), with PROV-O terms declared locally (not `owl:imports`) so reasoning stays
  offline. PROV-O suggested by Tianyang Huang.
- Wired plumbing: `src/catalog-v001.xml` (IRI→file mapping, forward-looking for when the drawing modules import
  it), `scripts/generate_docs.py` `dependency_order` (`aec_provenance: 0`, sorts first), `changelogs/
  aec_provenance.md`, and the `CHANGELOG.md` rollup (also corrected `aec_drawing_metadata` 2.0.0→3.0.0 there).

### Design decisions taken (ahead of team consensus, per the epic owner's go-ahead)
- **Field-kind + reified assertion (Option 3)** over one generic `asserts` or many `assertsX` properties:
  synonyms live on the field-kind concept, provenance is data (per-occurrence `assertedBy`) not schema.
- **Two-module layering**: this generic module is separate from the (title-block-specific) field-kind scheme,
  which will live in `aec_drawing_metadata` and `owl:imports` this. Not yet done — next increment.
- Confidence on the **assertion individual** (DANO-style `hasConfidence`), not on a triple — sidesteps the
  RDF-star/reification question left open in Discussion #62.

### Verified
- `uv run python scripts/validate_ontology.py src/aec_provenance.ttl` → **valid** (parse + version-consistency).
- **Not yet run:** ROBOT/HermiT DL reasoning (`scripts/run_reasoning.sh`, needs Java) and
  `scripts/generate_docs.py` (docs regen). Additive standalone module, nothing imports it yet, so the merged
  suite is unchanged in practice — but both gates should run before PR.

### Next step
- Increment 2: add the SKOS `TitleblockFieldScheme` (field kinds with `@en`/`@de` labels/synonyms, generic
  public examples, `skos:closeMatch` to DANO/DiCon) to `aec_drawing_metadata`, make it `owl:imports`
  `aec_provenance`, add `owl:hasKey` on `Person`/`Organisation` (Discussion #73), keeping the shipped
  `asserts*` properties in place (hybrid; deprecate later). Then run docs regen + reasoning before opening a PR.

---

## 2026-09-17 — Design-decision docs rehomed; leftover links retargeted

**Issue:** docs tidy-up (no new YouTrack ticket) · **Branch:** `main`

### What changed

Published modelling notes moved out of `docs/contribute/design-decisions.md` and the old
`docs/modularization/` working-notes tree into `docs/design-decisions/` (including
`modularization/` as a *published* subsection). `mkdocs.yml` `exclude_docs` no longer lists
`modularization/` (that pattern would have excluded the new subsection as well).

Link retargets in the same change:

- Contribute index, README Pages URL, changelog `KeyPlan` evidence path
- `docs/uc-orsd/` → `docs/specification/use-cases/` in live design-decision / changelog citations
- Cross-links between the vocabulary review and the field survey
- `AGENTS.md` keep-in-sync note for what the docs site excludes

Historical worklog paths were left as written (they record what existed at the time).

### Verification

- `uv run mkdocs build --strict` (or equivalent) after the retargets
- Spot-check that Design decisions nests in the nav (index + children, including Modularization)

### Next step

None for links. Dropped files (`ontology-modularization-todo.md`, `titleblock-placement-option1-plan.md`,
`aec_titleblock-build-plan.md`) were already gone or not moved; the survey now says so instead of pointing
at a missing plan file.

---

## 2026-09-14 — `hasScale` extended to `Layout`

**Issue:** [RES-89](https://bhmlrnd.youtrack.cloud/issue/RES-89) · **PR:** [#66](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/66) · **Branch:** `res-89-aec-titleblock-tbox`

### What changed

`hasScale`'s domain widened from `DrawingSheet` to `owl:unionOf (DrawingSheet Layout)`. A sheet routinely
carries several drawings at different scales — a detail at 1:5 beside a plan at 1:100 — which a single
sheet-level scale cannot express.

### Why the domain had to be widened rather than the property just reused

This is the part worth recording, because the wrong version of it would have passed every gate.

`rdfs:domain` in OWL is an **inference rule, not a constraint**. Leaving the domain as `DrawingSheet` and
asserting `someLayout hasScale "1:5"` does not raise an error — it makes a reasoner **infer
`someLayout a DrawingSheet`**. That layout would then inherit `DrawingSheet`'s restrictions and be required to
contain a `Titleblock` and a `Layout` of its own.

And it would **not** have been caught: nothing in the suite declares `Layout` and `DrawingSheet` disjoint, so
there is no inconsistency for HermiT to find. The suite would have reasoned cleanly while quietly typing every
scaled layout as a drawing sheet.

Used the `owl:unionOf` domain idiom already established in this file by `hasOrientation` (`Section ∪ Detail`),
rather than inventing a pattern.

### Two smaller things

**Non-breaking.** A *widened* domain permits strictly more than before; every existing `DrawingSheet hasScale`
assertion stays valid with identical entailments. (Contrast the `RevisionTable` relaxation in the entry below,
which was also non-breaking but did cost an entailment.)

**A stale hint fixed.** `layoutTitle`'s `extractionHint` said *"the number belongs to layoutIdentifier and the
scale is sheet-level"* — written yesterday, wrong as of today. Corrected, and the correction is a genuinely nice
outcome: the common caption line `3  MULLION HEAD  1:5` now decomposes **completely** across three properties on
a single `Layout` — `layoutIdentifier` `3`, `layoutTitle` `MULLION HEAD`, `hasScale` `1:5`. Nothing in that
caption is left unmodelled.

### Verification

| Check | Result |
| --- | --- |
| `validate_ontology.py` (all four) | pass |
| **HermiT** | pass — `reason exit code: 0`; checked specifically because a union domain is the kind of change that can go non-DL |
| ROBOT `report` | **0 ERROR**, WARN unchanged at 222 |
| `compat_diff.py` | Forecast unmoved (already MAJOR for unrelated reasons) |
| `generate_docs.py` | 4/4 clean |
| `mkdocs build` | not re-run — no nav or page added or removed |

### Note for later

UC-07 proposes `scaleRatio` (decimal, for arithmetic) alongside the string `hasScale`. It is **not in any shipped
module** — checked. If it lands, it will want the same union domain for the same reason, and the two should be
widened together rather than drifting apart.

---

## 2026-09-14 (resolution) — `DrawingSheet`'s `RevisionTable` cardinality relaxed to `min 0`

**Issue:** [RES-89](https://bhmlrnd.youtrack.cloud/issue/RES-89) · **PR:** [#66](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/66) · **Branch:** `res-89-aec-titleblock-tbox`

### The decision

Option 1 of the three offered in the entry below. `DrawingSheet contains exactly 1 RevisionTable` becomes
`min 0`. A sheet is no longer required to contain a revision table **directly**, which is what the new
`Titleblock contains RevisionTable` restriction needed in order to be usable: `:contains` is direct and
non-transitive, so a revision table nested in the title block left the sheet with none of its own and the
`exactly 1` manufactured a phantom.

The constraint and the real-world layout were in conflict. The layout wins.

### Two things to be precise about

**`min 0` is logically vacuous.** It asserts nothing at all. The file uses it as a documentation idiom for "may
contain", so the honest description of this change is that **the constraint was removed**, not weakened.

**It is non-breaking by the repo's own spec, but an entailment is lost.**
`docs/governance/compatibility-diff-algorithm-spec.md` classifies `RESTRICTION_LOOSENED` as non-breaking, and
nothing previously valid becomes invalid. But you could previously infer, from `?x a DrawingSheet` alone, that
`?x` contains a `RevisionTable` — and you no longer can. A consumer relying on the *inference* rather than on
asserted data would notice, even though the classification says non-breaking.

**Checked before changing it, rather than asserting a risk vaguely:** I had flagged this as "weakens a
constraint UC-01 may rely on". Grepping `docs/uc-orsd/` and `ORSD_v1.1.md`, **no competency question or SPARQL
depends on the cardinality** — the only UC-01 mentions are a design note about `MetadataContainer` parentage and
a `hasRevisionTable` property that lives in UC-01's own working file, not in the shipped module. So the risk I
flagged does not appear to be real. Recording that I looked, since "may rely on" is cheap to write and expensive
to leave unresolved.

Incidentally the check turned up a **malformed restriction in
`docs/uc-orsd/uc01/uc01-merged-for-visualization.ttl` line 146** — one restriction node carrying
`minQualifiedCardinality 0`, `qualifiedCardinality 1` *and* `maxQualifiedCardinality 1` together. That file is a
visualisation artefact, not a source module, so it is out of scope here and untouched, but it is wrong and worth
someone's attention.

`Titleblock`'s own `exactly 1` on `DrawingSheet` is **unchanged** — every sheet still has exactly one title block.

### Verification

| Check | Result |
| --- | --- |
| `validate_ontology.py` (all four) | pass |
| **HermiT** | pass — `reason exit code: 0` |
| ROBOT `report` | **0 ERROR**, WARN unchanged at 222 |
| `compat_diff.py` | Forecast unmoved — `aec_drawing_metadata` was already MAJOR for unrelated accumulated reasons. `RESTRICTION_LOOSENED` is non-breaking by the spec, so this change would not have forced a MAJOR on its own |
| `generate_docs.py` | 4/4 clean |
| `mkdocs build` | not re-run — no nav or page added or removed |

### Next step

Unchanged: @alelom's `CHANGES_REQUESTED` (2026-08-13) still stands, and the survey's German-sampling gap would
settle three parked terms cheaply.

---

## 2026-09-14 (late) — `dimensionUnits` withdrawn; nine terms in the PR

**Issue:** [RES-89](https://bhmlrnd.youtrack.cloud/issue/RES-89) · **PR:** [#66](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/66) · **Branch:** `res-89-aec-titleblock-tbox`

### What changed

Removed `dm:dimensionUnits` at Ahmed Elnagar's direction. The PR now adds **nine** terms, not ten.

It goes on the same grounds as `planKey`: a German-practice field (DIN 1356-1's `1:50 – m,cm`) appearing in none
of the four surveyed projects, so it does not clear the agreed `<40%-of-sheets` rule.

**Worth distinguishing from the other withdrawals, though.** The vocabulary review had separately confirmed
this concept is genuinely *not* covered by any other module or use case
(`titleblock-vocabulary-review.md` §2.3). So unlike `Discipline` or `scale`, this is **purely an evidence call,
not a redundancy one** — the concept is real and unclaimed, no sampled drawing printed it, and the sample is
UK/US. Of the five withdrawn terms it is the likeliest to return.

### A pattern now visible across the withdrawals, recorded in the survey doc

Three of the five withdrawn terms — `planKey`, `dimensionUnits`, and arguably `supplementaryTitle` — are
**German/DIN practice, and the survey contains no German project.** The `<40%` rule is behaving correctly on the
corpus it has, but the corpus has a known geographic gap. "Withdrawn" for these should be read as *not evidenced
by these four UK/US projects*, not *not a real title-block field*. **Sampling one German project would settle all
three at once** — that is now the single highest-value addition to the survey.

| File | Change |
| --- | --- |
| `src/aec_drawing_metadata.ttl` | Term removed |
| `changelogs/aec_drawing_metadata.md` | Relocated-terms list corrected to seven; withdrawal recorded |
| `docs/modularization/titleblock-field-survey-2026-09.md` | §7.3 gains the term and the German-sampling-gap note |
| `docs/modularization/titleblock-vocabulary-review.md` | §2.3 row struck through and corrected — it still said "Keep", which was live guidance pointing the wrong way |
| PR #66 title/body | Updated; body also corrected to the British `Organisation` spelling standardised in `fd75891` |

### Verification

| Check | Result |
| --- | --- |
| Terms added by this PR | **9** (was 10) |
| `validate_ontology.py` (all four) | pass |
| **HermiT** | pass — `reason exit code: 0` |
| ROBOT `report` | **0 ERROR**; WARN down by one, the removed property's `missing_definition` |
| `generate_docs.py` | 4/4 clean |
| `mkdocs build` | not re-run — no nav or page was added or removed this time |

### `Titleblock` can now contain `KeyPlan`, `Legend` and `RevisionTable`

Added three `min 0` `contains` restrictions to `Titleblock`, mirroring the `DrawingSheet` pattern. All three are
commonly printed inside the title-block strip rather than standing alone, so both placements are now expressible.
`KeyPlan`'s and `Titleblock`'s `rdfs:comment`s say so, since that is where an annotator or pipeline author looks.

#### ⚠️ One genuine trap this opens, flagged not fixed — `RevisionTable`

`:contains` is **direct** containment. Its own comment says so and it is not declared `owl:TransitiveProperty`.
And `DrawingSheet` requires **exactly 1** `RevisionTable` (`owl:qualifiedCardinality "1"`), not `min 0`.

So for a sheet whose revision table sits inside the title block, asserting the natural thing —
`sheet contains titleblock` and `titleblock contains revisionTable` — leaves the sheet with **no direct
`RevisionTable`**. The `exactly 1` then forces a reasoner to infer a *second, anonymous* revision table that the
sheet contains directly. A phantom.

**This does not show up in the gates**, which is why it is worth writing down: the TBox reasons cleanly (HermiT
exit 0, 0 ERROR) because the contradiction only materialises once individuals exist. It would surface as strange
inferences during the first real extraction run, at which point it is much more expensive to diagnose.

`KeyPlan` and `Legend` are **unaffected** — both are `min 0` on `DrawingSheet`, so nesting them costs nothing.

Three ways out were put to Ahmed Elnagar:

1. **Relax `DrawingSheet`'s `RevisionTable` to `min 0`** — simplest, but weakens a constraint UC-01 may rely on.
2. **Add a transitive super-property** (e.g. `containsTransitively`, with `contains rdfs:subPropertyOf` it) and
   hang the cardinality restrictions off that instead. Correct, and more work.
3. **Require the pipeline to always assert the sheet-level edge too**, treating the title-block edge as
   additional rather than alternative. No ontology change; pushes the burden onto every consumer, and nothing
   enforces it.

**Option 1 chosen and implemented** — see the entry above.

### Next step

Unchanged: @alelom's `CHANGES_REQUESTED` from 2026-08-13 still stands and now predates every structural decision
on the branch. Plus the survey's German-sampling gap above, which is cheap and would resolve three parked terms.
And the `RevisionTable` cardinality question above, which wants an answer before extraction data lands.

---

## 2026-09-14 (cleanup) — `aec_titleblock` module deleted; PR trimmed to what it needs

**Issue:** [RES-89](https://bhmlrnd.youtrack.cloud/issue/RES-89) · **PR:** [#66](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/66) · **Branch:** `res-89-aec-titleblock-tbox`

### What this PR now is

Following the relocation in the entry below, `aec_titleblock` held nothing. It is now **deleted outright** —
closing the open question that entry left. The suite is back to **four modules**.

The PR is no longer "add a title-block module". It is: **add ten terms to `aec_drawing_metadata` and remove a
module that was never released.**

### Deleted

| Deleted | Why |
| --- | --- |
| `src/aec_titleblock.ttl`, `src/aec_titleblock.display.json` | The module |
| `src/catalog-v001.xml` entry | Otherwise imports resolve to a missing file — this breaks reasoning CI if missed |
| `scripts/generate_docs.py` dependency-order entry | Renumbered the remaining four |
| `mkdocs.yml` nav entry | The nav is curated, not auto-discovered |
| `changelogs/aec_titleblock.md`, `CHANGELOG.md` rollup row | Per-module changelog for a module that no longer exists |
| `docs/aec_titleblock.{ttl,html,display.json}`, `docs/ontologies/aec_titleblock.md` | Generated artefacts |
| `docs/modularization/aec_titleblock-build-plan.md` | A repo-side build plan — passes, PR sequence, plumbing checklists — for a deleted module. Moot in full |
| `docs/modularization/titleblock-placement-option1-plan.md` | Reasoned entirely about whether to mint `tb:` counterparts vs reuse `dm:`. That is no longer a choice that can be made |

### Rescued before deleting, because it existed in exactly one place

The `aec_titleblock.ttl` footer carried the **record of ~15 terms considered and rejected, with reasons** —
the Option 1 reuse table, the PR #66 withdrawals (`hasLegalOwner`, `DocumentType` trio), the survey-driven
withdrawals, the redundancy drops, and the parked organisation roles. None of it is carried in
`aec_drawing_metadata`, and deleting the file would have destroyed it.

Rehomed as **§7 of `docs/modularization/titleblock-field-survey-2026-09.md`**, which is the natural home: that
document is the evidence base, and most of the withdrawals are its findings. The operative conclusion of the
deleted Option 1 plan (extraction writes straight onto `dm:` with no staging layer, accepted explicitly) is
preserved in §7.1; its one still-open question — whether the "one document, many sheets can disagree" gap
should be tracked separately — is already recorded as a next step in the 2026-08-19 entry below.

### Kept, deliberately

- **`titleblock-field-survey-2026-09.md`** — the evidence for every term in the PR and every term withdrawn
  from it. A reviewer asking "why this term and not that one" needs it.
- **`titleblock-vocabulary-review.md`** — the review against the use cases and DANO. Untouched by the module
  restructuring, and its findings are still open and forward-looking: the UC-01 placement contradiction, the
  ~40-terms-without-a-competency-question traceability gap, and the DANO alignment evidence that bears on the
  not-yet-built provenance layer.

### Verification

| Check | Result |
| --- | --- |
| `validate_ontology.py` | pass — **4 modules** (was 5) |
| **HermiT** | pass — `reason exit code: 0`; merge input is now four files |
| ROBOT `report` | **0 ERROR.** WARN 223, unchanged — the terms moved namespace, they did not disappear |
| `generate_docs.py` | **4/4** clean |
| **`mkdocs build`** | **clean** — run this time specifically because the nav entry and a nav target were removed |
| Dangling references | None. The four remaining mentions of the name are all deliberate history: this worklog, the `dm:` changelog (recording where the terms came from), and the survey doc |

### Next step

The PR title and body still describe adding a title-block module, which is now the opposite of what it does —
they need rewriting before re-review is requested. Alessio's `CHANGES_REQUESTED` from 2026-08-13 is now seven
rounds stale and predates every structural decision in this branch.

---

## 2026-09-14 (team decision) — `aec_titleblock` emptied into `aec_drawing_metadata`; `layoutTitle` added

**Issue:** [RES-89](https://bhmlrnd.youtrack.cloud/issue/RES-89) · **PR:** [#66](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/66) · **Branch:** `res-89-aec-titleblock-tbox`

### The decision

The team decided that **`aec_drawing_metadata` is the single repository for drawing metadata**, so new concepts
land there rather than in a parallel module. All eight remaining `aec_titleblock` terms were relocated, keeping
their local names. `aec_titleblock` now declares nothing.

This resolves, **in the strict direction**, the ambiguity flagged in the entry below after Zaalouk's 2026-09-10
comment. The loose reading was "`dm:` keeps what it already has, `tb:` mints the gaps"; the strict reading was
"new terms go to `dm:` too". The team took the strict one. Worth noting the flag was warranted — the two
readings did lead to materially different repositories.

| Term | Now |
| --- | --- |
| `Organisation`, `organisationName` | `dm:Organisation`, `dm:organisationName` |
| `assertsMetadataFor`, `assertsClient`, `assertsOriginator` | same names, `dm:` |
| `dimensionUnits`, `assertsCrossReferenceNumber`, `extractionHint` | same names, `dm:` |

### `layoutTitle` — new, and a modelling call worth recording

Added `dm:layoutTitle`: the caption naming an individual `Layout`, distinct from sheet-level `drawingTitle`. A
sheet routinely carries several drawings — details, sections, plans at different scales — each with its own
printed title; without this they all inherit one title and cannot be told apart. It pairs with the existing
`layoutIdentifier` as title-to-number.

**Modelled as a datatype property on `Layout`, not as a class**, despite being asked for as "LayoutTitle". The
reason is the same test that put `KeyPlan` in `dm:` as a region yesterday, applied in the other direction: a key
plan's value *is* a diagram, so it is a region; a title's value is *text*, so it is a property. The decisive
precedent is `drawingTitle` — the sheet's own title is a datatype property even though it too is visible text
inside a region. Named `layoutTitle` (lowerCamelCase) per the `AGENTS.md` property convention.

If what was actually wanted is a **labellable caption region** for annotators to box, that is a different term
(`LayoutTitle` as a `MetadataContainer` subclass, with a new annotation label) and is cheap to add alongside — say so
and it lands in one edit.

### What changed

| File | Change |
| --- | --- |
| `src/aec_drawing_metadata.ttl` | +8 relocated terms, +`layoutTitle`; new `skos:` prefix (first use in this module); two new section headers carrying the naming rationale |
| `src/aec_titleblock.ttl` | All terms removed. Header rewritten to record where each went; the withdrawal record (§a–d) **kept deliberately** |
| `changelogs/*.md` | Both updated; the `aec_titleblock` one gains a banner, and its term list is struck through rather than deleted |
| `docs/modularization/aec_titleblock-build-plan.md` | §1 superseded-banner + rewritten; new §1d on the relocation |
| `docs/**` | Regenerated |

### Two things flagged rather than decided unilaterally

1. **Whether `src/aec_titleblock.ttl` should exist at all.** It validates while declaring nothing, but publishes
   an empty docs page. Deleting it also means removing the `catalog-v001.xml` entry, the `generate_docs.py`
   dependency-order entry, the `mkdocs.yml` nav entry, its changelog, the display JSON and the generated
   artefacts — and it changes what PR #66 *is*, from "add a module" to "add terms to an existing module". **Not
   done**, because deletion was not part of the instruction and it is the reviewer's call. The file is kept with
   its header explaining why, and its record of rejected vocabulary intact — that record is not carried in
   `aec_drawing_metadata` and is the most expensive thing to rediscover.
2. **This reverses the 2026-08-11 separate-module decision** (Ahmed Elnagar + Alessio Lombardi), which rested on
   independent releasability and on volume. Neither concern has gone away — the volume one *sharpens* as the
   parked vocabulary lands, since the SKOS schemes, extension properties and provenance layer now all target
   `dm:`. The team has judged single-responsibility more valuable, which is a legitimate trade, but Alessio
   co-owned the decision being reversed and his `CHANGES_REQUESTED` is still standing.

### Verification

| Check | Result |
| --- | --- |
| `validate_ontology.py` (all five) | pass |
| **HermiT** | pass — `reason exit code: 0` |
| ROBOT `report` | **0 ERROR.** WARN 222 → 223 (+1, the new `layoutTitle`; the relocated terms carry their existing `missing_definition` warnings across unchanged) |
| **`duplicate_label`** | **none** — the namespace merge introduced no label collision, which was the specific risk of moving eight terms into a populated module |
| `compat_diff.py` | `aec_drawing_metadata` still forecasts `3.0.0` (MAJOR), unmoved — the relocated terms are all `TERM_ADDED` here. `aec_titleblock` still skipped, no released snapshot, so nothing published is invalidated |
| `generate_docs.py` | 5/5 clean |
| `mkdocs build` | not run this session |

### Next step

The PR now changes a **released** module substantially and an unreleased one down to nothing, which is a
materially different review from the one Alessio last looked at on 2026-08-13. His `CHANGES_REQUESTED` is now
six rounds stale. Re-review is the blocker, and the PR title/description no longer describe what the PR does —
both need updating before asking.

---

## 2026-09-14 — `sheetNumber` withdrawn (9 → 8); `KeyPlan` added to `aec_drawing_metadata`

**Issue:** [RES-89](https://bhmlrnd.youtrack.cloud/issue/RES-89) · **PR:** [#66](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/66) · **Branch:** `res-89-aec-titleblock-tbox`

### What changed

Two changes at Ahmed Elnagar's direction, continuing the survey-led pruning of the entry below.

| File | Change |
| --- | --- |
| `src/aec_titleblock.ttl` | `sheetNumber` removed (8 terms left); footer §(a3) rewritten to cover the whole sheet-position pair |
| `src/aec_drawing_metadata.ttl` | **New class `KeyPlan`** (`MetadataContainer` subclass) + a `min 0` `contains` restriction on `DrawingSheet`, matching the `Legend`/`Note` pattern |
| `changelogs/aec_titleblock.md`, `changelogs/aec_drawing_metadata.md` | Both `[Unreleased]` sections updated |
| `docs/modularization/aec_titleblock-build-plan.md` | §1 table; §1b extended; new §1c on the `KeyPlan` placement |
| `docs/modularization/titleblock-field-survey-2026-09.md` | §2 row corrected — see below |
| `docs/**` | Regenerated |

### `KeyPlan` went to `dm:`, not `tb:` — and why that is the substantive decision here

`dm:` models **detectable visual regions**; `tb:` models **content a title block asserts as text**. A key plan's
value *is* the diagram, so it is a region, and it sits beside `Legend` and `RevisionTable`. Putting it in `tb:`
would have made it the first `tb:` term that is not an assertable string. This also matches Zaalouk's
2026-09-10 position on PR #66 that `aec_drawing_metadata` should be the metadata repository.

### Three things flagged rather than left to be discovered

1. **A new annotation label.** `KeyPlan` carries `labellableRoot true`, and annotation class labels derive from
   the IRI local name — so the annotation label set changes. Needs coordination per KB
   [DATA-A-9](https://bhmlrnd.youtrack.cloud/articles/DATA-A-9) before annotation work assumes the old set.
2. **This PR now touches a released module.** It was scoped to `aec_titleblock` (unreleased); `dm:` is at
   `2.0.0`. The addition is non-breaking (`TERM_ADDED`) and `dm:` was *already* forecast MAJOR for unrelated
   accumulated reasons, so the forecast does not move — but reviewers should be told, not left to notice. If
   Alessio would rather keep the PR single-module, backing `KeyPlan` out means reverting two source edits
   (`src/aec_drawing_metadata.ttl`, its changelog), dropping build-plan §1c and the survey-row correction, then
   regenerating — it is not a clean single-commit revert, because this commit also carries the `sheetNumber`
   removal and the shared narrative docs.
3. **ISO 7200 §5.1.6 is mandatory, and we have now dropped it.** With `sheetNumber` gone the sheet-position
   concept is absent entirely. That is defensible on the evidence (zero of four projects printed it) but it is a
   deliberate departure from a mandatory clause, so it is recorded as such in the footer and build plan. If ISO
   7200 conformance ever becomes a stated goal, this is the decision to revisit.

### A correction to my own earlier analysis

The survey doc's §2 filed "key plan" under *already covered by `dm:Note`/`dm:Legend`*. That was wrong, and the
row is now struck through and corrected in place. The error came from trusting Project B's description
("copyright statements, usage notes and disclaimers" — almost certainly a mislabelled cell) over Project D's
accurate one ("denotes the location of the drawing in plan", value type *Sketch*).

Stated honestly: the real evidence for `KeyPlan` is **one solid project plus one doubtful one**, not the clean
2-of-4 the raw frequency table suggests. Still far better than the four withdrawn terms (zero each), but the
distinction matters if anyone re-runs this reasoning.

### Verification

| Check | Result |
| --- | --- |
| Term counts | `aec_titleblock` **8** (was 9); `aec_drawing_metadata` +1 class |
| `validate_ontology.py` (all five) | pass |
| **HermiT** | pass — `reason exit code: 0` |
| ROBOT `report` | **0 ERROR.** WARN flat at 222 — −1 from the removed property, +1 from the added class |
| `compat_diff.py` | `aec_drawing_metadata` still forecasts `3.0.0` (MAJOR) — unchanged, the addition is `TERM_ADDED`. `aec_titleblock` still skipped, no released snapshot |
| `generate_docs.py` | 5/5 clean |
| `mkdocs build` | not run this session |

### Next step

Unchanged and now five rounds stale: **Alessio's `CHANGES_REQUESTED` from 2026-08-13 has never been
re-reviewed.** Also still open — the ambiguity in Zaalouk's 2026-09-10 comment about whether "`dm:` contains all
metadata" extends to newly minted terms. Note `KeyPlan` is the first term to land under the broad reading of
that, so it is a useful concrete case to put to him.

---

## 2026-09-11 — Three unevidenced terms withdrawn; 12 → 9

**Issue:** [RES-89](https://bhmlrnd.youtrack.cloud/issue/RES-89) · **PR:** [#66](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/66) · **Branch:** `res-89-aec-titleblock-tbox`

### What changed

Removed `supplementaryTitle`, `numberOfSheets` and `planKey` from `aec_titleblock` at Ahmed Elnagar's
direction. The evidential basis: none of the three appears in **any** of the four projects in the field survey
(`docs/modularization/titleblock-field-survey-2026-09.md`), so none clears the agreed `<40%-of-sheets` rule.
All three were minted from a standards reading (ISO 7200 §5.2.3, §5.1.7; DIN SPEC 91391-1) rather than from
drawings — the same basis the `hasLegalOwner` withdrawal already rejected in review round 1: *"the standard is
not the evidence — the drawings are."*

This is the survey cutting **both** ways. The 2026-09-01 entry below used it to add a term; the same document
justifies subtracting three.

| File | Change |
| --- | --- |
| `src/aec_titleblock.ttl` | Three property blocks removed; new footer §(a3) recording each withdrawal with its standard reference and the reason |
| `changelogs/aec_titleblock.md` | Term count 12 → 9; new withdrawal paragraph above the 2026-08-13 one |
| `docs/modularization/aec_titleblock-build-plan.md` | Status line and §1 table updated; new §1b |
| `docs/**` | Regenerated (`generate_docs.py`) |

### Two things deliberately *not* done, and why

- **`sheetNumber` was kept** even though its partner `numberOfSheets` is gone. The extraction hint was rewritten
  so it no longer points at a term that does not exist, and the footer says plainly that the total is not
  modelled. Do not read the surviving half as an oversight — the pair was never evidenced *as a pair* on a real
  sheet, and `sheetNumber` alone did appear.
- **`planKey` is withdrawn as unevidenced, not as wrong.** The surveyed corpus is UK/US projects and the plan
  key is German practice (DIN SPEC 91391-1), so its absence is at least partly a **sampling gap in the survey**
  rather than a finding about the field. It is a plausible return once German projects are sampled, and the
  footer and changelog both say so — otherwise a future reader will re-derive the term and re-argue the case.

Also fixed two now-dangling references to `planKey` that would have survived the removal: one in
`assertsCrossReferenceNumber`'s `rdfs:comment` ("stored whole and verbatim, like planKey") and one in the build
plan §1a, plus the footer §(b) line that cross-referenced `numberOfSheets`.

### Verification

| Check | Result |
| --- | --- |
| Term count | **9** (was 12) |
| `validate_ontology.py` (module, then all five) | pass |
| **HermiT** | pass — `reason exit code: 0` on the merged 5-module suite |
| ROBOT `report` | **0 ERROR.** WARN 225 → 222 — exactly one fewer `missing_definition` per removed property, no new class of finding |
| `compat_diff.py` | `aec_titleblock` **skipped — no released snapshot to diff against.** So the removals raise no breaking-change flag: the module is pre-release and nothing downstream can have consumed these terms |
| `generate_docs.py` | 5/5 clean |
| `mkdocs build` | not run this session |

### Next step

Unchanged from the entry below — Alessio's `CHANGES_REQUESTED` from 2026-08-13 is still standing and has never
been re-reviewed, through three subsequent rounds of work. That, not further vocabulary work, is what the PR is
waiting on. Zaalouk's 2026-09-10 comment endorsed the Option 1 reuse design but left one ambiguity open (whether
"`aec_drawing_metadata` should contain *all* metadata" extends to newly minted terms, which would reopen the
settled separate-module decision) — worth one clarifying question.

---

## 2026-09-01 (decision) — `assertsCrossReferenceNumber` minted; organisation-role candidates parked

**Issue:** [RES-89](https://bhmlrnd.youtrack.cloud/issue/RES-89) · **PR:** [#66](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/66) · **Branch:** `res-89-aec-titleblock-tbox`

### The decision

Reviewed the two candidates from the field-survey proposal below (same date, earlier entry) and decided: mint
`tb:assertsCrossReferenceNumber` now; park the four organisation-role candidates (`assertsContractor`,
`assertsEngineer`, `assertsArchitect`, `assertsConsultant`) for a future discussion, since `tb:assertsOriginator`
already covers the general case for a first pass.

Also anonymised the survey document at the same time: it named four real BH projects, and was rewritten to refer
to them only as Project A–D, consistently, so it can be cited outside project-restricted channels without a
mapping back to specific clients/projects appearing in this public repo.

### What changed

| File | Change |
| --- | --- |
| `src/aec_titleblock.ttl` | New datatype property `assertsCrossReferenceNumber` (domain `dm:Titleblock`, range `xsd:string`), following the `planKey`/`asserts*` conventions — stored whole and verbatim, `skos:altLabel`s for the observed labels, no controlled vocabulary for the issuing system |
| `changelogs/aec_titleblock.md` | `[Unreleased]` section updated: term count 11 → 12, new bullet recording the addition and the parked organisation-role candidates |
| `docs/modularization/aec_titleblock-build-plan.md` | Status line and §1 term table updated to 12 terms; new §1a summarising the addition |
| `docs/modularization/titleblock-field-survey-2026-09.md` | Rewritten: project names anonymised to Project A–D; §3.1 and §3.2 updated from "candidate" to "parked" / "decided, implemented"; §6 recommendation rewritten as an outcome |
| `docs/**` | Regenerated (`generate_docs.py`) |

### Verification

| Check | Result |
| --- | --- |
| Term count | **12** (was 11) |
| `validate_ontology.py` (module, then all five) | pass |
| **HermiT** | pass — `reason exit code: 0` on the merged 5-module suite |
| ROBOT `report` | **0 ERROR.** WARN/INFO counts rose by one `missing_definition` WARN, consistent with the existing pattern for every property in this module (advisory, not new practice) |
| `generate_docs.py` | 5/5 clean |
| `mkdocs build` | not run this session |

### Next steps

1. Team discussion on the four parked organisation-role names (shape: one property per role vs. one generic
   property + role annotation) — see the survey doc §3.1, §5.
2. Push this to PR #66 (or a follow-up PR, team's call) and update the extraction profile / `RES-A-13` to read
   the new field once merged.

---

## 2026-09-01 — Field-frequency survey analysed; two candidates proposed for the next pass

**Issue:** [RES-89](https://bhmlrnd.youtrack.cloud/issue/RES-89) · **PR:** [#66](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/66) · **Branch:** `res-89-aec-titleblock-tbox`

### What happened

Ahmed Zaalouk collected a field-frequency spreadsheet from four real BH projects (Barbican, DDC – Project W,
Whiteleys, Fulham Riverside) — the survey the 2026-08-13 entry below and the TTL footer both said was still
pending before `hasLegalOwner` and the `<40%-of-sheets` acceptance criterion could be applied with real
evidence, and the same survey Zaalouk referenced on PR #66 (2026-08-19) as needed before he could review the
organisation properties in detail. Analysed it against the shipped `tb:` terms, the Option 1 `dm:` reuse
decision, and the original 73-term brainstorm (Discussion #61 §11.1).

**No `.ttl` edited — this is a proposal document only**, matching how decision 1 (Option 1) was drafted: a plan
for team review before implementation, not a unilateral mint.

### Findings, written up in `docs/modularization/titleblock-field-survey-2026-09.md`

- **Nine field groups need no new term** — the survey corroborates that `dm:Project`, `dm:DrawingPackage`,
  `dcommon:Discipline`, the shipped `tb:` terms, and the Option 1 `dm:` reuse already cover the majority of what
  real title blocks print.
- **Two genuine gaps, both crossing multiple independent projects, neither in the original 73-term list:**
  a contractor/consultant organisation role (4/4 projects, under five different labels) and a secondary
  drawing-reference number distinct from `dm:drawingIdentifier` (3/4 projects — an EDMS/Aconex number, a
  design-team-internal number, or a sketch/site-advice reference).
- Recommended starting narrow — `tb:assertsContractor` and `tb:assertsCrossReferenceNumber` — rather than
  minting every DDC-specific role split or reference-number label as its own term, for the same reason
  `DocumentType` was withdrawn in review round 1.
- Several surveyed fields explicitly **not** proposed (Level, Drawer Number, GHB.DRG.No., and six near-noise
  fields), with the reason recorded so the spreadsheet does not need re-reading to rediscover why.

### Verification

Not applicable — no ontology or code changed. Cross-checked proposed terms against `src/aec_drawing_metadata.ttl`
(current property/class list) and Discussion #61's raw term table (`gh api graphql`) to confirm neither gap was
already considered and rejected.

### Next step

Team decision on the two open shape questions in the proposal (§5): one property per organisation role vs one
generic property with the role left to `extractionHint`; and one generic cross-reference-number property vs
named properties per issuing system. Once decided, implementation is a small, single-purpose PR against the
already-open PR #66 branch or a follow-up.

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
| Classes | `Organisation`, `DocumentType` (+ `DocumentTypeScheme` as a `skos:ConceptScheme`) |
| Object properties | `assertsMetadataFor`, `hasClient`, `hasLegalOwner`, `hasOriginator`, `hasDocumentType` |
| Datatype properties | `organisationName`, `supplementaryTitle`, `sheetNumber`, `numberOfSheets`, `planKey`, `dimensionUnits` |
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
5. **PR 1** — fill the two placeholder sections: `Organisation`, `SourceFile`, `BoundingBox` (if the proposal
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
