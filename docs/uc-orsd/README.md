# ADIRO Use Case Summary & Documentation

## 1. Executive Summary

This document provides a consolidated reference for the **ADIRO AEC Drawing Ontology** project, developed under the KTP programme. The project aims to build a formal ontology for Architecture, Engineering, and Construction (AEC) drawings, enabling intelligent search, cross-referencing, content aggregation, and compliance checking across heterogeneous drawing sets.

**Methodology.** The project follows the **LOT (Linked Open Terms)** methodology:

```
Use Case → Information Needs → Functional Requirements → Competency Questions → OWL Terms
```

This pipeline enforces **forward traceability** (every OWL term traces back to a use case need) and **backward testability** (every competency question can be validated via SPARQL).

**Current Status (as of 2026-07-08):**

- **7 use cases** defined, covering search, linking, comparison, aggregation, and measurement.
- **4 of 7 ORSDs completed** (UC-01, UC-03, UC-06, UC-07).
- **3 ORSDs not yet written** (UC-02 Facade, UC-04, UC-05).
- UC-01 ORSD has been reviewed and alignment decisions made with the existing ontology.
- UC-03 ORSD review completed with 3 open issues remaining.
- Ontology versioning plan established (V1 through V4.x).

---

## 2. Use Case Catalogue

### UC-01: Titleblock-Based Drawing Search

| Field           | Detail                                                                                                   |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Actor**       | Engineer                                                                                                  |
| **Goal**        | Search drawings based on titleblock information                                                          |
| **Description** | As an engineer, I want to search easily a number of drawings based on the information in the titleblock. |
| **ORSD Status** | ✅ [Completed (v0.3)](<uc01/Ontology Requirements Specification - Use Case 1.md>) |

### UC-02: Facade Performance Lines

| Field | Detail |
|---|---|
| **Actor** | Facade Engineer |
| **Goal** | Identify facade performance lines and detect breaks/gaps |
| **Description** | As a facade engineer, I want to identify facade performance lines (water/air barriers, thermal line) to identify cases where there is space/break between them. |
| **ORSD Status** | Not Started |

### UC-03: Reference Symbol Cross-Sheet Linking

| Field           | Detail                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Actor**       | Designer                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| **Goal**        | Navigate across sheets via reference symbols                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| **Description** | As a designer, I want to understand how a certain building element or parts are designed, so I want to find all the drawings that are connected to a drawing. In engineering drawings, there are typically Reference Symbols such as Detail Markers, Section Markers, and Elevation Markers. By recognising these Reference Symbols, we can automatically match and link the Sections, Details, and Elevations they reference -- enabling navigation across sheets and even across drawing sets. |
| **ORSD Status** | ✅ [Completed (v0.2)](<uc03/Ontology Requirements Specification — Use Case 3.md>) — 3 open issues remaining |

### UC-04: Element Similarity Search

| Field           | Detail                                                                                                                                                |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Actor**       | Designer                                                                                                                                              |
| **Goal**        | Find similar elements for reference and design understanding                                                                                          |
| **Description** | As a designer, I want to find all elements that are similar to a certain one so I can use it as a reference or better understand how it was designed. |
| **ORSD Status** | Not Started                                                                                                                                           |

### UC-05: Contractor Design Comparison

| Field | Detail |
|---|---|
| **Actor** | Designer |
| **Goal** | Compare contractor design against own design for compliance/quality |
| **Description** | As a designer, I want to compare a contractor's design against our own, in order to ensure compliance/quality. This involves comparing the KG representation of the two drawings. |
| **ORSD Status** | Not Started |

### UC-06: Drawing Content Aggregation & Hazardous Material Identification

| Field | Detail |
|---|---|
| **Actor** | Engineer |
| **Goal** | Aggregate/summarise drawing content for reports, archiving, and Building Safety Act compliance |
| **Description** | As an engineer, I want to aggregate/summarise the content of many different drawings so they can be easily grouped for inclusion in a report or archiving. Related to the Building Safety Act. |
| **ORSD Status** | ⚠️ [Draft (v0.1)](<uc06/Ontology Requirements Specification — Use Case 6.md>) — not yet aligned with the current ontology |

### UC-07: Wall Orientation Identification & Measurement

| Field | Detail |
|---|---|
| **Actor** | Engineer |
| **Goal** | Measure all walls facing a specific cardinal direction in a plan drawing |
| **Description** | As an engineer, I want to measure all walls that are facing north or east in a plan drawing. |
| **ORSD Status** | ⚠️ [Draft (v0.2)](<uc07/Ontology Requirements Specification — Use Case 7.md>) — not yet aligned with the current ontology |

