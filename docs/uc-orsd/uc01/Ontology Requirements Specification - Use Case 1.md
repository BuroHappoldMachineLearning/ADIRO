# Titleblock-Based Drawing Search

> **Methodology:** LOT (Linked Open Terms) **Use Case ID:** UC-01 **Version:** 0.2 (draft) **Changes from v 0.1:** Added `DrawingType` to information needs; added FR 6 (Drawing Type Classification) after FR 5 (Discipline); CQ groups and traceability matrix updated accordingly; FRs renumbered for consistency.

---

## 1. Use Case

| Field             | Content                                                                                                       |
| ----------------- | ------------------------------------------------------------------------------------------------------------- |
| **ID**            | UC-01                                                                                                         |
| **Title**         | Titleblock-Based Drawing Search                                                                               |
| **Statement**     | As an engineer, I want to search and filter drawings based on the information in the titleblock.              |
| **Primary Actor** | Engineer                                                                                                      |
| **Goal**          | Retrieve a set of drawings matching one or more titleblock metadata criteria, individually or in combination. |

---

## 2. Information Needs Analysis

The use case is decomposed into three categories of information it implicitly depends on.

### 2.1 Entities

Things that exist independently and will become OWL Classes.

| Entity          | Rationale                                                              |
| --------------- | ---------------------------------------------------------------------- |
| Drawing         | The primary object being searched                                      |
| DrawingRevision | Titleblock data (status, date, persons) changes per revision           |
| Project         | Drawings are grouped under a project                                   |
| Person          | Authors, checkers, and approvers appear in the titleblock              |
| Discipline      | Engineering domain (Structural, MEP, Civil, Architectural…)            |
| DrawingType     | View nature of a drawing (Plan, Section, Elevation, Detail, Schedule…) |
| StatusCode      | Approval state (IFC, IFR, AFC…) expressed as a controlled vocabulary   |
| DrawingPackage  | Drawings are grouped into volumes or packages within a project         |

> **Design note — Titleblock:** `Titleblock` is not modelled as a separate entity. Its metadata is distributed directly across `Drawing` (static identity fields) and `DrawingRevision` (revision-specific fields). This avoids unnecessary indirection while preserving the semantic distinction between drawing-level and revision-level data.

> **Design note — Discipline vs DrawingType:** These are two orthogonal classification axes. `Discipline` describes the engineering domain a drawing belongs to; `DrawingType` describes the view nature of the drawing. A single drawing carries one value from each axis independently (e.g. a Structural Section, or an MEP Plan).

> **Design note — Person vs Role:** `Person` models what an individual _is_, not the role they play. Roles (Author, Checker, Approver) are expressed as distinct Object Properties on `DrawingRevision`, not as subclasses of `Person`. This keeps `Person` reusable across roles and binds each role assignment to its specific revision context.

### 2.2 Attributes -- Datatype Properties

Characteristics of a single entity; will become Datatype Properties.

| Attribute       | Entity          | Expected Type |
| --------------- | --------------- | ------------- |
| Drawing number  | Drawing         | xsd:string    |
| Drawing title   | Drawing         | xsd:string    |
| Scale           | Drawing         | xsd:string    |
| Sheet size      | Drawing         | xsd:string    |
| Revision code   | DrawingRevision | xsd:string    |
| Issue date      | DrawingRevision | xsd:date      |
| Person name     | Person          | xsd:string    |
| Project name    | Project         | xsd:string    |
| Project number  | Project         | xsd:string    |
| Package name    | DrawingPackage  | xsd:string    |
| Discipline code | Discipline      | xsd:string    |
| Type label      | DrawingType     | xsd:string    |
| Status label    | StatusCode      | xsd:string    |

### 2.3 Relations

Links between two entities; will become Object Properties.

| Relation           | Domain          | Range           |
| ------------------ | --------------- | --------------- |
| has revision       | Drawing         | DrawingRevision |
| belongs to project | Drawing         | Project         |
| has discipline     | Drawing         | Discipline      |
| has drawing type   | Drawing         | DrawingType     |
| belongs to package | Drawing         | DrawingPackage  |
| has author         | DrawingRevision | Person          |
| has checker        | DrawingRevision | Person          |
| has approver       | DrawingRevision | Person          |
| has status code    | DrawingRevision | StatusCode      |

---

## 3. Functional Requirements

Each FR describes one representational capability the ontology must have, in implementation-neutral language.

**Obligation levels:** MUST = mandatory for current scope; SHOULD = important but deferrable; MAY = optional extension.

---

**FR 1 — Drawing Identity Fields**

> The ontology MUST represent the core identity fields of a drawing — drawing number, title, scale, and sheet size — such that drawings can be retrieved and distinguished by these fields.

- Source: UC-01
- Derived terms: `:Drawing`, `:drawingNumber`, `:drawingTitle`, `:hasScale`, `:sheetSize`

---

**FR 2 — Project Membership**

> The ontology MUST represent the relationship between a drawing and the project it belongs to, such that all drawings within a given project can be retrieved as a set.

