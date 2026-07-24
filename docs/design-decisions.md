# Design decisions

## Why OWL restrictions for contains

`contains` is an **object property**: it relates individuals to individuals. In OWL, class axioms describe constraints on instances. To express "Class A can contain Class B" (0 or more) at the class level, we use an **OWL restriction** with qualified cardinality:

```turtle
:Layout rdfs:subClassOf [ rdf:type owl:Restriction ;
                         owl:onProperty :contains ;
                         owl:minQualifiedCardinality 0 ;
                         owl:onClass :Annotation
                       ] .
```

Min cardinality 0 means "can contain" (optional). Use min ≥ 1 for "must contain".

## Annotation properties

OWL annotation properties attach metadata to classes without affecting logical reasoning. We use custom annotation properties for application-specific behaviour.

**Example: labellableRoot** — A boolean we use to mark which classes can serve as labels in diagrams. When `true`, the class is shown as a solid contour (labellable); when `false`, as a dashed contour (structural/category node). This drives filtering and styling in the visualizer and editor.

Other annotation properties (e.g. `rdfs:label`, `rdfs:comment`) follow standard OWL usage.

## Relationship examples

- **rdfs:subClassOf** — Taxonomy: e.g. `CurtainWallSystem` subClassOf `FacadeSystem`
- **contains** — Containment: e.g. a layout can contain drawing elements (via OWL restrictions)
- **hasFunction**, **hasMaterial** — Domain-specific: e.g. a facade component has a function or material