---

## 3. Prioritization Matrix

> [!info] Source
> Prioritization agreed at the **KTP Monthly Meeting on 2026-06-10**.
> Priority order: **1 → 3 → 6 → 7 → 4 → 5 → 2**

| Priority | Use Case | Academic Impact | Business Commonality | Business Amplitude | Data Difficulty | Implementation Difficulty | Notes |
|:---:|---|:---:|:---:|:---:|:---:|:---:|---|
| **XL** | UC-01: Titleblock Search | XS | XL | M / L | XS | XS (Modern) / M (Historical) | Done already |
| **XL** | UC-03: Cross-Sheet Linking | M | XL | M / L | XS | S (Modern) / M (Historical) | |
| **L** | UC-06: Content Aggregation | XL | M | XL | M | M | |
| **L** | UC-07: Wall Orientation | S | L | L | S | M / L | |
| **M** | UC-04: Element Similarity | M | L | L | M | L / XL | |
| **S/M** | UC-05: Contractor Comparison | L | XL | XL | M / L | XL | |
| **S** | UC-02: Facade Performance | L | S | L | L | L | |

**Key observations:**

- **UC-01 and UC-03** are highest priority (XL) due to extreme business commonality (XL) and low data difficulty (XS). UC-01 is already implemented.
- **UC-06** ranks high due to its exceptional academic impact (XL) and business amplitude (XL), despite moderate implementation difficulty.
- **UC-07** is prioritised for its relatively low data difficulty (S) and clear, measurable output.
- **UC-05** has the highest implementation difficulty (XL) and is deprioritised despite strong business commonality and amplitude.
- **UC-02** is lowest priority due to small business commonality (S), though it has notable academic impact (L).

---

## 4. Current Progress & Next Steps

### Completed

Following the LOT pipeline (`Use Case → Information Needs → Functional Requirements → Competency Questions → OWL Terms`), the following milestones have been achieved:

| Milestone | UC-01 | UC-03 |
|---|:---:|:---:|
| ORSD (Use Case → CQs) | ✅ v0.3 | ✅ v0.2 |
| OWL Terms Specification | ✅ | ✅ |
| ORSD Review & Alignment | ✅ | ✅ (3 open issues) |
| T-Box Implementation (.owl/.ttl) | ✅ | ✅ |

### Next Steps

With the T-Box (schema-level ontology) in place for UC-01 and UC-03, the immediate next phase is **validation through instantiation**:

**Step 1 — A-Box Test Data Creation**

Populate the ontology with sample instance data (Named Individuals) based on real or representative drawing scenarios. This includes:

- Creating RDF individuals for `DrawingSheet`, `Project`, `Person`, `Discipline`, `DrawingRevision`, etc. (UC-01)
- Creating RDF individuals for `ReferenceSymbol` and cross-sheet linking relationships (UC-03)
- Ensuring test data covers edge cases identified in the Competency Questions (e.g. multi-revision drawings, cross-discipline queries)

**Step 2 — SPARQL Competency Question Validation**

Execute the SPARQL queries defined in each ORSD against the populated A-Box to verify that every Competency Question is answerable. This serves as the formal **acceptance test** for the ontology:

- Each CQ must return correct, non-empty results on the test data
- Integration CQs (CQ-I group) must work across UC-01 and UC-03 terms combined
- Any CQ that fails indicates a gap in either the T-Box modelling or the test data coverage

---

## 5. Related documents

| Use case | ORSD | Visualization TTL |
|---|---|---|
| UC-01 | [Ontology Requirements Specification - Use Case 1.md](<uc01/Ontology Requirements Specification - Use Case 1.md>) | [uc01-merged-for-visualization.ttl](uc01/uc01-merged-for-visualization.ttl) |
| UC-03 | [Ontology Requirements Specification — Use Case 3.md](<uc03/Ontology Requirements Specification — Use Case 3.md>) | [uc03-core-for-visualization.ttl](uc03/uc03-core-for-visualization.ttl) |
| UC-06 | [Ontology Requirements Specification — Use Case 6.md](<uc06/Ontology Requirements Specification — Use Case 6.md>) | — |
| UC-07 | [Ontology Requirements Specification — Use Case 7.md](<uc07/Ontology Requirements Specification — Use Case 7.md>) | — |
