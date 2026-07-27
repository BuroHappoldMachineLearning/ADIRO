# ADIRO Ontology Requirements Specification — v1.1

**Author:** ADIRO project team
**Version:** 1.1 (July 2026)

---

*Ontology Requirements Specification Document*

## 1. Purpose

The purpose of ADIRO is to establish a standardized semantic backbone for the comprehensive interpretation and management of technical drawing data to facilitate the creation of intelligent building models. This framework is designed to model complex spatial and logical relationships both within individual drawings and across multiple sheets or documents to enable a unified understanding of building projects that are often distributed across multiple technical documentation. In addition, ADIRO provides a structured schema for the integration of high-granularity machine learning extraction results, in which the ontology supports advanced post-processing, consistency checks, and error detection through logical and geometric reasoning. A key goal of ADIRO is to capture and represent the way engineers interpret technical content. It models the reasoning process and cognitive cues engineers use to understand drawings, combining contextual information with logical rules to build a complete semantic understanding of the data. By connecting analysed drawing information with established design and engineering knowledge, the ontology acts as a semantic bridge that improves interoperability and supports more efficient Plan-to-BIM reconstruction workflows.

---

## 2. Scope

The scope provides a phased, multi-disciplinary framework for representing AEC drawing concepts. ADIRO's scope begins with metadata and layout, then extends to common AEC symbols, and concludes with domain-specific and discipline-specific symbols, specifically targeting Facade and MEP extensions.

---

## 3. Implementation Language

The ontology is implemented using RDF and OWL to establish a standardized and interoperable information schema. In addition, it is specifically engineered to maintain technical compatibility with the SPARQL, SHACL, SWRL, and DL reasoning technology stacks to enable data validation and post-processing use cases.

---

## 4. Intended End-Users

| # | User | Description |
|---|------|-------------|
| User 1 | **AEC Engineer** | Interprets specialized systems, materials, and source information from technical AEC drawings for a variety of purposes, like: extracting required information in order to design new components; identifying logical inconsistencies or design gaps; verify compliance against legal Codes. |
| User 2 | **Designer** | Inspects spatial and logical drawing relationships to compare design intent across multiple documents and traces how specific building elements are represented across different sheets. |
| User 3 | **ML/AI Practitioner** | Employs ontology-grounded representations to facilitate structured information extraction, post-processing, explainable AI (XAI), and human-in-the-loop validation workflows. |
| User 4 | **Downstream Application Developer** | Reuses standardized ontology concepts to build knowledge graphs, retrieval systems, and reporting pipelines that support interoperability across the AECO industry. |

---

## 5. Intended Uses

| # | Use Case | Description |
|---|----------|-------------|
| Use 1 | **Automated content retrieval and regulatory reporting** | Aggregating title block metadata for drawing searches and summarizing cross-document content for compliance requirements, such as the Building Safety Act. |
| Use 2 | **Design validation and data integrity checks** | Detect spatial gaps in facade performance lines, identify discrepancies between different drawing versions (e.g., design intent vs. contractor submissions) through comparative analysis, and automatically resolve extraction conflicts using logical rules, while flagging high-uncertainty results for human-in-the-loop verification and manual correction when autonomous rectification is insufficient. |
| Use 3 | **Learning-based reasoning** | Perform context-aware label refinement, where ontological knowledge is used to validate and correct uncertain machine-learning predictions based on their spatial and semantic context. |
| Use 4 | **Inter-drawing connectivity** | Enable navigation across sheets and drawing sets by automatically matching and linking reference symbols, including detail, section, and elevation markers. |
| Use 5 | **Spatial reasoning and similarity analysis** | Identify repeated occurrences of building elements and quantify components based on geometric attributes such as orientation or location. |

