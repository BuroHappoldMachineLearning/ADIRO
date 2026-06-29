# Titleblock-Based Drawing Search

> **Methodology:** LOT (Linked Open Terms) **Use Case ID:** UC-01 **Version:** 0.3 (draft)
>
> **Changes from v 0.2:** Aligned with existing ontology modules (`aec_drawing_metadata`, `aec_domain_common`) per @alelom's PR review. Key changes:
> - `Drawing` → `metadata:DrawingSheet`; `Layout` added as a first-class entity (G1).
> - `dcommon:hasDiscipline` proposed to move from `LayoutContentType` to `Layout` (G5 — open issue).
> - Reuse `dcommon:Discipline` class hierarchy; drop `disciplineCode` string property (G3).
> - Reuse `metadata:LayoutContentType`; drop `DrawingType` / `hasDrawingType` / `typeLabel` (G4).
> - Datatype properties (`drawingIdentifier`, `drawingTitle`, `hasScale`, `sheetSize`) attached directly to `DrawingSheet` — no intermediate entity (G2).
> - New object properties wired into `metadata:contains` / `metadata:hasProperty` via `rdfs:subPropertyOf` (G6).
> - SPARQL placeholder namespace replaced with real module prefixes (G8).
> - Only `isRevisionOf` materialised as `owl:inverseOf`; other inverses deferred (G9).
> - Stray editing artifact on FR 4 removed.
> - New Section 7: Module Alignment Summary.

---

## 1. Use Case

| Field             | Content                                                                                                       |
| ----------------- | ------------------------------------------------------------------------------------------------------------- |
| **ID**            | UC-01                                                                                                         |
| **Title**         | Titleblock-Based Drawing Search                                                                               |
| **Statement**     | As an engineer, I want to search and filter drawings based on the information in the titleblock.              |
| **Primary Actor** | Engineer                                                                                                      |
| **Goal**          | Retrieve a set of drawing sheets matching one or more titleblock metadata criteria, individually or in combination. |

> **Terminology note:** Throughout this ORSD, the user-facing term "drawing" refers to a `metadata:DrawingSheet` — the top-level, titleblock-bearing, searchable unit in the existing ontology. A sheet contains one or more `Layout`s, each of which carries its content type (Plan / Section / Detail / …) and discipline classification.

---

## 2. Information Needs Analysis

### 2.1 Entities

Things that exist independently and will become OWL Classes.

| Entity              | Module                              | Action | Rationale                                                                                |
| ------------------- | ----------------------------------- | ------ | ---------------------------------------------------------------------------------------- |
| `DrawingSheet`      | `aec_drawing_metadata`              | REUSE  | The primary object being searched. UC-01 "Drawing" maps here.                            |
| `Layout`            | `aec_drawing_metadata`              | REUSE  | A view region within a DrawingSheet; carries discipline and content-type classification. |
| `LayoutContentType` | `aec_drawing_metadata`              | REUSE  | View type (Plan / Section / Elevation / Detail / Table / Perspective).                   |
| `DrawingRevision`   | `aec_drawing_metadata`              | NEW    | Titleblock data (status, date, persons) changes per revision.                            |
| `Project`           | `aec_drawing_metadata`              | NEW    | Drawings are grouped under a project.                                                    |
| `Person`            | `aec_drawing_metadata`              | NEW    | Authors, checkers, and approvers appear in the titleblock.                               |
| `Discipline`        | `aec_domain_common`                 | REUSE  | Existing class hierarchy (`Structural`, `MEP`, `Architectural`, …).                      |
| `StatusCode`        | `aec_drawing_metadata`              | NEW    | Approval state (IFC, IFR, AFC…) expressed as a controlled vocabulary.                    |
| `DrawingPackage`    | `aec_drawing_metadata`              | NEW    | Drawings are grouped into volumes or packages within a project.                          |

> **Design note — DrawingSheet vs Layout:** A `DrawingSheet` may contain multiple `Layout`s, each with its own `LayoutContentType` and `Discipline`. Queries for "Structural Plan drawings" filter for sheets containing at least one Layout whose content type is `Plan` and whose discipline is (a subclass of) `Structural`.

