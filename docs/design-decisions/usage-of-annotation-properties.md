
## Use of annotation properties for pipeline-specific workflows

OWL annotation properties can be used to attach metadata to classes/relationships without affecting logical reasoning. 

We use custom annotation properties for application-specific behaviour or pipeline-specific workflows.

Some examples:

- [**`labellableRoot`**](https://github.com/BuroHappoldMachineLearning/ADIRO/blob/8b16ca55eacdfa8d991d0f22e14e90d0071dc83f/src/aec_drawing_metadata.ttl#L40): A boolean we use to mark which classes can serve as labels in annotation pipelines. These classes can be surfaced in an annotation software as concepts that can be labelled by human annotators.
- [**`isCVATProperty`**](https://github.com/BuroHappoldMachineLearning/ADIRO/blob/8b16ca55eacdfa8d991d0f22e14e90d0071dc83f/src/aec_drawing_metadata.ttl#L35) used to alter the display of a certain element in the annotation software that we use (CVAT).


Other annotation properties (e.g. `rdfs:label`, `rdfs:comment`) follow standard OWL usage.

## `rdfs:comment` is ADIRO's definition vocabulary

Every ADIRO term carries its human-readable definition in **`rdfs:comment`**. ADIRO deliberately does **not**
use `IAO:0000115`, the OBO Foundry definition annotation that ROBOT's `report` command looks for in its
built-in `missing_definition` rule. That rule is therefore set to `INFO` in
[`config/robot_report_profile.txt`](https://github.com/BuroHappoldMachineLearning/ADIRO/blob/main/config/robot_report_profile.txt)
— it is measuring conformance to a convention ADIRO has not adopted, and left at `WARN` it fired on every
term in the suite.

**Why not `IAO:0000115`:**

- **The published documentation would lose every description.** pyLODE, which generates the ontology
  reference pages, builds a description by normalising from exactly four properties — `dc:description`,
  `rdfs:comment`, `skos:definition` and `sdo:description`. `IAO:0000115` is not among them and IAO is not
  referenced anywhere in pyLODE, so moving the text there would blank the descriptions on the site.
- **The conversion is editorial, not mechanical.** An IAO definition is the definition alone; a good number
  of ADIRO's comments deliberately carry the definition *plus* the design rationale, which would have to be
  split by hand.
- **It buys conformance with tooling ADIRO does not use**, at the cost of an external vocabulary in every
  core module — see [External ontology imports](external-ontology-imports.md) for the test a core-module
  reference has to pass.

The peer ontology [DAnO](dano-comparison.md) makes the same choice: `rdfs:label` plus `rdfs:comment` on
essentially every term, no `IAO:0000115` and no `skos:definition`.

**What replaces the ROBOT rule.** `scripts/validate_ontology.py` checks that every term in an ADIRO namespace
carries an `rdfs:comment` (`skos:definition` and `dcterms:description` are accepted too, since pyLODE renders
those as well). Terms from other namespaces are exempt by design: an external term declared as a local stub is
a name, not a definition — the definition lives at the source, which is what its `rdfs:isDefinedBy` points at.
The check is advisory while the existing backlog is cleared ([#87](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/87)); set `ENFORCE_DESCRIPTIONS=1`
to promote it to a blocking error, and `LIST_UNDESCRIBED=1` to list every term it finds.

**If the definition/commentary distinction is ever wanted**, the route is `skos:definition` for the definition
alongside `rdfs:comment` for the note — pyLODE renders it, and ADIRO already uses SKOS throughout, so it adds
no new dependency.
