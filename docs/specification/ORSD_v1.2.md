# ADIRO Ontology Requirements Specification — v1.2

**Author:** ADIRO project team
**Version:** 1.2 (September 2026) — see [Version history](#version-history)

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

> | ORSD v1 label | Corresponding UC ORSD |
> |---|---|
> | Use 1 | UC-01 + UC-06 — see [Related documents](use-cases/README.md#5-related-documents) |
> | Use 2 | *No dedicated UC ORSD yet* |
> | Use 3 | *No dedicated UC ORSD yet* |
> | Use 4 | UC-03 — see [Related documents](use-cases/README.md#5-related-documents) |
> | Use 5 | UC-07 — see [Related documents](use-cases/README.md#5-related-documents) |

---

## 6. Ontology Requirements

### a. Non-Functional Requirements

| ID | Requirement | Description |
|----|-------------|-------------|
| NFR 1 | **Concise terminology** | The ontology shall use precise, domain-appropriate terms aligned with international standards and established engineering vocabulary. |
| NFR 2 | **Consistency** | The model shall avoid contradictory assertions and redundant modelling to support the logical interpretation of classes and properties. ADIRO individuals are **detections, not idealised drawing constructs** - historical sheets are routinely clipped, torn or partially legible - so structural axioms must not assert a completeness the extraction cannot guarantee. Closed-world completeness checks belong in SHACL over a finished extraction, not in OWL cardinality over detections ([#84](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/84)). |
| NFR 3 | **Extendability** | The ontology shall be built to accommodate new AEC disciplines (e.g., Facade, MEP) without restructuring the core model, and shall reuse established external ontologies where doing so is sound. Extendability is achieved today through the modular internal package structure (e.g. `aec_domain_common`, `aec_facade_domain`). ADIRO imports no external ontology: how external terms may be reused is governed by [External ontology imports](../design-decisions/external-ontology-imports.md), which prefers the lightest option that meets the need and sets a test for when a core module may reference an external vocabulary at all. PROV-O is reused directly in `aec_provenance`; DAnO is mapped at annotation level only in the optional `aec_dano_alignment` layer ([DAnO comparison](../design-decisions/dano-comparison.md)); GeoSPARQL remains deferred ([#36](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/36)). A per-vocabulary reuse justification is being added to the ORSD ([#82](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/82)). |
| NFR 4 | **Reliability** | The ontology and its metadata shall be structured to ensure sustained availability and traceability for long-term use in the AECO industry. |
| NFR 5 | **FAIR principles** | The ontology shall be developed, documented, and published to ensure it is Findable, Accessible, Interoperable, and Reusable. |
| NFR 6 | **Modularity and Scalability** | The ontology shall support a modular framework where different aspects of a drawing can be processed by independent extraction services and subsequently aggregated without loss of semantic integrity or performance degradation when scaled to multi-document collections. |

---

### b. Functional Requirements: Competency Question Groups (CQGs)

!!! note "Which module answers these, and a known traceability gap"
    **CQG 2, 3 and 4 depend on extraction provenance** and are served by the `aec_provenance` module
    (`FieldAssertion`, `InferenceMeta`, `hasConfidence`, `capturedCaption`, `assertedBy`): **CQ 3.1** needs a
    confidence score, **CQ 3.2** needs predicted and ground-truth claims to be distinct individuals, **CQ 2.4**
    needs a per-claim validation status, and **CQ 4.4** needs each result attributed to the service that
    produced it. This is the requirement that justifies the module.

    **The gap:** the CQGs on this page and the competency questions in the per-use-case ORSDs are two separate
    systems that do not reference each other, and their numbering collides (this page's CQ 5.2 is about
    external ontology links; UC-01's is about disciplines; UC-07's is about wall lengths). **No written
    use-case ORSD currently claims CQG 2, 3 or 4.** Tracked in [#86](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/86), with the underlying
    question - write an extraction ORSD, or cut to use-case demand - in the title-block vocabulary review's
    Decision 2. Cite a CQ from this page as *ORSD CQ n.n* to avoid the collision.

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
- **CQ 5.2:** Which external ontology classes are linked to a given metadata:DrawingElement for cross-domain interoperability?  *(the linking property itself — working name `depicts` — is not yet defined in the ontology, so let's treat it as a proposed pending Open Issue **OI-1**. Note that UC-06 and UC-07 each specify their own (`depictsMaterial`, `depictsElement`), both with domain `Drawing` rather than `DrawingElement`; reconciling that is part of OI-1. See [#80](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/80).)*

---

## Version history

### v1.2 (September 2026)

Changed in [PR #76](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/76), alongside the first
provenance module in the suite:

- **NFR 2 (Consistency)** now records that ADIRO individuals are **detections, not idealised drawing
  constructs** — historical sheets are routinely clipped, torn or partially legible — so structural axioms
  must not assert a completeness the extraction cannot guarantee, and closed-world completeness checks belong
  in SHACL rather than in OWL cardinality ([#84](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/84)).
- **NFR 3 (Extendability)** rewritten. It previously said external reuse "is a target for future alignment";
  it now points at the normative
  [External ontology imports](../design-decisions/external-ontology-imports.md) rule and records where each
  candidate stands (PROV-O reused in the core, DAnO annotation-level only in an optional compatibility layer,
  GeoSPARQL deferred).
- **CQG section** gains a note recording that **CQG 2, 3 and 4 are what justify the `aec_provenance` module**,
  and that the CQGs on this page and the per-use-case competency questions are separate systems that never
  reference each other and whose numbering collides
  ([#86](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/86)).
- **CQ 5.2** annotated: open issue OI-1 remains open, and reconciling UC-06's `depictsMaterial` and UC-07's
  `depictsElement` (both with domain `Drawing` rather than `DrawingElement`) is part of it
  ([#80](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/80)).

No competency question was added, removed or re-numbered, so this is a MINOR revision.

### v1.1 (July 2026)

Predates this changelog.