> **Design note — Titleblock as visual region vs titleblock data:** The existing `metadata:Titleblock` class models the *visual region* on a sheet (for CV annotation). The *information* conventionally found inside it (`drawingIdentifier`, `drawingTitle`, …) is attached as datatype properties directly on `DrawingSheet`. The two layers coexist independently: a sheet has a drawing number whether or not its visual Titleblock region has been bounded in annotation.

> **Design note — `:Metadata` → `:MetadataContainer`:** The existing `:Metadata` class has been renamed to `:MetadataContainer` (team decision). It is the parent of `Titleblock`, `RevisionTable`, `Legend`, and `Note` — i.e. it models *visual supporting regions*, not semantic metadata. The rename avoids confusion with UC-01's datatype properties (`drawingIdentifier`, `drawingTitle`, etc.) on `DrawingSheet`.

> **Design note — DrawingType deprecated:** UC-01 v0.2 introduced `:DrawingType` (Plan, Section, Elevation, Detail, Schedule). This is the same axis as `metadata:LayoutContentType` (Plan, Section, Elevation, Detail, Table, Perspective). "Schedule" maps to `Table`. `DrawingType` is removed in v0.3 — `LayoutContentType` is reused.

> **Design note — Discipline reuse:** UC-01 v0.2 introduced `:Discipline` plus a `:disciplineCode` string property. The existing `dcommon:Discipline` is already a full class hierarchy (`Structural`, `MEP > Mechanical / Electrical > Lighting / Plumbing`, `Architectural > Facade / FireLifeSafety`, `Masterplan`). v0.3 reuses it and drops `:disciplineCode` — discipline filtering uses `rdf:type` checks against the class hierarchy (e.g. `?disc a dcommon:MEP`), which automatically rolls up sub-disciplines via `rdfs:subClassOf` reasoning.

> **Design note — Person vs Role:** `Person` models what an individual *is*, not the role they play. Roles (Author, Checker, Approver) are expressed as distinct Object Properties on `DrawingRevision`, not as subclasses of `Person`. This keeps `Person` reusable across roles and binds each role assignment to its specific revision context.

### 2.2 Attributes — Datatype Properties

Characteristics of a single entity. **Datatype properties on `DrawingSheet` are attached directly — no intermediate "metadata container" entity.**

| Attribute        | Entity            | Module                 | Action | Expected Type | Notes |
| ---------------- | ----------------- | ---------------------- | ------ | ------------- | ----- |
| `drawingIdentifier`  | `DrawingSheet`    | `aec_drawing_metadata` | NEW    | `xsd:string`  | Also known as "drawing number". |
| `drawingTitle`   | `DrawingSheet`    | `aec_drawing_metadata` | NEW    | `xsd:string`  | |
| `hasScale`       | `DrawingSheet`    | `aec_drawing_metadata` | NEW    | `xsd:string`  | |
| `sheetSize`      | `DrawingSheet`    | `aec_drawing_metadata` | NEW    | `xsd:string`  | |
| `revisionCode`   | `DrawingRevision` | `aec_drawing_metadata` | NEW    | `xsd:string`  | |
| `issueDate`      | `DrawingRevision` | `aec_drawing_metadata` | NEW    | `xsd:date`    | |
| `personName`     | `Person`          | `aec_drawing_metadata` | NEW    | `xsd:string`  | |
| `projectName`    | `Project`         | `aec_drawing_metadata` | NEW    | `xsd:string`  | |
| `projectNumber`  | `Project`         | `aec_drawing_metadata` | NEW    | `xsd:string`  | |
| `packageName`    | `DrawingPackage`  | `aec_drawing_metadata` | NEW    | `xsd:string`  | |
| `statusLabel`    | `StatusCode`      | `aec_drawing_metadata` | NEW    | `xsd:string`  | |

### 2.3 Relations — Object Properties

Links between two entities. New properties are wired into the existing generic top-level properties via `rdfs:subPropertyOf`.

