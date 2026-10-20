# Design decisions

The decisions on this page apply to the whole ADIRO suite. A decision that belongs to one use case sits with that
use case, under its **Design notes**:

- [UC-01 design notes](../use-cases/UC-01/design-notes/titleblock-vocabulary-review.md): the title-block vocabulary and its field survey.
- [UC-03 design notes](../use-cases/UC-03/design-notes/uc03-three-layer-model.md): the semantic, geometry and provenance layers, the reference expressions and the provenance profile.

## Suite-wide decisions

- [The file a drawing is stored in](file-and-page-metadata.md): the file, the page and the coordinate frame kept apart, and their alignment to ISO 21597-1 and other vocabularies (decided, not yet in the ontology).
- [External ontology imports](external-ontology-imports.md): how ADIRO brings in terms from external vocabularies, and when it does not.
- [DAnO comparison](dano-comparison.md): where ADIRO overlaps DAnO, and why ADIRO mints its own terms.
- [Croissant, PROV-O and DAnO](croissant-comparison.md): what each does, and where Croissant fits ADIRO.
- [Bounding boxes, coordinate frames and provenance](geometry-coordinate-frames.md): a worked example that locates a title block.
- [Usage of annotation properties](usage-of-annotation-properties.md): annotation properties for pipeline-specific workflows.
- [Usage of restrictions for cardinality](usage-of-restrictions-for-cardinality.md): how class-level containment is expressed.
- [Ontology modularization](modularization/index.md): the module layout and its import hierarchy.