- Source: UC-01
- Derived terms: `:Project`, `:belongsToProject`, `:projectName`, `:projectNumber`

---

**FR 3 — Revision History and Temporal Metadata**

> The ontology MUST represent multiple revisions of the same drawing as distinct entities, each carrying a revision code, issue date, and status code, such that both the current state and the full revision history of a drawing can be queried.

- Source: UC-01
- Derived terms: `:DrawingRevision`, `:hasRevision`, `:isRevisionOf`, `:revisionCode`, `:issueDate`

---

**FR 4 — Role-Differentiated Person Attribution**

> The ontology MUST distinguish between the roles of Author, Checker, and Approver as separate relationships between a drawing revision and a person, such that drawings can be filtered by a specific person in a specific role.

- Source: UC-01
- Derived terms: `:Person`, `:hasAuthor`, `:hasChecker`, `:hasApprover`, `:personName`
-  hasChecker - "isCheckedby"  "isAuthoredby" "isApprovedby" 
---

**FR 5 — Discipline Classification**

> The ontology MUST represent the engineering discipline of a drawing (e.g. Structural, MEP, Civil, Architectural), such that drawings can be filtered by discipline and cross-discipline queries can be executed.

- Source: UC-01
- Derived terms: `:Discipline`, `:hasDiscipline`, `:disciplineCode`

---

**FR 6 — Drawing Type Classification**

> The ontology MUST represent the drawing type of a drawing using a controlled vocabulary (e.g. Plan, Section, Elevation, Detail, Schedule), such that drawings can be filtered by their view type independently of their engineering discipline.

- Source: UC-01
- Derived terms: `:DrawingType`, `:hasDrawingType`, `:typeLabel`

---

**FR 7 — Issue Status**

> The ontology MUST represent the approval status of each drawing revision using a controlled vocabulary of status codes, such that drawings can be filtered by their current or historical approval state.

- Source: UC-01
- Derived terms: `:StatusCode`, `:hasStatusCode`, `:statusLabel`

---

**FR 8 — Package / Volume Grouping** -- Lowest Priority

> The ontology SHOULD represent the grouping of drawings into packages or volumes within a project, such that project-scoped and package-scoped searches can both be supported.

- Source: UC-01
- Derived terms: `:DrawingPackage`, `:belongsToPackage`, `:packageName`

---

## 4. Competency Questions

CQs are grouped by the FR they validate. Each must be translatable directly into a SPARQL query.

---

### CQ Group 1 — Drawing Identity (validates FR 1)

| ID     | Competency Question                                       |
| ------ | --------------------------------------------------------- |
| CQ 1.1 | What drawings have a drawing number beginning with "ST-"? |
| CQ 1.2 | What is the title of drawing number "ST-101"?             |
| CQ 1.3 | What drawings are drawn at scale 1:50?                    |

---

### CQ Group 2 — Project Membership (validates FR 2)

| ID     | Competency Question                                           |
| ------ | ------------------------------------------------------------- |
| CQ 2.1 | What drawings belong to project "HS 2-N 400"?                 |
| CQ 2.2 | How many drawings are currently registered under project "X"? |

---

### CQ Group 3 — Revision History (validates FR 3)

| ID     | Competency Question                                                                    |
| ------ | -------------------------------------------------------------------------------------- |
| CQ 3.1 | What is the latest revision code of drawing "ST-101"?                                  |
| CQ 3.2 | What drawings were issued after 1 January 2024?                                        |
| CQ 3.3 | How many revisions has drawing "ST-101" gone through, and what were their issue dates? |

---

### CQ Group 4 — Role-Differentiated Persons (validates FR 4)

| ID     | Competency Question                                          |
| ------ | ------------------------------------------------------------ |
| CQ 4.1 | What drawings were authored by "J. Smith"?                   |
| CQ 4.2 | What drawings were checked by "A. Chen"?                     |
| CQ 4.3 | For drawing "ST-101 Rev C", who was the approving authority? |

---

### CQ Group 5 — Discipline (validates FR 5)

|ID|Competency Question|
|---|---|
|CQ 5.1|What drawings are classified under the Structural discipline?|
|CQ 5.2|What disciplines are represented in project "X"?|

---

### CQ Group 6 — Drawing Type (validates FR 6)

|ID|Competency Question|
|---|---|
|CQ 6.1|What drawings are of type "Section"?|
|CQ 6.2|What drawing types are used in project "X"?|

---

### CQ Group 7 — Issue Status (validates FR 7)

| ID     | Competency Question                                                                                     |
| ------ | ------------------------------------------------------------------------------------------------------- |
| CQ 7.1 | What drawings currently carry the status "Issued for Construction"?                                     |
| CQ 7.2 | Which drawings changed from status "Issued for Review" to "Approved for Construction" across revisions? |

---

### CQ Group 8 — Package Grouping (validates FR 8)

| ID     | Competency Question                                                          |
| ------ | ---------------------------------------------------------------------------- |
| CQ 8.1 | What drawings belong to package "Volume 3"?                                  |
| CQ 8.2 | Which drawings in package "Volume 3" still have status "Issued for Comment"? |

---