| Relation              | Domain            | Range               | Module                 | Action | `subPropertyOf`         |
| --------------------- | ----------------- | ------------------- | ---------------------- | ------ | ----------------------- |
| `contains` (sheet)    | `DrawingSheet`    | `Layout` (1..*)     | `aec_drawing_metadata` | REUSE  | —                       |
| `hasProperty`         | `Layout`          | `LayoutContentType` | `aec_drawing_metadata` | REUSE  | —                       |
| `hasDiscipline` ⚠️    | `Layout`          | `Discipline` (min 1)| `aec_domain_common`    | REUSE¹ | —                       |
| `hasRevision`         | `DrawingSheet`    | `DrawingRevision`   | `aec_drawing_metadata` | NEW    | `metadata:contains`     |
| `isRevisionOf`        | `DrawingRevision` | `DrawingSheet`      | `aec_drawing_metadata` | NEW    | (inverse of hasRevision)|
| `belongsToProject`    | `DrawingSheet`    | `Project`           | `aec_drawing_metadata` | NEW    | (top-level)             |
| `belongsToPackage`    | `DrawingSheet`    | `DrawingPackage`    | `aec_drawing_metadata` | NEW    | (top-level)             |
| `isAuthoredBy`           | `DrawingRevision` | `Person`            | `aec_drawing_metadata` | NEW    | (top-level)             |
| `isCheckedBy`          | `DrawingRevision` | `Person`            | `aec_drawing_metadata` | NEW    | (top-level)             |
| `isApprovedBy`         | `DrawingRevision` | `Person`            | `aec_drawing_metadata` | NEW    | (top-level)             |
| `hasStatusCode`       | `DrawingRevision` | `StatusCode`        | `aec_drawing_metadata` | NEW    | `metadata:hasProperty`  |

¹ ⚠️ **Open issue (G5):** `dcommon:hasDiscipline` currently has `rdfs:domain metadata:LayoutContentType`. v0.3 proposes moving the domain to `metadata:Layout` (along with the `min 1` cardinality restriction). Discipline characterises the layout itself, not its content type — and the two are orthogonal axes (see design note below). Pending @alelom / @m-asakihattori sign-off.

> **Design note — two orthogonal axes on Layout:**
>
> ```
> Layout
>   ├── hasProperty   → LayoutContentType  (exactly 1: Plan / Section / Detail / …)
>   └── hasDiscipline → Discipline         (min 1: Structural / Facade / MEP / …)
> ```
>
> Content type describes the view nature; discipline describes the engineering domain. A Layout carries one independent value on each axis.

---

## 3. Functional Requirements

Each FR describes one representational capability the ontology must have, in implementation-neutral language.

**Obligation levels:** MUST = mandatory for current scope; SHOULD = important but deferrable; MAY = optional extension.

---

**FR 1 — Drawing Identity Fields**

> The ontology MUST represent the core identity fields of a drawing sheet — drawing number, title, scale, and sheet size — such that sheets can be retrieved and distinguished by these fields.

- Source: UC-01
- Derived terms: `metadata:DrawingSheet` (REUSE), `metadata:drawingIdentifier`, `metadata:drawingTitle`, `metadata:hasScale`, `metadata:sheetSize` (NEW datatype properties on `DrawingSheet`)

---

**FR 2 — Project Membership**

> The ontology MUST represent the relationship between a drawing sheet and the project it belongs to, such that all sheets within a given project can be retrieved as a set.

- Source: UC-01
- Derived terms: `metadata:Project` (NEW), `metadata:belongsToProject` (NEW), `metadata:projectName`, `metadata:projectNumber` (NEW datatype properties on `Project`)

---

**FR 3 — Revision History and Temporal Metadata**

> The ontology MUST represent multiple revisions of the same drawing sheet as distinct entities, each carrying a revision code, issue date, and status code, such that both the current state and the full revision history of a sheet can be queried.

- Source: UC-01
- Derived terms: `metadata:DrawingRevision` (NEW), `metadata:hasRevision` (NEW, `subPropertyOf metadata:contains`), `metadata:isRevisionOf` (NEW, inverse of `hasRevision` — materialised because CQ 3.x needs reverse navigation), `metadata:revisionCode`, `metadata:issueDate` (NEW)

---

**FR 4 — Role-Differentiated Person Attribution**

> The ontology MUST distinguish between the roles of Author, Checker, and Approver as separate relationships between a drawing revision and a person, such that sheets can be filtered by a specific person in a specific role.

