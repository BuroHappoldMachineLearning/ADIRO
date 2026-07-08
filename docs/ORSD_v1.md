# ADIRO Ontology Requirements Specification Draft

**Author:** ADIRO project team
**Date:** June 2026

---

## Ontology Requirements Specification Document

### 1. Purpose

The purpose of ADIRO is to establish a standardized semantic backbone for the comprehensive interpretation and management of technical drawing data to facilitate the creation of intelligent building models. This framework is designed to model complex spatial and logical relationships both within individual drawings and across multiple sheets or documents to enable a unified understanding of building projects that are often distributed across multiple technical documentation. In addition, ADIRO provides a structured schema for the integration of high-granularity machine learning extraction results, in which the ontology supports advanced post-processing, consistency checks, and error detection through logical and geometric reasoning. A key goal of ADIRO is to capture and represent the way engineers interpret technical content. It models the reasoning process and cognitive cues engineers use to understand drawings, combining contextual information with logical rules to build a complete semantic understanding of the data. By connecting analysed drawing information with established design and engineering knowledge, the ontology acts as a semantic bridge that improves interoperability and supports more efficient Plan-to-BIM reconstruction workflows.

---

### 2. Scope

The scope provides a phased, multi-disciplinary framework for representing AEC drawing concepts. ADIRO's scope begins with metadata and layout, then extends to common AEC symbols, and concludes with domain-specific and discipline-specific symbols, specifically targeting Facade and MEP extensions.

---

### 3. Implementation Language

The ontology is implemented using RDF and OWL to establish a standardized and interoperable information schema. In addition, it is specifically engineered to maintain technical compatibility with the SPARQL, SHACL, SWRL, and DL reasoning technology stacks to enable data validation and post-processing use cases.

---

### 4. Intended End-Users

| # | User | Description |
|---|------|-------------|
| User 1 | **Facade Engineer** | Interprets specialized facade systems, materials, and performance lines while identifying logical inconsistencies or design gaps within facade-related drawing content. |
| User 2 | **Designer** | Inspects spatial and logical drawing relationships to compare design intent across multiple documents and traces how specific building elements are represented across different sheets. |
| User 3 | **ML/AI Practitioner** | Employs ontology-grounded representations to facilitate structured information extraction, post-processing, explainable AI (XAI), and human-in-the-loop validation workflows. |
| User 4 | **Downstream Application Developer** | Reuses standardized ontology concepts to build knowledge graphs, retrieval systems, and reporting pipelines that support interoperability across the AECO industry. |

---

### 5. Intended Uses

| # | Use Case | Description |
|---|----------|-------------|
| Use 1 | **Automated content retrieval and regulatory reporting** | Aggregating title block metadata for drawing searches and summarizing cross-document content for compliance requirements, such as the Building Safety Act. |
| Use 2 | **Design validation and data integrity checks** | Detect spatial gaps in facade performance lines, identify discrepancies between different drawing versions (e.g., design intent vs. contractor submissions) through comparative analysis, and automatically resolve extraction conflicts using logical rules, while flagging high-uncertainty results for human-in-the-loop verification and manual correction when autonomous rectification is insufficient. |
| Use 3 | **Learning-based reasoning** | Perform context-aware label refinement, where ontological knowledge is used to validate and correct uncertain machine-learning predictions based on their spatial and semantic context. |
| Use 4 | **Inter-drawing connectivity** | Enable navigation across sheets and drawing sets by automatically matching and linking reference symbols, including detail, section, and elevation markers. |
| Use 5 | **Spatial reasoning and similarity analysis** | Identify repeated occurrences of building elements and quantify components based on geometric attributes such as orientation or location. |

---

## 6. Ontology Requirements

### a. Non-Functional Requirements

| ID | Requirement | Description |
|----|-------------|-------------|
| NFR 1 | **Concise terminology** | The ontology shall use precise, domain-appropriate terms aligned with international standards and established engineering vocabulary. |
| NFR 2 | **Consistency** | The model shall avoid contradictory assertions and redundant modelling to support the logical interpretation of classes and properties. |
| NFR 3 | **Extendability** | The ontology shall be built to accommodate new AEC disciplines (e.g., Facade, MEP) without restructuring the core model, primarily through the reuse of established ontologies like BOT, ifcOWL, and GeoSPARQL. |
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
- **CQ 2.4:** How does the system distinguish between errors it can resolve autonomously (e.g., duplicate deletion) and those requiring human intervention?

#### CQG 3. Learning-Based Reasoning

- **CQ 3.1:** How can model predictions be represented as ontology individuals with labels, confidence scores, and geometry?
- **CQ 3.2:** How can extracted predictions be compared against ground-truth knowledge graphs?
- **CQ 3.3:** Can the ontology help refine uncertain classifications using spatial and semantic context?
- **CQ 3.4:** What specific semantic or spatial rules were triggered to produce a given validation outcome, and how can this reasoning be made explicit for users?

#### CQG 4. Intra- and Inter-Drawing Information Interrelation

- **CQ 4.1:** What drawings are connected to a given drawing through reference symbols?
- **CQ 4.2:** What relationships exist among elements inside a drawing or across drawings?
- **CQ 4.3:** Can drawing relationships be represented in a way that supports navigation and GraphRAG-style retrieval?
- **CQ 4.4:** How can results from multiple extraction services be aggregated into a unified knowledge base?

#### CQG 5. Discipline and Data Interoperability

- **CQ 5.1:** Which DrawingElement types are consistently identified across different engineering drawing sets?
- **CQ 5.2:** Which external ontology classes are linked to a given DisplayElement through the `depicts` property to ensure cross-domain interoperability?