### CQ Group I — Integration / Multi-field Queries

These CQs test the combined coverage of multiple FRs.

| ID     | Competency Question                                                             | FRs exercised          |
| ------ | ------------------------------------------------------------------------------- | ---------------------- |
| CQ-I 1 | What MEP drawings in project "X" were approved by "R. Jones" after March 2024?  | FR 2, FR 4, FR 5, FR 7 |
| CQ-I 2 | What drawings at scale 1:50 in the Structural discipline belong to project "Y"? | FR 1, FR 2, FR 5       |
| CQ-I 3 | What Structural drawings of type "Detail" belong to project "X"?                | FR 2, FR 5, FR 6       |

---

## 5. SPARQL Validation

The following example demonstrates that the term inventory is sufficient to answer integration query CQ-I 1.

**CQ-I 1:** _What MEP drawings in project "X" were approved by "R. Jones" after March 2024?_

```sparql
PREFIX : <https://example.org/aec-ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?drawing ?drawingNumber WHERE {
  ?drawing    a                   :Drawing ;
              :drawingNumber      ?drawingNumber ;
              :hasDiscipline      ?disc ;
              :belongsToProject   :ProjectX ;
              :hasRevision        ?rev .

  ?disc       :disciplineCode     "MEP" .

  ?rev        :hasApprover        ?person ;
              :issueDate          ?date .

  ?person     :personName         "R. Jones" .

  FILTER (?date > "2024-03-01"^^xsd:date)
}
```

Every filter condition maps to a defined property. The query is fully expressible, confirming that CQ-I 1 is covered by the current term inventory.

---

## 6. Traceability Matrix

| OWL Term            | CQ(s)                                          | FR(s)                              | UC    |
| ------------------- | ---------------------------------------------- | ---------------------------------- | ----- |
| `:Drawing`          | CQ 1.x, CQ 2.x, CQ 3.x, CQ 5.x, CQ 6.x, CQ 8.x | FR 1, FR 2, FR 3, FR 5, FR 6, FR 8 | UC-01 |
| `:DrawingRevision`  | CQ 3.x, CQ 4.x, CQ 7.x                         | FR 3, FR 4, FR 7                   | UC-01 |
| `:Project`          | CQ 2.x, CQ-I 1                                 | FR 2                               | UC-01 |
| `:Person`           | CQ 4.x, CQ-I 1                                 | FR 4                               | UC-01 |
| `:Discipline`       | CQ 5.x, CQ-I 1, CQ-I 2, CQ-I 3                 | FR 5                               | UC-01 |
| `:DrawingType`      | CQ 6.x, CQ-I 3                                 | FR 6                               | UC-01 |
| `:StatusCode`       | CQ 7.x, CQ 8.2                                 | FR 7                               | UC-01 |
| `:DrawingPackage`   | CQ 8.x                                         | FR 8                               | UC-01 |
| `:hasRevision`      | CQ 3.x                                         | FR 3                               | UC-01 |
| `:hasAuthor`        | CQ 4.1                                         | FR 4                               | UC-01 |
| `:hasChecker`       | CQ 4.2                                         | FR 4                               | UC-01 |
| `:hasApprover`      | CQ 4.3, CQ-I 1                                 | FR 4                               | UC-01 |
| `:hasStatusCode`    | CQ 7.x, CQ 8.2                                 | FR 7                               | UC-01 |
| `:belongsToProject` | CQ 2.x, CQ-I 1, CQ-I 2, CQ-I 3                 | FR 2                               | UC-01 |
| `:hasDiscipline`    | CQ 5.x, CQ-I 1, CQ-I 2, CQ-I 3                 | FR 5                               | UC-01 |
| `:hasDrawingType`   | CQ 6.x, CQ-I 3                                 | FR 6                               | UC-01 |
| `:belongsToPackage` | CQ 8.x                                         | FR 8                               | UC-01 |
| `:drawingNumber`    | CQ 1.1, CQ 1.2                                 | FR 1                               | UC-01 |
| `:drawingTitle`     | CQ 1.2                                         | FR 1                               | UC-01 |
| `:hasScale`         | CQ 1.3, CQ-I 2                                 | FR 1                               | UC-01 |
| `:revisionCode`     | CQ 3.1, CQ 3.3                                 | FR 3                               | UC-01 |
| `:issueDate`        | CQ 3.2, CQ 3.3, CQ-I 1                         | FR 3                               | UC-01 |
| `:personName`       | CQ 4.x, CQ-I 1                                 | FR 4                               | UC-01 |
| `:disciplineCode`   | CQ 5.x                                         | FR 5                               | UC-01 |
| `:typeLabel`        | CQ 6.x                                         | FR 6                               | UC-01 |
| `:statusLabel`      | CQ 7.x                                         | FR 7                               | UC-01 |
| `:projectName`      | CQ 2.x                                         | FR 2                               | UC-01 |
| `:projectNumber`    | CQ 2.x                                         | FR 2                               | UC-01 |
| `:packageName`      | CQ 8.x                                         | FR 8                               | UC-01 |

---

_End of ORSD — UC-01 v 0.2_