- Source: UC-01
- Derived terms: `metadata:Person` (NEW), `metadata:isAuthoredBy`, `metadata:isCheckedBy`, `metadata:isApprovedBy` (NEW, top-level), `metadata:personName` (NEW)

> **Design note — inverse properties:** Only `isRevisionOf` is materialised as `owl:inverseOf` (CQ 3.x requires the reverse direction). For role-based relations, `isAuthoredBy` / `isCheckedBy` / `isApprovedBy` are *not* declared in v0.3 — forward properties are sufficient for SPARQL. ⚠️ **Open issue:** project-wide convention for `owl:inverseOf` vs reasoner-derived inverses — flagged for separate discussion.

---

**FR 5 — Discipline Classification**

> The ontology MUST support filtering drawing sheets by engineering discipline, reusing the existing `dcommon:Discipline` class hierarchy (`Structural`, `MEP`, `Architectural`, `Facade`, `FireLifeSafety`, `Masterplan`, plus their sub-disciplines), attached at the `Layout` level via `dcommon:hasDiscipline`.

- Source: UC-01
- Derived terms: `dcommon:Discipline` (REUSE), `dcommon:hasDiscipline` (REUSE — domain proposed to move from `LayoutContentType` to `Layout`, see G5)
- Note: `disciplineCode` from v0.2 is **removed** — filtering uses `rdf:type` against the class hierarchy, which gives automatic sub-discipline rollup (querying `dcommon:MEP` auto-includes `Mechanical`, `Electrical`, `Plumbing`).
- Note: `Civil` is to be added to `dcommon:Discipline` as a direct subclass of `Discipline` (confirmed by team discussion).

---

**FR 6 — Layout Content Type Classification**

> The ontology MUST support filtering drawing sheets by view type, reusing the existing `metadata:LayoutContentType` controlled vocabulary (`Plan`, `Section`, `Elevation`, `Detail`, `Table`, `Perspective`), attached at the `Layout` level via `metadata:hasProperty`.

- Source: UC-01
- Derived terms: `metadata:LayoutContentType` (REUSE), `metadata:Layout` (REUSE), `metadata:hasProperty` (REUSE)
- Note: UC-01 v0.2's `:DrawingType` (with subclasses Plan / Section / Elevation / Detail / Schedule) is **removed** — `metadata:LayoutContentType` already provides this. "Schedule" maps to the existing `metadata:Table` subclass.

---

**FR 7 — Issue Status**

> The ontology MUST represent the approval status of each drawing revision using a controlled vocabulary of status codes, such that sheets can be filtered by their current or historical approval state.

- Source: UC-01
- Derived terms: `metadata:StatusCode` (NEW), `metadata:hasStatusCode` (NEW, `subPropertyOf metadata:hasProperty`), `metadata:statusLabel` (NEW)

---

**FR 8 — Package / Volume Grouping** — *Lowest priority*

> The ontology SHOULD represent the grouping of drawing sheets into packages or volumes within a project, such that project-scoped and package-scoped searches can both be supported.

- Source: UC-01
- Derived terms: `metadata:DrawingPackage` (NEW), `metadata:belongsToPackage` (NEW), `metadata:packageName` (NEW)

---

## 4. Competency Questions

CQs are grouped by the FR they validate. Each must be translatable directly into a SPARQL query against the term inventory above.

### CQ Group 1 — Drawing Identity (validates FR 1)

| ID     | Competency Question                                              |
| ------ | ---------------------------------------------------------------- |
| CQ 1.1 | What drawing sheets have a drawing number beginning with "ST-"?  |
| CQ 1.2 | What is the title of the sheet with drawing number "ST-101"?     |
| CQ 1.3 | What drawing sheets are drawn at scale 1:50?                     |

### CQ Group 2 — Project Membership (validates FR 2)

| ID     | Competency Question                                                 |
| ------ | ------------------------------------------------------------------- |
| CQ 2.1 | What drawing sheets belong to project "HS 2-N 400"?                 |
| CQ 2.2 | How many drawing sheets are currently registered under project "X"? |

### CQ Group 3 — Revision History (validates FR 3)

