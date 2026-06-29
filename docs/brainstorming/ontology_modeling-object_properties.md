# Ontology modeling notes

## Core conclusion
In ontologies, it is usually better to use semantically specific object properties such as `hasGeometry`, `hasCrossSection`, and `hasMaterial` rather than collapsing everything into a single generic relation such as `hasProperty`.[cite:7][cite:13]

## Why specific properties are preferred
- In OWL/RDF, the predicate is part of the meaning, so different relations should usually be named explicitly rather than treated as interchangeable links.[cite:7][cite:13]
- Specific properties support domain and range constraints, which improves validation and allows useful type inferences.[cite:7][cite:10]
- They also enable property hierarchies, so detailed properties can roll up into more general ones through subproperty axioms.[cite:10]
- Many class definitions and restrictions depend on named properties, for example `hasMaterial some Concrete` or `hasCrossSection only IBeamSection`.[cite:5][cite:7]
- Queries are clearer and more maintainable when the relation itself tells the reader what kind of connection is being asserted.[cite:9]

## Why a single `hasProperty` is usually too weak
A generic relation such as `hasProperty` hides distinctions between geometry, material, and cross-section, so the graph becomes less informative and reasoning becomes weaker.[cite:9][cite:13]

Using only one generic predicate often pushes meaning into extra nodes, metamodeling patterns, or reified structures, which increases complexity and tends to be less natural for standard ontology engineering.[cite:7][cite:10]

## Practical compromise
A useful compromise is to define a small set of generic, high-level properties and then specialize them with subproperties.[cite:10][cite:12]

For example:
- `hasProperty`
- `hasPhysicalProperty` subproperty of `hasProperty`
- `hasGeometry` subproperty of `hasPhysicalProperty`
- `hasCrossSection` subproperty of `hasPhysicalProperty`
- `hasMaterial` subproperty of `hasProperty` or `hasConstituent`, depending on the intended semantics.[cite:10][cite:12]

## Design takeaway
The goal is not to maximize the number of predicates or to minimize them aggressively. The goal is to choose relations that are semantically clear, support the competency questions, and still fit into an intelligible hierarchy of reusable high-level properties.[cite:9][cite:10][cite:12]
