# Data validation

ADIRO has two kinds of check, and they answer different questions.

- **The ontology** (the `.ttl` files in `src/`) says what exists: classes, properties and the axioms between them.
  It is written in OWL, which reasons under the *open-world assumption*: what is not stated is unknown, not false.
  Because of that, OWL cannot say "every drawing must have an author". A minimum cardinality would not report a drawing
  with no author; it would infer one that nobody extracted (see [#84, "Model detections, not idealised drawings"](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/84)).
- **The data validation files** (the `*.shacl.ttl` files in `data-validation/`) say what a complete, well-formed
  *dataset* must contain: the individuals an extraction pipeline produces for one drawing or a set of drawings. They are
  written in [SHACL](https://www.w3.org/TR/shacl/) (the *Shapes Constraint Language*), which checks data under
  closed-world rules: what is required and absent is reported.

The ontology is validated by `scripts/validate_ontology.py` and the reasoner. Data is validated by
`scripts/validate_data.py` against the files in `data-validation/`.

## What is in `data-validation/`

| File | Rules |
|---|---|
| `uc01-authorship.shacl.ttl` | A drawing has at least one recorded author (a warning); a drawing that records none is read as authored by its revisions' authors, so an author on a revision counts. Only the author is required: the checker and the approver are optional, and no rule reports their absence. It answers competency question CQ 4.4 of the UC-01 ORSD. |
| `assertions.shacl.ttl` | The rules for a field assertion ([#187](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/187), [#220](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/220)): it has at most one acceptance status (`Pending`, `Accepted` or `Rejected`) and at most one outcome (`Empty`, `Illegible`, `NotPrinted`, `NotFound` or `Failed`), so an assertion both accepted and rejected is reported before it is promoted, and a different result is recorded as a different assertion; it has a value or an outcome, never both; an accepted assertion has an `acceptedBy`; an assertion that supersedes another is about the same subject and the same field kind, and no assertion supersedes itself, directly or through others ([#221](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/221)). |
| `release/public-locations.shacl.ttl` | Run only for a public release (below): every address an ADIRO term records is on an allowlisted public host. |
| `configuration.shacl.ttl` | A configuration (`Configuration`) has exactly one content (`configurationContent`), as a string: it is identified by that content, so with none a step cannot be repeated and with two the configuration is ambiguous ([#237](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/237)). It supports competency question CQ 10.1 of the UC-01 ORSD. |
| `readings.shacl.ttl` | A text reading (`TextReading`, [#238](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/238)) reads exactly one region or page (`isReadingOf`), and has either one text (`readText`, a string with or without a language tag) or one outcome (`hasReadingOutcome`: `Empty`, `Illegible` or `Failed`), never both and never neither. It supports competency questions CQ 11.1 to CQ 11.3 of the UC-01 ORSD. |
| `frames.shacl.ttl` | The frames a model saw ([#239](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/239)): a frame has at most one `resolutionDpi`, a positive decimal, and covers at most one region (`coversRegion`, a `BoundingBox`); a kept image is an image of exactly one frame (`imageOf`); a pixel frame (unit `px`) with no resolution is a warning. It supports competency question CQ 10.4 of the UC-01 ORSD. |
| `file-source.shacl.ttl` | A file records where it was obtained from (`sourceLocation`), itself or through the files it was derived from (`prov:wasDerivedFrom`), as a warning ([#229](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/229)). It answers competency question CQ 9.5 of the UC-01 ORSD. |
| `uc03-composition.shacl.ttl` | The composition rules of the UC-03 reference expressions: an inline layout and sheet reference contains exactly one drawing identifier mention and at least one layout identifier mention; a reference symbol contains at most one drawing identifier mention; a drawing identifier mention has at most one accepted `denotesDrawingSheet` target. |

A file holds the rules of one use case or one topic, and is named `<topic>.shacl.ttl`. The suffix names the technology;
a `.ttl` in the folder without it is never run, and a test reports it.

## Severity

Each shape states `sh:severity`:

- **`sh:Violation`**: the graph is malformed. The UC-03 composition rules are violations.
- **`sh:Warning`**: the graph is incomplete or suspicious but usable, for example a drawing with no recorded author. A warning
  is reported and never fails a run.

## Run the checks

```bash
uv run --with pyshacl python scripts/validate_data.py path/to/data.ttl
```

The script reads the ontology modules as background, so a subclass counts as its superclass (a standalone sheet reference is
a drawing identifier mention). It exits with 1 when a result is a violation, and with 0 otherwise.

## Check data before a public release

Data kept inside an organisation may name its own storage: an internal file's origin is its internal address, and a public
file copied there has that copy as a `storageLocation`. Data that is published names only public addresses. The shapes in
`data-validation/release/` check that, and run only when an allowlist of public hosts is given:

```bash
uv run --with pyshacl python scripts/validate_data.py --public-hosts public-hosts.txt path/to/data.ttl
```

`public-hosts.txt` lists one host per line (`#` starts a comment); a host also allows its subdomains, so `loc.gov` allows
`tile.loc.gov`. Every `sourceLocation`, `sourcePage`, `storageLocation` and `acceptedUnder` on another host, or that is not a URL
with a plainly written host (a file path, or a backslash, a space or a line break in it), is a violation
([#229](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/229)). The release must drop or replace each one before
publishing; the check only reports them. Any `dvr:` term in the data itself is ignored, so the data cannot extend the allowlist. The list is supplied by
whoever releases the data and is not kept in this repository: it names public hosts only, so no internal host name has to be
written down anywhere.

The check covers the addresses ADIRO's terms record, not everything in a dataset. ADIRO publishes only its ontology; the data
is published by whoever produces it, and its publication step owns the rest:

- it mints the IRIs of its individuals so that they are not storage addresses (a `urn:` or a public namespace), because an IRI
  built from an internal path would publish that path;
- it checks the other literals and files it publishes (a manifest, a README) itself.

## Add a rule

1. Put the shape in the file of its use case or topic, or in a new `<topic>.shacl.ttl`. Give it a `sh:message` that says what is
   wrong in plain words, and an explicit `sh:severity`.
2. Add tests to `tests/test_data_validation.py`: a graph that conforms and one that breaks the rule, so the rule is shown to
   accept and to reject.
3. Say in the shape file's header, or in the use case's ORSD, which competency question or requirement the rule serves. A rule
   that no use case needs is not added.
4. Update this page if the file is new.

The tests also check that every ADIRO term a shape names is declared by the ontology, so a renamed term cannot leave a shape
that silently matches nothing.

## Versioning and publication

The shapes and the UC-01 competency queries are released together as **the checks**, an artefact with its own version
([#240](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/240)). They are not an ontology module: a shape checks data
against several modules at once, so it cannot follow one module's version. A system that writes ADIRO data and tests it against
the checks pins one version of them, so a later change to a shape or a query never silently changes what its tests accept.

**What a release holds.** Each release is served under `https://w3id.org/adiro/checks/<version>/`:

| Path | What |
|---|---|
| `manifest.json` | The version, every file below, and the version of each module in `src/` when the checks were released (the versions they were tested with). |
| `shapes/<topic>.shacl.ttl` | Every shape file of `data-validation/`, as in the repository. |
| `shapes/release/<topic>.shacl.ttl` | The shapes that run only for a public release. |
| `queries/uc01/<name>.rq` | Each competency query recorded in the UC-01 ORSD (`cq-10-1.rq`, `promotion.rq`, …), as written there. |

Point at a file, such as `https://w3id.org/adiro/checks/1.0.0/manifest.json`, never at the bare version address. The queries are
written once, in the ORSD: the tests read them there, and `scripts/export_checks.py` copies each block whose first comment line
names it (`# CQ 10.1: …`, `# Promotion: …`) into its own file, and a test runs each of them. A SPARQL block with no such line is
an illustration and is not released: in the UC-01 ORSD, only CQ-I 1, which needs a reasoner.

**What a version number means.** The checks follow SemVer, read from the point of view of the data being checked:

- **MAJOR**: a dataset that passed may now fail, or a query may answer differently: a rule tightened or added at `sh:Violation`, a
  query changed or removed, a file renamed or removed.
- **MINOR**: nothing that passed fails: a rule loosened, a new query, a new rule at `sh:Warning`, a new public-release rule.
- **PATCH**: a message, a comment or the wording of a file, with the same results.

Record each change under `[Unreleased]` in `changelogs/checks.md`, in the pull request that makes it. Releasing is a separate step,
described in [Releasing the checks](versioning/release-process.md#releasing-the-checks). Between releases the files in the repository
are the current state, and a pinned release does not change.