| ID     | Competency Question                                                                         |
| ------ | ------------------------------------------------------------------------------------------- |
| CQ 3.1 | What is the latest revision code of the sheet with drawing number "ST-101"?                 |
| CQ 3.2 | What sheets were issued after 1 January 2024?                                               |
| CQ 3.3 | How many revisions has sheet "ST-101" gone through, and what were their issue dates?        |

### CQ Group 4 — Role-Differentiated Persons (validates FR 4)

| ID     | Competency Question                                          |
| ------ | ------------------------------------------------------------ |
| CQ 4.1 | What sheets were authored by "J. Smith"?                     |
| CQ 4.2 | What sheets were checked by "A. Chen"?                       |
| CQ 4.3 | For sheet "ST-101 Rev C", who was the approving authority?   |

### CQ Group 5 — Discipline (validates FR 5)

| ID     | Competency Question                                                                 |
| ------ | ----------------------------------------------------------------------------------- |
| CQ 5.1 | What sheets contain at least one Layout classified under the `Structural` discipline? |
| CQ 5.2 | What disciplines are represented across the Layouts of project "X"?                 |

### CQ Group 6 — Layout Content Type (validates FR 6)

| ID     | Competency Question                                                          |
| ------ | ---------------------------------------------------------------------------- |
| CQ 6.1 | What sheets contain a Layout of content type `Section`?                       |
| CQ 6.2 | What content types are used across the Layouts of project "X"?               |

### CQ Group 7 — Issue Status (validates FR 7)

| ID     | Competency Question                                                                                     |
| ------ | ------------------------------------------------------------------------------------------------------- |
| CQ 7.1 | What sheets currently carry the status "Issued for Construction"?                                       |
| CQ 7.2 | Which sheets changed from status "Issued for Review" to "Approved for Construction" across revisions?   |

### CQ Group 8 — Package Grouping (validates FR 8)

| ID     | Competency Question                                                              |
| ------ | -------------------------------------------------------------------------------- |
| CQ 8.1 | What sheets belong to package "Volume 3"?                                        |
| CQ 8.2 | Which sheets in package "Volume 3" still have status "Issued for Comment"?       |

### CQ Group I — Integration / Multi-field Queries

| ID     | Competency Question                                                                                  | FRs exercised               |
| ------ | ---------------------------------------------------------------------------------------------------- | --------------------------- |
| CQ-I 1 | What sheets in project "X" contain a `MEP` Layout and were approved by "R. Jones" after March 2024?  | FR 2, FR 4, FR 5, FR 7      |
| CQ-I 2 | What sheets at scale 1:50 contain a `Structural` Layout and belong to project "Y"?                   | FR 1, FR 2, FR 5            |
| CQ-I 3 | What sheets in project "X" contain a `Structural` Layout of content type `Detail`?                   | FR 2, FR 5, FR 6            |

---

## 5. SPARQL Validation

The following example demonstrates that the term inventory is sufficient to answer integration query CQ-I 1.

**CQ-I 1:** *What sheets in project "X" contain a MEP Layout and were approved by "R. Jones" after March 2024?*

```sparql
PREFIX metadata: <https://burohappoldmachinelearning.github.io/ADIRO/aec_drawing_metadata#>
PREFIX dcommon:  <https://burohappoldmachinelearning.github.io/ADIRO/aec_domain_common#>
PREFIX xsd:      <http://www.w3.org/2001/XMLSchema#>

SELECT ?sheet ?drawingIdentifier WHERE {
  ?sheet  a                          metadata:DrawingSheet ;
          metadata:drawingIdentifier     ?drawingIdentifier ;
          metadata:belongsToProject  metadata:ProjectX ;
          metadata:hasRevision       ?rev ;
          metadata:contains          ?layout .

  ?layout a                          metadata:Layout ;
          dcommon:hasDiscipline      ?disc .
  ?disc   a                          dcommon:MEP .

  ?rev    metadata:isApprovedBy       ?person ;
          metadata:issueDate         ?date .
  ?person metadata:personName        "R. Jones" .

  FILTER (?date > "2024-03-01"^^xsd:date)
}
```

Every filter condition maps to a defined property:

- `metadata:DrawingSheet`, `metadata:drawingIdentifier`, `metadata:belongsToProject`, `metadata:hasRevision`, `metadata:contains` — reused / new in `aec_drawing_metadata`.
- `metadata:Layout`, `dcommon:hasDiscipline`, `dcommon:MEP` — reused; note the `rdf:type` check against the class hierarchy automatically matches `Mechanical`, `Electrical`, `Plumbing`, `Lighting` via `rdfs:subClassOf` reasoning.
- `metadata:isApprovedBy`, `metadata:issueDate`, `metadata:personName` — new in `aec_drawing_metadata`.

The query is fully expressible, confirming that CQ-I 1 is covered by the current term inventory. The previous v0.2 placeholder prefix (`https://example.org/aec-ontology#`) is retired in favour of the real module namespaces.

---

## 6. Traceability Matrix

| OWL Term                       | Module                 | Action | CQ(s)                                          | FR(s)                              |
| ------------------------------ | ---------------------- | ------ | ---------------------------------------------- | ---------------------------------- |
| `metadata:DrawingSheet`        | `aec_drawing_metadata` | REUSE  | CQ 1.x, CQ 2.x, CQ 3.x, CQ 5.x, CQ 6.x, CQ 8.x | FR 1, FR 2, FR 3, FR 5, FR 6, FR 8 |
| `metadata:Layout`              | `aec_drawing_metadata` | REUSE  | CQ 5.x, CQ 6.x, CQ-I 1, CQ-I 2, CQ-I 3         | FR 5, FR 6                         |
| `metadata:LayoutContentType`   | `aec_drawing_metadata` | REUSE  | CQ 6.x, CQ-I 3                                 | FR 6                               |
| `metadata:DrawingRevision`     | `aec_drawing_metadata` | NEW    | CQ 3.x, CQ 4.x, CQ 7.x                         | FR 3, FR 4, FR 7                   |
| `metadata:Project`             | `aec_drawing_metadata` | NEW    | CQ 2.x, CQ-I 1                                 | FR 2                               |
| `metadata:Person`              | `aec_drawing_metadata` | NEW    | CQ 4.x, CQ-I 1                                 | FR 4                               |
| `dcommon:Discipline`           | `aec_domain_common`    | REUSE  | CQ 5.x, CQ-I 1, CQ-I 2, CQ-I 3                 | FR 5                               |
| `metadata:StatusCode`          | `aec_drawing_metadata` | NEW    | CQ 7.x, CQ 8.2                                 | FR 7                               |
| `metadata:DrawingPackage`      | `aec_drawing_metadata` | NEW    | CQ 8.x                                         | FR 8                               |
| `metadata:contains`            | `aec_drawing_metadata` | REUSE  | CQ-I 1, CQ-I 2, CQ-I 3                         | (structural)                       |
| `metadata:hasRevision`         | `aec_drawing_metadata` | NEW    | CQ 3.x                                         | FR 3                               |
| `metadata:isRevisionOf`        | `aec_drawing_metadata` | NEW    | CQ 3.x (reverse navigation)                    | FR 3                               |
| `metadata:isAuthoredBy`           | `aec_drawing_metadata` | NEW    | CQ 4.1                                         | FR 4                               |
| `metadata:isCheckedBy`          | `aec_drawing_metadata` | NEW    | CQ 4.2                                         | FR 4                               |
| `metadata:isApprovedBy`         | `aec_drawing_metadata` | NEW    | CQ 4.3, CQ-I 1                                 | FR 4                               |
| `metadata:hasStatusCode`       | `aec_drawing_metadata` | NEW    | CQ 7.x, CQ 8.2                                 | FR 7                               |
| `metadata:belongsToProject`    | `aec_drawing_metadata` | NEW    | CQ 2.x, CQ-I 1, CQ-I 2, CQ-I 3                 | FR 2                               |
| `dcommon:hasDiscipline`        | `aec_domain_common`    | REUSE  | CQ 5.x, CQ-I 1, CQ-I 2, CQ-I 3                 | FR 5                               |
| `metadata:hasProperty`         | `aec_drawing_metadata` | REUSE  | CQ 6.x, CQ-I 3                                 | FR 6                               |
| `metadata:belongsToPackage`    | `aec_drawing_metadata` | NEW    | CQ 8.x                                         | FR 8                               |
| `metadata:drawingIdentifier`       | `aec_drawing_metadata` | NEW    | CQ 1.1, CQ 1.2                                 | FR 1                               |
| `metadata:drawingTitle`        | `aec_drawing_metadata` | NEW    | CQ 1.2                                         | FR 1                               |
| `metadata:hasScale`            | `aec_drawing_metadata` | NEW    | CQ 1.3, CQ-I 2                                 | FR 1                               |
| `metadata:sheetSize`           | `aec_drawing_metadata` | NEW    | —                                              | FR 1                               |
| `metadata:revisionCode`        | `aec_drawing_metadata` | NEW    | CQ 3.1, CQ 3.3                                 | FR 3                               |
| `metadata:issueDate`           | `aec_drawing_metadata` | NEW    | CQ 3.2, CQ 3.3, CQ-I 1                         | FR 3                               |
| `metadata:personName`          | `aec_drawing_metadata` | NEW    | CQ 4.x, CQ-I 1                                 | FR 4                               |
| `metadata:statusLabel`         | `aec_drawing_metadata` | NEW    | CQ 7.x                                         | FR 7                               |
| `metadata:projectName`         | `aec_drawing_metadata` | NEW    | CQ 2.x                                         | FR 2                               |
| `metadata:projectNumber`       | `aec_drawing_metadata` | NEW    | CQ 2.x                                         | FR 2                               |
| `metadata:packageName`         | `aec_drawing_metadata` | NEW    | CQ 8.x                                         | FR 8                               |

