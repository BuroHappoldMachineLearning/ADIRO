
## Use of annotation properties for pipeline-specific workflows

OWL annotation properties can be used to attach metadata to classes/relationships without affecting logical reasoning. 

We use custom annotation properties for application-specific behaviour or pipeline-specific workflows.

Some examples:

- **`isComputerVisionLabel`**: A boolean we use to mark which classes can serve as labels in annotation pipelines. These classes can be surfaced in an annotation software as concepts that can be labelled by human annotators. It also marks the datatype properties whose printed value is a text field an annotator boxes, such as a layout's title or a sheet's scale ([#162](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/162)); the box belongs to the class whose `owl:onProperty` restriction names the property (see [Usage of OWL restrictions for cardinality](usage-of-restrictions-for-cardinality.md)). It replaces `labellableRoot`, which was removed ([#141](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/141)).
  - **Which datatype properties are marked** ([#162](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/162)). A datatype property is marked when a use case needs the printed field located on the drawing, not only its value read. Today that is six fields, marked for UC-03: `drawingIdentifier`, `drawingTitle`, `drawingScale`, `layoutIdentifier`, `layoutTitle` and `layoutScale`. A property whose value a use case only reads, such as `sheetSize`, the revision fields and the dates in UC-01, is not marked. It can be marked when a use case needs to locate it, for example to trace an extracted value back to where it is printed. The decision is taken per use case and not from the kind of field, so a new mark names the use case that needs it, as these name UC-03.
- **`isComputerVisionOptionalLabel`**: a presentation hint: computer-vision annotation tooling presents the class apart from the required labels. It is independent of `isComputerVisionLabel` (a discipline can be an optional label picked as an attribute without being drawn as a label). Example: once a layout is identified, an annotator may qualify it as an architectural layout (an architectural plan) or an engineering layout (engineering detail) by picking the discipline; the discipline is an optional label for that choice, not a shape drawn on the sheet. Both are named for the application they serve; another application, such as tagging report documents, gets its own pair. It replaces an earlier property whose name carried a tool name, which was removed ([#141](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/141)).


Other annotation properties (e.g. `rdfs:label`, `rdfs:comment`) follow standard OWL usage.

## `skos:definition` is ADIRO's definition vocabulary, `rdfs:comment` its commentary

Every ADIRO term carries its human-readable definition in **`skos:definition`** and any commentary in **`rdfs:comment`**:

| Property | Holds |
|---|---|
| `skos:definition` | What the term is, in one to three sentences, in ADIRO's own words, tagged `@en`. One per term. |
| `rdfs:comment` | Commentary: design rationale, examples, the standard the term corresponds to and how it differs, links to issues and design notes. Optional. |

This separates the definition, which a tool or a reader selects, from the commentary, which a definition-only string cannot
carry without the two blurring. It was decided in
[Discussion #265](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/265) and carried out by
[#273](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/273) one module at a time: a term not yet split carries its
definition in `rdfs:comment`, and the validator reports it. The `owl:Ontology` header keeps its `rdfs:comment`, which is the
module's introduction and not a term's definition. *(Amended: the definition was an `rdfs:comment` until [#273](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/273).)*

ADIRO deliberately does **not**
use `IAO:0000115`, the OBO Foundry definition annotation that ROBOT's `report` command looks for in its
built-in `missing_definition` rule. That rule is therefore **not listed** in
[`config/robot_report_profile.txt`](https://github.com/BuroHappoldMachineLearning/ADIRO/blob/main/config/robot_report_profile.txt),
so ROBOT does not run it: a profile lists the checks that run, and omitting one disables it. Downgrading it to
`INFO` was tried first and rejected — the rows stayed, still naming `IAO:0000115` on every term, and a check
whose output you have to learn to ignore is worse than no check. ADIRO's own description check replaces it.
(The profile format is strict TSV and does not accept comment lines, so this note cannot live in the file
itself.)

**Why not `IAO:0000115`:**

- **The published documentation would lose every description.** pyLODE, which generates the ontology
  reference pages, builds a description by normalising from exactly four properties — `dc:description`,
  `rdfs:comment`, `skos:definition` and `sdo:description`. `IAO:0000115` is not among them and IAO is not
  referenced anywhere in pyLODE, so moving the text there would blank the descriptions on the site. `skos:definition`
  is among them. pyLODE lists it and `rdfs:comment` together in one *Description* entry, so the documentation generator (`scripts/pylode_metadata.py`) gives them their own *Definition* and *Comment* rows.
- **The conversion is editorial, not mechanical.** An IAO definition is the definition alone; a good number
  of ADIRO's comments deliberately carry the definition *plus* the design rationale, which would have to be
  split by hand, as the move to `skos:definition` is.
- **It buys conformance with tooling ADIRO does not use**, at the cost of an external vocabulary in every
  core module — see [External ontology imports](external-ontology-imports.md) for the test a core-module
  reference has to pass.

The peer ontology [DAnO](dano-comparison.md) avoids `IAO:0000115` too: `rdfs:label` plus `rdfs:comment` on
essentially every term, and no `skos:definition`.

**What replaces the ROBOT rule.** `scripts/validate_ontology.py` checks that every term in an ADIRO namespace
carries a description: a `skos:definition`, or, until its module is split, an `rdfs:comment` (`dcterms:description`
is accepted too, since pyLODE renders it as well). A second check lists the terms that have an `rdfs:comment` and no
`skos:definition`, advisory until the last module is split (`ENFORCE_DEFINITIONS=1` makes it blocking). Terms from other namespaces are exempt by design: an external term declared as a local stub is
a name, not a definition — the definition lives at the source, which is what its `rdfs:isDefinedBy` points at.
The check is advisory while the existing backlog is cleared ([#87](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/87)); set `ENFORCE_DESCRIPTIONS=1`
to promote it to a blocking error, and `LIST_UNDESCRIBED=1` to list every term it finds.

