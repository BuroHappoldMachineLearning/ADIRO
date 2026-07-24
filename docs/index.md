# ADIRO Ontologies Documentation

ADIRO (*AEC Drawing Information Representation Ontologies*) is a set of ontologies for AEC (*Architecture, Engineering, and Construction*) drawing representation, designed to support machine learning tasks, in particular information extraction workflows.

The ontologies include concepts for drawing metadata, common symbols, domain-common symbols, and domain-specific symbols. They can be used to represent the information in AEC drawings, to make them machine-readable, and to support the creation of graph databases and knowledge graphs.

[:fontawesome-brands-github: View on GitHub](https://github.com/BuroHappoldMachineLearning/ADIRO){ .md-button }

## Documentation

<div class="grid cards" markdown>

-   :material-clipboard-list-outline: __Use Cases__

    Use case catalogue (UC-01 through UC-07), prioritization matrix, and current ORSD status across all use cases.

    [:octicons-arrow-right-24: Use Cases](uc-orsd/README.md)

-   :material-file-document-check-outline: __Ontology Requirements (ORSD)__

    Ontology Requirements Specification Document: purpose, scope, intended users and uses, and the functional/non-functional requirements.

    [:octicons-arrow-right-24: ORSD](ORSD_v1.md)

</div>

## Available Ontologies

<div class="grid cards" markdown>

-   ### [Aec Drawing Metadata](aec_drawing_metadata.html)

    Sheet/layout/document structure for AEC drawings.

    Source: [`aec_drawing_metadata.ttl`](aec_drawing_metadata.ttl)

    [:material-graph-outline: Open in OntoCanvas](https://alelom.github.io/OntoCanvas/?onto=https://burohappoldmachinelearning.github.io/ADIRO/aec_drawing_metadata.html){ .md-button target=_blank }

-   ### [Aec Common Symbols](aec_common_symbols.html)

    Cross-discipline layout content. Generic symbol classes like dimensions, reference symbols, grids, etc. (mostly reusable non-domain symbols). All symbols are subclasses of DrawingElement from the drawing metadata ontology.

    *Imports: aec_drawing_metadata*

    Source: [`aec_common_symbols.ttl`](aec_common_symbols.ttl)

    [:material-graph-outline: Open in OntoCanvas](https://alelom.github.io/OntoCanvas/?onto=https://burohappoldmachinelearning.github.io/ADIRO/aec_common_symbols.html){ .md-button target=_blank }

-   ### [Aec Domain Common](aec_domain_common.html)

    Shared domain abstractions reused across multiple domain ontologies (e.g., facade+structural).

    *Imports: aec_common_symbols, aec_drawing_metadata*

    Source: [`aec_domain_common.ttl`](aec_domain_common.ttl)

    [:material-graph-outline: Open in OntoCanvas](https://alelom.github.io/OntoCanvas/?onto=https://burohappoldmachinelearning.github.io/ADIRO/aec_domain_common.html){ .md-button target=_blank }

-   ### [Aec Facade Domain](aec_facade_domain.html)

    Facade-specific concepts and symbols for facade engineering drawings.

    *Imports: aec_common_symbols, aec_domain_common, aec_drawing_metadata*

    Source: [`aec_facade_domain.ttl`](aec_facade_domain.ttl)

    [:material-graph-outline: Open in OntoCanvas](https://alelom.github.io/OntoCanvas/?onto=https://burohappoldmachinelearning.github.io/ADIRO/aec_facade_domain.html){ .md-button target=_blank }

</div>

!!! note ""
    Ontology reference pages are generated automatically by [pyLODE](https://github.com/RDFLib/pyLODE).