---

## 7. Module Alignment Summary

This section makes the placement of every UC-01 term in the existing module hierarchy explicit, per @alelom's cross-cutting review point #2.

**Existing module hierarchy** (unchanged):

```
aec_drawing_metadata
        |
        +---- aec_common_symbols
                |
                +---- aec_domain_common
                        |
                        +---- aec_facade_domain
```

**Term placement:**

| Module                 | UC-01 contribution                                                                                                                                                          |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `aec_drawing_metadata` | **New classes:** `DrawingRevision`, `Project`, `Person`, `StatusCode`, `DrawingPackage`. **New properties:** all UC-01 datatype properties; `hasRevision` (⊂ `contains`), `isRevisionOf`, `hasStatusCode` (⊂ `hasProperty`), `belongsToProject`, `belongsToPackage`, `isAuthoredBy`, `isCheckedBy`, `isApprovedBy`. |
| `aec_common_symbols`   | No UC-01 contribution.                                                                                                                                                      |
| `aec_domain_common`    | **Reused:** `Discipline` and its subclasses; `hasDiscipline` (with proposed domain change from `LayoutContentType` to `Layout` — see G5).                                   |
| `aec_facade_domain`    | No UC-01 contribution.                                                                                                                                                      |

**SubProperty wiring:**

```
metadata:contains (already exists)
  └── metadata:hasRevision (NEW)

metadata:hasProperty (already exists)
  └── metadata:hasStatusCode (NEW)
```

All other new object properties (`belongsToProject`, `belongsToPackage`, `isAuthoredBy`, `isCheckedBy`, `isApprovedBy`) are declared at the top level — they are associative or role-differentiated and do not fit the "containment" or "characterising property" generalisations.

---

## 8. Open Issues — Pending Team Discussion

These items affect UC-01 but cannot be unilaterally decided in the ORSD; recording for review.

| ID  | Issue                                                                                                                                                              |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| G5  | Should `hasDiscipline` domain move from `LayoutContentType` to `Layout`? v0.3 proposes yes — discipline characterises the layout, not its content type.            |
| G5b | Should `DrawingSheet` itself carry a `hasDiscipline` (a "primary discipline" for the whole sheet) in addition to Layout-level discipline?                          |
| G10 | ~~`:Metadata` class name misleading~~ — **resolved**: renamed to `:MetadataContainer` (team decision). The class models visual supporting regions (titleblock, legend, etc.), not semantic metadata. |
| —   | Project-wide convention for `owl:inverseOf` — when to materialise vs rely on reasoner? v0.3 only materialises `isRevisionOf`.                                      |
| —   | ~~"Civil" discipline~~ — **resolved**: `Civil` to be added as a direct subclass of `dcommon:Discipline` (team decision).                                           |

---

*End of ORSD — UC-01 v 0.3*
