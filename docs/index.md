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

    Foundational, domain-neutral vocabulary for representing an inferred/extracted assertion together with its provenance and confidence. It exists so that a value read off a drawing (a title-block field, a detected symbol, ...) can be modelled as a first-class assertion carrying: which region asserted it, what produced it, from where, when, and with what confidence - independently of the value itself. Imported by the drawing modules (e.g. aec_drawing_metadata); aligned to W3C PROV-O for interoperability.

    Source: [`aec_provenance.ttl`](aec_provenance.ttl)

    [![OntoCanvas](https://raw.githubusercontent.com/alelom/OntoCanvas/main/OntoCanvas.png){ .ontocanvas-icon } Open in OntoCanvas](https://alelom.github.io/OntoCanvas/?onto=https://burohappoldmachinelearning.github.io/ADIRO/aec_provenance.html){ .md-button target=_blank }

-   ### [Aec Drawing Metadata](aec_drawing_metadata.html)

    Sheet/layout/document structure for AEC drawings.

    *Imports: aec_provenance*

    Source: [`aec_drawing_metadata.ttl`](aec_drawing_metadata.ttl)

    [![OntoCanvas](https://raw.githubusercontent.com/alelom/OntoCanvas/main/OntoCanvas.png){ .ontocanvas-icon } Open in OntoCanvas](https://alelom.github.io/OntoCanvas/?onto=https://burohappoldmachinelearning.github.io/ADIRO/aec_drawing_metadata.html){ .md-button target=_blank }

-   ### [Aec Common Symbols](aec_common_symbols.html)

    Cross-discipline layout content. Generic symbol classes like dimensions, reference symbols, grids, etc. (mostly reusable non-domain symbols). All symbols are subclasses of DrawingElement from the drawing metadata ontology.

    *Imports: aec_drawing_metadata*

    Source: [`aec_common_symbols.ttl`](aec_common_symbols.ttl)

    [![OntoCanvas](https://raw.githubusercontent.com/alelom/OntoCanvas/main/OntoCanvas.png){ .ontocanvas-icon } Open in OntoCanvas](https://alelom.github.io/OntoCanvas/?onto=https://burohappoldmachinelearning.github.io/ADIRO/aec_common_symbols.html){ .md-button target=_blank }

-   ### [Aec Domain Common](aec_domain_common.html)

    Shared domain abstractions reused across multiple domain ontologies (e.g., facade+structural).

    *Imports: aec_common_symbols, aec_drawing_metadata*

    Source: [`aec_domain_common.ttl`](aec_domain_common.ttl)

    [![OntoCanvas](https://raw.githubusercontent.com/alelom/OntoCanvas/main/OntoCanvas.png){ .ontocanvas-icon } Open in OntoCanvas](https://alelom.github.io/OntoCanvas/?onto=https://burohappoldmachinelearning.github.io/ADIRO/aec_domain_common.html){ .md-button target=_blank }

-   ### [Aec Facade Domain](aec_facade_domain.html)

    Facade-specific concepts and symbols for facade engineering drawings.

    *Imports: aec_common_symbols, aec_domain_common, aec_drawing_metadata*

    Source: [`aec_facade_domain.ttl`](aec_facade_domain.ttl)

    [![OntoCanvas](https://raw.githubusercontent.com/alelom/OntoCanvas/main/OntoCanvas.png){ .ontocanvas-icon } Open in OntoCanvas](https://alelom.github.io/OntoCanvas/?onto=https://burohappoldmachinelearning.github.io/ADIRO/aec_facade_domain.html){ .md-button target=_blank }

-   ### [Aec Dano Alignment](aec_dano_alignment.html)

    OPTIONAL compatibility layer mapping ADIRO terms to the Drawing Analysis Ontology (DAnO, https://w3id.org/dano). Nothing in the ADIRO core imports this module and no ADIRO core module mentions DAnO, so a consumer who wants the DAnO crosswalk loads this file explicitly and everyone else never sees it. Every mapping uses ADIRO's own :closeMatch annotation property and carries no logical force: no rdfs:subPropertyOf alignment to a DAnO term is available, and the DAnO IRIs are not declared here or anywhere else in ADIRO. Kept separate from the core for lifecycle reasons - DAnO has no releases, and an unreleased third-party vocabulary should not force a version bump on a module downstream consumers pin. Full rationale and per-term verdicts: https://burohappoldmachinelearning.github.io/ADIRO/design-decisions/dano-comparison/

    *Imports: aec_provenance*

    Source: [`aec_dano_alignment.ttl`](aec_dano_alignment.ttl)

    [![OntoCanvas](https://raw.githubusercontent.com/alelom/OntoCanvas/main/OntoCanvas.png){ .ontocanvas-icon } Open in OntoCanvas](https://alelom.github.io/OntoCanvas/?onto=https://burohappoldmachinelearning.github.io/ADIRO/aec_dano_alignment.html){ .md-button target=_blank }

</div>
