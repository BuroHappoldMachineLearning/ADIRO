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

The files are not ontology modules: they have no version of their own and do not go through the release process. A shape follows
the module it checks, and a change that makes a previously valid dataset invalid is recorded in that module's changelog. The
folder is not part of the published site; it is in the repository.
