# Introduction

![ADIRO](img/adiro_banner.png){ .adiro-banner }

ADIRO (*AEC Drawing Information Representation Ontologies*) is a set of ontologies for AEC (*Architecture, Engineering, and Construction*) drawing representation, designed to support machine learning tasks, in particular information extraction workflows.

The ontologies include concepts for drawing metadata, common symbols, domain-common symbols, and domain-specific symbols. They can be used to represent the information in AEC drawings, to make them machine-readable, and to support the creation of graph databases and knowledge graphs.

[:fontawesome-brands-github: View on GitHub](https://github.com/BuroHappoldMachineLearning/ADIRO){ .md-button }

## Documentation

<div class="grid cards" markdown>

-   :material-file-document-check-outline: __Ontology Requirements (ORSD)__

    Ontology Requirements Specification Document: purpose, scope, intended users and uses, and the functional/non-functional requirements.

    [:octicons-arrow-right-24: ORSD](specification/ORSD_v1.2.md)

-   :material-clipboard-list-outline: __Use Cases__

    Use case catalogue (UC-01 through UC-07), prioritization matrix, and current ORSD status across all use cases.

    [:octicons-arrow-right-24: Use Cases](specification/use-cases/README.md)

</div>

## Available Ontologies

<div class="grid cards" markdown>

-   ### [Aec Provenance](aec_provenance.html)

    Foundational, domain-neutral module for provenance. It lets any value inferred from a drawing be recorded as an assertion that carries its own source, confidence, and how it was produced, aligned to W3C PROV-O. The drawing modules import it.

    Source: [`aec_provenance.ttl`](aec_provenance.ttl)

    [![OntoCanvas](https://raw.githubusercontent.com/alelom/OntoCanvas/main/OntoCanvas.png){ .ontocanvas-icon } Open in OntoCanvas](https://alelom.github.io/OntoCanvas/?onto=https://w3id.org/adiro/aec_provenance.html){ .md-button target=_blank }

-   ### [Aec Geometry](aec_geometry.html)

    Foundational, domain-neutral module for geometry. It records where something sits on a drawing page as a bounding box, read against an explicit coordinate frame. Each box carries its own provenance and confidence. It reuses GeoSPARQL, is imported by the drawing modules, and is shared across use cases.

    *Imports: aec_provenance*

    Source: [`aec_geometry.ttl`](aec_geometry.ttl)

    [![OntoCanvas](https://raw.githubusercontent.com/alelom/OntoCanvas/main/OntoCanvas.png){ .ontocanvas-icon } Open in OntoCanvas](https://alelom.github.io/OntoCanvas/?onto=https://w3id.org/adiro/aec_geometry.html){ .md-button target=_blank }

-   ### [Aec Drawing Metadata](aec_drawing_metadata.html)

    The core drawing vocabulary. It describes the structure of a drawing sheet: its layouts, title block, revisions, and the fields read from them. It imports the provenance and geometry modules, and the discipline modules build on it.

    *Imports: aec_geometry, aec_provenance*

    Source: [`aec_drawing_metadata.ttl`](aec_drawing_metadata.ttl)

    [![OntoCanvas](https://raw.githubusercontent.com/alelom/OntoCanvas/main/OntoCanvas.png){ .ontocanvas-icon } Open in OntoCanvas](https://alelom.github.io/OntoCanvas/?onto=https://w3id.org/adiro/aec_drawing_metadata.html){ .md-button target=_blank }

-   ### [Aec Common Symbols](aec_common_symbols.html)

    Reusable symbols that appear across disciplines, such as dimensions, grids, levels, and reference symbols. Every symbol is a kind of drawing element from the drawing-metadata module. The discipline modules build on these shared symbols.

    *Imports: aec_drawing_metadata*

    Source: [`aec_common_symbols.ttl`](aec_common_symbols.ttl)

    [![OntoCanvas](https://raw.githubusercontent.com/alelom/OntoCanvas/main/OntoCanvas.png){ .ontocanvas-icon } Open in OntoCanvas](https://alelom.github.io/OntoCanvas/?onto=https://w3id.org/adiro/aec_common_symbols.html){ .md-button target=_blank }

-   ### [Aec Domain Common](aec_domain_common.html)

    Concepts shared by several engineering domains. It sits between the common symbols and the discipline-specific modules, holding abstractions that more than one domain reuses, so they are defined once.

    *Imports: aec_common_symbols, aec_drawing_metadata*

    Source: [`aec_domain_common.ttl`](aec_domain_common.ttl)

    [![OntoCanvas](https://raw.githubusercontent.com/alelom/OntoCanvas/main/OntoCanvas.png){ .ontocanvas-icon } Open in OntoCanvas](https://alelom.github.io/OntoCanvas/?onto=https://w3id.org/adiro/aec_domain_common.html){ .md-button target=_blank }

-   ### [Aec Facade Domain](aec_facade_domain.html)

    Facade-engineering concepts and symbols, such as curtain-wall systems and glazing units. It is a discipline-specific module at the end of the dependency chain, building on the shared drawing, symbol, and domain vocabularies.

    *Imports: aec_common_symbols, aec_domain_common, aec_drawing_metadata*

    Source: [`aec_facade_domain.ttl`](aec_facade_domain.ttl)

    [![OntoCanvas](https://raw.githubusercontent.com/alelom/OntoCanvas/main/OntoCanvas.png){ .ontocanvas-icon } Open in OntoCanvas](https://alelom.github.io/OntoCanvas/?onto=https://w3id.org/adiro/aec_facade_domain.html){ .md-button target=_blank }

</div>