> **Cross-reference note (not part of the LOT template — reviewer aid only):** This note maps the "Use N" labels above to the canonical, stable `UC-0x` IDs used in the per-use-case ORSDs (`docs/uc-orsd/`), for reviewers checking alignment between this umbrella document and the per-UC ORSDs. It is scaffolding, not a permanent fixture — it can be removed once use-case numbering has stabilised, in favour of `docs/uc-orsd/README.md`, which maintains its own authoritative "Related documents" index.
>
> | ORSD v1 label | Corresponding UC ORSD |
> |---|---|
> | Use 1 | UC-01 + UC-06 — see [Related documents](uc-orsd/README.md#5-related-documents) |
> | Use 2 | *No dedicated UC ORSD yet* |
> | Use 3 | *No dedicated UC ORSD yet* |
> | Use 4 | UC-03 — see [Related documents](uc-orsd/README.md#5-related-documents) |
> | Use 5 | UC-07 — see [Related documents](uc-orsd/README.md#5-related-documents) |

---

## 6. Ontology Requirements

### a. Non-Functional Requirements

| ID | Requirement | Description |
|----|-------------|-------------|
| NFR 1 | **Concise terminology** | The ontology shall use precise, domain-appropriate terms aligned with international standards and established engineering vocabulary. |
| NFR 2 | **Consistency** | The model shall avoid contradictory assertions and redundant modelling to support the logical interpretation of classes and properties. |
| NFR 3 | **Extendability** | The ontology shall be built to accommodate new AEC disciplines (e.g., Facade, MEP) without restructuring the core model, primarily through the reuse of established ontologies like BOT, ifcOWL, and GeoSPARQL. ( Extendability is achieved today through the modular internal package structure (e.g. aec_domain_common, aec_facade_domain). Reuse of established external ontologies is a target for future alignment and currently ADIRO doesn't import them. ) |
| NFR 4 | **Reliability** | The ontology and its metadata shall be structured to ensure sustained availability and traceability for long-term use in the AECO industry. |
| NFR 5 | **FAIR principles** | The ontology shall be developed, documented, and published to ensure it is Findable, Accessible, Interoperable, and Reusable. |
| NFR 6 | **Modularity and Scalability** | The ontology shall support a modular framework where different aspects of a drawing can be processed by independent extraction services and subsequently aggregated without loss of semantic integrity or performance degradation when scaled to multi-document collections. |

---

### b. Functional Requirements: Competency Question Groups (CQGs)

#### CQG 1. Data Extraction and Organisation

- **CQ 1.1:** Which types of descriptive elements (e.g., project name, sheet number) have been extracted from the title block?
- **CQ 1.2:** What is the origin drawing of a given extracted building element or wall?
- **CQ 1.3:** Does the extracted geometry for the walls include orientation attributes (e.g., North/East) for measurement?

#### CQG 2. Design and Data Validation

- **CQ 2.1:** Does the extracted knowledge graph for a facade system lack any mandatory functional sub-components required to form a semantically complete assembly?
- **CQ 2.2:** Which elements share the same taxonomy class or properties to be identified as "similar" for design checks?
- **CQ 2.3:** Can containment, cardinality, co-occurrence, or material inconsistencies be detected from the ontology model?
- **CQ 2.4:** For a given set of detected errors, which are classified as auto-resolvable (e.g., duplicate deletion) and which are classified as requiring human intervention?

#### CQG 3. Learning-Based Reasoning

- **CQ 3.1:** What label, confidence score, and geometry are recorded for a given model-prediction individual?
- **CQ 3.2:** 
For a given set of evaluation drawings, which predicted individuals match their corresponding ground-truth individuals in the ground-truth knowledge graphs, and which diverge?
- **CQ 3.3:** Which uncertain classifications are refined into confirmed classifications using their spatial and semantic context?
- **CQ 3.4:** What are the labels and descriptions of the semantic or spatial rules triggered to produce a given validation outcome?

#### CQG 4. Intra- and Inter-Drawing Information Interrelation

- **CQ 4.1:** What drawings are connected to a given drawing through reference symbols?
- **CQ 4.2:** What relationships exist among elements inside a drawing or across drawings?
- **CQ 4.3:** 
What is the complete set of drawings reachable from a given drawing through reference-symbol links, in both outgoing and incoming directions?
- **CQ 4.4:** 
 Which extraction-service results have been aggregated into a drawing's unified representation, and from which service did each originate?

#### CQG 5. Discipline and Data Interoperability

- **CQ 5.1:** Which DrawingElement types are consistently identified across different engineering drawing sets?
- **CQ 5.2:** Which external ontology classes are linked to a given metadata:DrawingElement for cross-domain interoperability?  *(the linking property itself — working name `depicts` — is not yet defined in the ontology, so lets to treat it as a proposed pending Open Issue OI-1)*
