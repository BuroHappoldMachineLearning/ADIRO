# Introduction

![ADIRO](img/adiro_banner.png){ .adiro-banner }

[![DOI](https://zenodo.org/badge/1165500639.svg)](https://doi.org/10.5281/zenodo.24319134)

ADIRO (*AEC Drawing Information Representation Ontologies*) is a set of ontologies for AEC (*Architecture, Engineering, and Construction*) drawing representation, designed to support machine learning tasks, in particular information extraction workflows.

The ontologies include concepts for drawing metadata, common symbols, domain-common symbols, and domain-specific symbols. They can be used to represent the information in AEC drawings, to make them machine-readable, and to support the creation of graph databases and knowledge graphs.

[:fontawesome-brands-github: View on GitHub](https://github.com/BuroHappoldMachineLearning/ADIRO){ .md-button }

## Documentation

<div class="grid cards" markdown>

-   :material-file-document-check-outline: __Ontology Requirements (ORSD)__

    Ontology Requirements Specification Document: purpose, scope, intended users and uses, and the functional/non-functional requirements.

    [:octicons-arrow-right-24: ORSD](specification/ORSD_v1.5.md)

-   :material-clipboard-list-outline: __Use Cases__

    Use case catalogue (UC-01 through UC-07), prioritization matrix, and current ORSD status across all use cases.

    [:octicons-arrow-right-24: Use Cases](specification/use-cases/README.md)

</div>

## Available Ontologies

<div class="grid cards" markdown>

-   ### [Adiro Provenance](adiro_provenance.html)

    Foundational, domain-neutral module for provenance. It lets any value inferred from a drawing be recorded as an assertion that carries its own source, confidence, and how it was produced, aligned to W3C PROV-O. The drawing modules import it.

    Source: [`adiro_provenance.ttl`](adiro_provenance.ttl)

    [![OntoCanvas](https://burohappoldmachinelearning.github.io/OntoCanvas/OntoCanvas.png){ .ontocanvas-icon } Open in OntoCanvas](https://burohappoldmachinelearning.github.io/OntoCanvas/?onto=https://w3id.org/adiro/adiro_provenance.html){ .md-button target=_blank }

-   ### [Adiro Geometry](adiro_geometry.html)

    Foundational, domain-neutral module for geometry. It records where something sits on a drawing page as a bounding box, read against an explicit coordinate frame. Each box carries its own provenance and confidence. It reuses GeoSPARQL, is imported by the drawing modules, and is shared across use cases.

    *Imports: adiro_provenance*

    Source: [`adiro_geometry.ttl`](adiro_geometry.ttl)

    [![OntoCanvas](https://burohappoldmachinelearning.github.io/OntoCanvas/OntoCanvas.png){ .ontocanvas-icon } Open in OntoCanvas](https://burohappoldmachinelearning.github.io/OntoCanvas/?onto=https://w3id.org/adiro/adiro_geometry.html){ .md-button target=_blank }

-   ### [Adiro Drawing Metadata](adiro_drawing_metadata.html)

    The core drawing vocabulary. It describes the structure of a drawing sheet: its layouts, title block, revisions, and the fields read from them. It imports the provenance module (which also holds the file, the page and the agents) and the geometry module (where a title block's region is located), and the discipline modules build on it.

    *Imports: adiro_geometry, adiro_provenance*

    Source: [`adiro_drawing_metadata.ttl`](adiro_drawing_metadata.ttl)

    [![OntoCanvas](https://burohappoldmachinelearning.github.io/OntoCanvas/OntoCanvas.png){ .ontocanvas-icon } Open in OntoCanvas](https://burohappoldmachinelearning.github.io/OntoCanvas/?onto=https://w3id.org/adiro/adiro_drawing_metadata.html){ .md-button target=_blank }

-   ### [Adiro Drawing Symbology](adiro_drawing_symbology.html)

    The symbols and marks a drawing uses, shared by every discipline: reusable symbols and text that appear across disciplines, such as dimensions, grids, levels and references to another layout or drawing: the graphical reference symbol, the inline and standalone reference expressions, and the occurrences of drawing and layout identifiers they are made of. Every one is a kind of drawing element from the drawing-metadata module. The discipline modules build on them.

    *Imports: adiro_drawing_metadata*

    Source: [`adiro_drawing_symbology.ttl`](adiro_drawing_symbology.ttl)

    [![OntoCanvas](https://burohappoldmachinelearning.github.io/OntoCanvas/OntoCanvas.png){ .ontocanvas-icon } Open in OntoCanvas](https://burohappoldmachinelearning.github.io/OntoCanvas/?onto=https://w3id.org/adiro/adiro_drawing_symbology.html){ .md-button target=_blank }

-   ### [Adiro Discipline Core](adiro_discipline_core.html)

    The vocabulary that several discipline modules share: materials, section shapes and properties, structural components and loads, and the discipline classes. It sits between the drawing symbology and the discipline-specific modules, holding abstractions that more than one discipline reuses, so they are defined once.

    *Imports: adiro_drawing_metadata*

    Source: [`adiro_discipline_core.ttl`](adiro_discipline_core.ttl)

    [![OntoCanvas](https://burohappoldmachinelearning.github.io/OntoCanvas/OntoCanvas.png){ .ontocanvas-icon } Open in OntoCanvas](https://burohappoldmachinelearning.github.io/OntoCanvas/?onto=https://w3id.org/adiro/adiro_discipline_core.html){ .md-button target=_blank }

-   ### [Adiro Facade Discipline](adiro_facade_discipline.html)

    Facade-engineering concepts and symbols, such as curtain-wall systems and glazing units. It is a discipline-specific module at the end of the dependency chain, building on the shared drawing, symbology, and discipline-core vocabularies.

    *Imports: adiro_discipline_core, adiro_drawing_metadata*

    Source: [`adiro_facade_discipline.ttl`](adiro_facade_discipline.ttl)

    [![OntoCanvas](https://burohappoldmachinelearning.github.io/OntoCanvas/OntoCanvas.png){ .ontocanvas-icon } Open in OntoCanvas](https://burohappoldmachinelearning.github.io/OntoCanvas/?onto=https://w3id.org/adiro/adiro_facade_discipline.html){ .md-button target=_blank }

</div>
