# UC-01: Titleblock-Based Drawing Search

> **Methodology:** LOT (Linked Open Terms) · **Use Case ID:** UC-01 · **Version:** 0.9 (draft) — see [§9 Version History](#9-version-history)

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
| `Person`            | `aec_provenance`                    | NEW    | Authors, checkers, and approvers appear in the titleblock. *(Moved from `aec_drawing_metadata` in [v0.9](#9-version-history).)* |
| `DrawingFile`       | `aec_provenance`                    | NEW    | The file a drawing is stored in: a reference to a document, identified by its content hash. *(Added in [v0.9](#9-version-history).)* |
| `FilePage`          | `aec_provenance`                    | NEW    | One page of a file, counted from 1; the drawing is on a page, not on a file. *(Added in [v0.9](#9-version-history).)* |
| `Discipline`        | `aec_domain_common`                 | REUSE  | Existing class hierarchy (`Structural`, `MEP`, `Architectural`, …).                      |
| `StatusCode`        | `aec_drawing_metadata`              | NEW    | Approval state (IFC, IFR, AFC…) expressed as a controlled vocabulary.                    |
| `DrawingPackage`    | `aec_drawing_metadata`              | NEW    | Drawings are grouped into volumes or packages within a project.                          |

> **Design note — DrawingSheet vs Layout:** A `DrawingSheet` may contain multiple `Layout`s, each with its own `LayoutContentType` and `Discipline`. Queries for "Structural Plan drawings" filter for sheets containing at least one Layout whose content type is `Plan` and whose discipline is (a subclass of) `Structural`.

> **Design note — Titleblock as visual region vs titleblock data:** The existing `metadata:Titleblock` class models the *visual region* on a sheet (for CV annotation). The *information* conventionally found inside it (`drawingIdentifier`, `drawingTitle`, …) is attached as datatype properties directly on `DrawingSheet`. The two layers coexist independently: a sheet has a drawing number whether or not its visual Titleblock region has been bounded in annotation.

> **Design note — `:Metadata` → `:MetadataContainer`:** The existing `:Metadata` class has been renamed to `:MetadataContainer` (team decision). It is the parent of `Titleblock`, `RevisionTable`, `Legend`, and `Note` — i.e. it models *visual supporting regions*, not semantic metadata. The rename avoids confusion with UC-01's datatype properties (`drawingIdentifier`, `drawingTitle`, etc.) on `DrawingSheet`.

> **Design note — DrawingType deprecated:** UC-01 v0.2 introduced `:DrawingType` (Plan, Section, Elevation, Detail, Schedule). This is the same axis as `metadata:LayoutContentType` (Plan, Section, Elevation, Detail, Table, Perspective). "Schedule" maps to `Table`. `DrawingType` is removed in v0.3 — `LayoutContentType` is reused.

> **Design note — Discipline reuse:** UC-01 v0.2 introduced `:Discipline` plus a `:disciplineCode` string property. The existing `dcommon:Discipline` is already a full class hierarchy (`Structural`, `MEP > Mechanical / Electrical > Lighting / Plumbing`, `Architectural > Facade / FireLifeSafety`, `Masterplan`). v0.3 reuses it and drops `:disciplineCode` — discipline filtering uses `rdf:type` checks against the class hierarchy (e.g. `?disc a dcommon:MEP`), which automatically rolls up sub-disciplines via `rdfs:subClassOf` reasoning.

> **Design note — curated values vs extracted assertions:** UC-01 attaches title-block information as datatype properties **directly on `DrawingSheet`** (`drawingIdentifier`, `drawingTitle`, …). That remains correct for a *validated* value. A second, parallel path exists for values that have been **machine-extracted and not yet validated**: an `aprov:FieldAssertion` reifies the claim - what was read, from which region (`assertedBy`), by what (`hasInferenceMeta`), with what confidence, and with the caption exactly as printed (`capturedCaption`) - bound to a field kind in the `TitleblockFieldScheme`. `aprov:mapsToFieldProperty` names the UC-01 property a validated assertion is promoted to. The two coexist: UC-01's properties are the query surface, the assertion layer is the extraction and provenance record. **When a value moves from one to the other, and whether the direct properties eventually deprecate, is open — see §8 (G11).** *(Added in [v0.4](#9-version-history).)*

> **Design note — Person vs Role:** `Person` models what an individual *is*, not the role they play. Roles (Author, Checker, Approver) are expressed as distinct Object Properties, not as subclasses of `Person`. Each applies to a `DrawingSheet` (the person the drawing names, for example the title block's "drawn by") and to a `DrawingRevision` (the person who made, checked or approved that revision, who can differ from the one named for the drawing). This keeps `Person` reusable across roles. A drawing that records no author of its own is read as authored by the authors of its revisions (the path `metadata:isAuthoredBy|metadata:hasRevision/metadata:isAuthoredBy`); a drawing that records its own author keeps just that author, so this is a reading convention and not an OWL entailment. It applies to the author only. *(Amended in [v0.8](#9-version-history).)*

### 2.2 Attributes — Datatype Properties

Characteristics of a single entity. **Datatype properties on `DrawingSheet` are attached directly — no intermediate "metadata container" entity.**

| Attribute        | Entity            | Module                 | Action | Expected Type | Notes |
| ---------------- | ----------------- | ---------------------- | ------ | ------------- | ----- |
| `drawingIdentifier`  | `DrawingSheet`    | `aec_drawing_metadata` | NEW    | `xsd:string`  | Also known as "drawing number". |
| `drawingTitle`   | `DrawingSheet`    | `aec_drawing_metadata` | NEW    | `xsd:string`  | |
| `hasScale`       | `DrawingSheet`, `Layout` | `aec_drawing_metadata` | NEW    | `xsd:string`  | The general scale property; `drawingScale` and `layoutScale` are its sub-properties. With sub-property entailment a query on `hasScale` returns values recorded with either; without it, a sheet's scale is read with the path `metadata:hasScale\|metadata:drawingScale` and a layout's with `metadata:hasScale\|metadata:layoutScale`. *(Amended in [v0.7](#9-version-history).)* |
| `drawingScale`     | `DrawingSheet`    | `aec_drawing_metadata` | NEW    | `xsd:string`  | The scale of the sheet as a whole: most often printed in the title block, also in general notes or other areas outside any layout. Never copied from a layout. Sub-property of `hasScale`. *(Added in [v0.7](#9-version-history).)* |
| `layoutScale`    | `Layout`          | `aec_drawing_metadata` | NEW    | `xsd:string`  | The scale printed in a layout's own caption (or 'NTS' / 'As shown', verbatim); more specific than `drawingScale`; left empty when the layout prints none. Sub-property of `hasScale`. *(Added in [v0.7](#9-version-history).)* |
| `sheetSize`      | `DrawingSheet`    | `aec_drawing_metadata` | NEW    | `xsd:string`  | Named for the sheet of paper, which has a size; also known as "drawing size". *(Noted in [v0.7](#9-version-history).)* |
| `revisionCode`   | `DrawingRevision` | `aec_drawing_metadata` | NEW    | `xsd:string`  | |
| `issueDate`      | `DrawingSheet` or `DrawingRevision` | `aec_drawing_metadata` | NEW    | `xsd:date`    | The date a drawing, or a revision of it, was issued; the title block's date is the drawing's, and "date authored" is the same property. *(Amended in [v0.8](#9-version-history).)* |
| `personName`     | `Person`          | `aec_drawing_metadata` | NEW    | `xsd:string`  | |
| `projectName`    | `Project`         | `aec_drawing_metadata` | NEW    | `xsd:string`  | |
| `projectNumber`  | `Project`         | `aec_drawing_metadata` | NEW    | `xsd:string`  | |
| `packageName`    | `DrawingPackage`  | `aec_drawing_metadata` | NEW    | `xsd:string`  | |
| `statusLabel`    | `StatusCode`      | `aec_drawing_metadata` | NEW    | `xsd:string`  | |

#### Where a scale is printed, and which property records it

| Where the scale is printed | Recorded as | Note |
| -------------------------- | ----------- | ---- |
| In the title block (the "Scale" cell), the usual place | `drawingScale` on the `DrawingSheet` | The sheet's nominal scale. |
| In a general note or another area of the drawing outside the title block and outside any layout ("all drawings 1:50 unless noted") | `drawingScale` on the `DrawingSheet` | Whether such a scale applies to the whole sheet is judged from its context when the value is extracted; that is a matter for extraction, not for the ontology. |
| In a layout's own caption | `layoutScale` on that `Layout` | More specific than the sheet's, and may differ from it (a 1:500 plan on a 1:50 sheet). |
| In the caption of the only layout detected on the sheet | `layoutScale` on that `Layout`, and nothing on the sheet | Not repeated as `drawingScale`. A scale belongs to a drawing view: if more layouts are detected later, a `drawingScale` copied from the first would no longer be true of the sheet. |
| A layout printing "NTS" or "As shown" instead of a ratio | `layoutScale` with that text, verbatim | Tells a layout drawn out of scale apart from one that prints no scale. |
| A layout printing no scale | nothing | `layoutScale` stays empty; the sheet's scale is not written into it. |

What scale applies to a layout is answered by a query (CQ 1.4), not by a stored value: the layout's own `layoutScale` if it has one, otherwise the sheet's scale, reported as "assumed from sheet". The fallback is an assumption (a scale can be missing by mistake), so it is never asserted as a `layoutScale`, which would present an assumption as a printed value. "No scale" (CQ 1.5, CQ 1.6) is a closed-world check: OWL reads a missing value as "not stated", never as an error, so a `someValuesFrom` restriction would only make a reasoner infer that a scale exists. Such checks are queries, or validation shapes in the wider ABox validation work ([#22](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/22)).

### 2.3 Relations — Object Properties

Links between two entities. New properties are wired into the existing generic top-level properties via `rdfs:subPropertyOf`.

| Relation              | Domain            | Range               | Module                 | Action | `subPropertyOf`         |
| --------------------- | ----------------- | ------------------- | ---------------------- | ------ | ----------------------- |
| `contains` (sheet)    | `DrawingSheet`    | `Layout` (1..*)     | `aec_drawing_metadata` | REUSE  | —                       |
| `hasProperty`         | `Layout`          | `LayoutContentType` | `aec_drawing_metadata` | REUSE  | —                       |
| `hasDiscipline` ⚠️    | `Layout`          | `Discipline` (min 1)| `aec_domain_common`    | REUSE¹ | —                       |
| `hasRevision`         | `DrawingSheet`    | `DrawingRevision`   | `aec_drawing_metadata` | NEW    | `metadata:contains`     |
| `belongsToProject`    | `DrawingSheet`    | `Project`           | `aec_drawing_metadata` | NEW    | (top-level)             |
| `assertsProject`      | `Titleblock`      | `Project`           | `aec_drawing_metadata` | NEW    | (top-level)             |
| `belongsToPackage`    | `DrawingSheet`    | `DrawingPackage`    | `aec_drawing_metadata` | NEW    | (top-level)             |
| `assertsPackage`      | `Titleblock`      | `DrawingPackage`    | `aec_drawing_metadata` | NEW    | (top-level)             |
| `isAuthoredBy`           | `DrawingSheet` or `DrawingRevision` | `Person` | `aec_drawing_metadata` | NEW    | (top-level)             |
| `isCheckedBy`          | `DrawingSheet` or `DrawingRevision` | `Person` | `aec_drawing_metadata` | NEW    | (top-level)             |
| `isApprovedBy`         | `DrawingSheet` or `DrawingRevision` | `Person` | `aec_drawing_metadata` | NEW    | (top-level)             |
| `assertsRevision`      | `RevisionTable`   | `DrawingRevision`   | `aec_drawing_metadata` | NEW    | (top-level)             |
| `isOnPage`            | `DrawingSheet`    | `FilePage`          | `aec_drawing_metadata` | NEW    | (top-level)             |
| `belongsToFile`       | `FilePage`        | `DrawingFile`       | `aec_provenance`       | NEW    | (top-level)             |
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
- Derived terms: `metadata:DrawingSheet` (REUSE), `metadata:drawingIdentifier`, `metadata:drawingTitle`, `metadata:hasScale`, `metadata:drawingScale`, `metadata:sheetSize` (NEW datatype properties on `DrawingSheet`); `metadata:layoutScale` (NEW, on `Layout`). `drawingScale` and `layoutScale` are sub-properties of `hasScale`. *(Amended in [v0.7](#9-version-history).)*

---

**FR 2 — Project Membership**

> The ontology MUST represent the relationship between a drawing sheet and the project it belongs to, such that all sheets within a given project can be retrieved as a set.

- Source: UC-01
- Derived terms: `metadata:Project` (NEW), `metadata:belongsToProject` (NEW), `metadata:assertsProject` (NEW, from a `Titleblock` to the project it names), `metadata:projectName`, `metadata:projectNumber` (NEW datatype properties on `Project`)

---

**FR 3 — Revision History and Temporal Metadata**

> The ontology MUST represent multiple revisions of the same drawing sheet as distinct entities, each carrying a revision code, issue date, and status code, such that both the current state and the full revision history of a sheet can be queried.

- Source: UC-01
- Derived terms: `metadata:DrawingRevision` (NEW), `metadata:hasRevision` (NEW, `subPropertyOf metadata:contains`), `metadata:assertsRevision` (NEW, from a `RevisionTable` to each revision it lists), `metadata:revisionCode`, `metadata:issueDate` (NEW)

---

**FR 4 — Role-Differentiated Person Attribution**

> The ontology MUST distinguish between the roles of Author, Checker, and Approver as separate relationships between a person and a drawing, and between a person and a revision of it, such that drawings can be filtered by a specific person in a specific role, and a drawing with no recorded person in a required role can be found.

- Source: UC-01
- Derived terms: `metadata:Person` (NEW), `metadata:isAuthoredBy`, `metadata:isCheckedBy`, `metadata:isApprovedBy` (NEW, top-level), `metadata:personName` (NEW)

> **Design note — inverse properties:** ADIRO declares **no** named inverse properties and no `owl:inverseOf` axioms. Only forward properties are modelled; reverse navigation uses the SPARQL inverse path, e.g. `?rev ^metadata:hasRevision ?sheet`. Decided project-wide in [#21](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/21). *(Changed in [v0.4](#9-version-history).)*

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
- Derived terms: `metadata:DrawingPackage` (NEW), `metadata:belongsToPackage` (NEW), `metadata:assertsPackage` (NEW, from a `Titleblock` to the package it names, when it names one), `metadata:packageName` (NEW)


---

**FR 9 — Source File and Page**

> The ontology MUST say in which file, and on which page of it, a drawing is stored, and identify and locate that file, such that a drawing can be traced to its source, the drawings of a file can be listed, and a file can be found again.

- Source: UC-01 (and every use case that must return to the source of an extraction)
- Derived terms: `aprov:DrawingFile` (NEW), `aprov:FilePage` (NEW), `metadata:isOnPage` (NEW), `aprov:belongsToFile` (NEW), `aprov:pageNumber` (NEW, from 1); the description of a file: `aprov:fileName`, `aprov:storageLocation`, `aprov:contentHash` and `aprov:hashAlgorithm`, `aprov:mediaType`, `aprov:fileCreatedAt`, `aprov:fileModifiedAt`, `aprov:fileCreatedBy`, `aprov:fileModifiedBy`, `aprov:pageCount`, `aprov:fileSize` (all NEW); and of a page: `aprov:displayWidthPt`, `aprov:displayHeightPt`, `aprov:pdfRotationDeg` (moved from the coordinate frame)

> **Design note — drawing, file, page.** A PDF holds many drawings and one drawing can exist in several files, so a drawing is linked to the *page* it is on (`isOnPage`), and the page to its file (`belongsToFile`). The coordinate frame of `aec_geometry` reads a page in one convention (`describesPage`). The measured size of a page is not `sheetSize`, which is the paper format the drawing is meant for. See [the file a drawing is stored in](../../design-decisions/file-and-page-metadata.md). *(Added in [v0.9](#9-version-history).)*
---

## 4. Competency Questions

CQs are grouped by the FR they validate. Each must be translatable directly into a SPARQL query against the term inventory above.

### CQ Group 1 — Drawing Identity (validates FR 1)

| ID     | Competency Question                                              |
| ------ | ---------------------------------------------------------------- |
| CQ 1.1 | What drawing sheets have a drawing number beginning with "ST-"?  |
| CQ 1.2 | What is the title of the sheet with drawing number "ST-101"?     |
| CQ 1.3 | What drawing sheets are drawn at scale 1:50? (Only sheets with a sheet-level scale are returned; a sheet whose only scale is in its single layout's caption is not.) |
| CQ 1.4 | What scale applies to this layout: its own, or otherwise its sheet's? |
| CQ 1.5 | Which drawing sheets state no scale at all? |
| CQ 1.6 | Which layouts have no scale of their own and sit on a sheet with no scale, so that their scale cannot be determined? |
| CQ 1.7 | Which layouts are drawn at a different scale from their sheet? |

### CQ Group 2 — Project Membership (validates FR 2)

| ID     | Competency Question                                                 |
| ------ | ------------------------------------------------------------------- |
| CQ 2.1 | What drawing sheets belong to project "HS 2-N 400"?                 |
| CQ 2.2 | How many drawing sheets are currently registered under project "X"? |
| CQ 2.3 | Which project does the title block of drawing "ST-101" name? *(Added in [v0.8](#9-version-history).)* |
| CQ 2.4 | Which drawings are filed under a project other than the one their title block names? *(Added in [v0.8](#9-version-history).)* |

CQ 2.4 as a query (`assertsProject` is the title block's claim, `belongsToProject` the filing):

```sparql
PREFIX metadata: <https://w3id.org/adiro/aec_drawing_metadata#>

# CQ 2.4: the drawings filed under another project than their title block names
SELECT ?drawing ?named ?filed WHERE {
  ?titleblock a metadata:Titleblock ;
              metadata:assertsMetadataFor ?drawing ;
              metadata:assertsProject     ?named .
  ?drawing metadata:belongsToProject ?filed .
  FILTER (?named != ?filed)
}
```

### CQ Group 3 — Revision History (validates FR 3)

| ID     | Competency Question                                                                         |
| ------ | ------------------------------------------------------------------------------------------- |
| CQ 3.1 | What is the latest revision code of the sheet with drawing number "ST-101"?                 |
| CQ 3.2 | What sheets were issued after 1 January 2024?                                               |
| CQ 3.3 | How many revisions has sheet "ST-101" gone through, and what were their issue dates?        |
| CQ 3.4 | From which revision table was revision "B" of drawing "ST-101" read? *(Added in [v0.8](#9-version-history).)* |

### CQ Group 4 — Role-Differentiated Persons (validates FR 4)

| ID     | Competency Question                                          |
| ------ | ------------------------------------------------------------ |
| CQ 4.1 | What sheets were authored by "J. Smith"?                     |
| CQ 4.2 | What sheets were checked by "A. Chen"?                       |
| CQ 4.3 | For sheet "ST-101 Rev C", who was the approving authority?   |
| CQ 4.4 | Which drawings have no recorded author, neither their own nor a revision's? *(Added in [v0.8](#9-version-history).)* |
| CQ 4.5 | Which drawings have no recorded checker, or no recorded approver? *(Added in [v0.8](#9-version-history).)* |

CQ 3.4 and CQ 4.4 as queries (CQ 4.5 is the same pattern with `isCheckedBy` or `isApprovedBy` alone, without the path through the revisions, which is for the author only):

```sparql
PREFIX metadata: <https://w3id.org/adiro/aec_drawing_metadata#>

# CQ 3.4: the table a revision was read from
SELECT ?table WHERE {
  ?table a metadata:RevisionTable ;
         metadata:assertsRevision ?revision .
  ?revision metadata:revisionCode "B" .
}
```

```sparql
PREFIX metadata: <https://w3id.org/adiro/aec_drawing_metadata#>

# CQ 4.4: the drawings with no recorded author (a revision's author counts when the drawing records none)
SELECT ?drawing WHERE {
  ?drawing a metadata:DrawingSheet .
  FILTER NOT EXISTS { ?drawing metadata:isAuthoredBy|(metadata:hasRevision/metadata:isAuthoredBy) ?person }
}
```

A drawing must have an author; whether it was checked or approved varies, so CQ 4.5 is a plain query and not a check. CQ 4.4 is a closed-world check: the ontology cannot state "every drawing has an author" (an OWL cardinality would infer an author, not report its absence), so the same rule is also a data-validation shape ([#179](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/179)). The query lists the drawings with no recorded person; it cannot say whether the extraction missed the author or the drawing names none (open issue G12).

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
| CQ 8.3 | Which package does the title block of drawing "ST-101" name, if it names one? *(Added in [v0.8](#9-version-history).)* |
| CQ 8.4 | Which drawings are filed in a package other than the one their title block names? *(Added in [v0.8](#9-version-history).)* |

CQ 8.4 as a query (a title block that names no package is not compared):

```sparql
PREFIX metadata: <https://w3id.org/adiro/aec_drawing_metadata#>

# CQ 8.4: the drawings filed in another package than their title block names
SELECT ?drawing ?named ?filed WHERE {
  ?titleblock a metadata:Titleblock ;
              metadata:assertsMetadataFor ?drawing ;
              metadata:assertsPackage     ?named .
  ?drawing metadata:belongsToPackage ?filed .
  FILTER (?named != ?filed)
}
```

### CQ Group 9 — Source File and Page (validates FR 9)

| ID     | Competency Question                                                                  |
| ------ | ------------------------------------------------------------------------------------ |
| CQ 9.1 | In which file, and on which page, is drawing "ST-101" stored? *(Added in [v0.9](#9-version-history).)* |
| CQ 9.2 | Which drawings are in file "A101-ground-floor.pdf"? *(Added in [v0.9](#9-version-history).)* |
| CQ 9.3 | Which files hold more than one drawing? *(Added in [v0.9](#9-version-history).)* |
| CQ 9.4 | Which drawings are in files last modified after 1 January 2026? *(Added in [v0.9](#9-version-history).)* |

CQ 9.1 and CQ 9.3 as queries:

```sparql
PREFIX metadata: <https://w3id.org/adiro/aec_drawing_metadata#>
PREFIX aprov:    <https://w3id.org/adiro/aec_provenance#>

# CQ 9.1: the file and the page of a drawing
SELECT ?fileName ?pageNumber WHERE {
  ?drawing metadata:drawingIdentifier "ST-101" ;
           metadata:isOnPage          ?page .
  ?page aprov:pageNumber ?pageNumber ;
        aprov:belongsToFile ?file .
  ?file aprov:fileName ?fileName .
}
```

```sparql
PREFIX metadata: <https://w3id.org/adiro/aec_drawing_metadata#>
PREFIX aprov:    <https://w3id.org/adiro/aec_provenance#>

# CQ 9.3: the files that hold more than one drawing
SELECT ?file (COUNT(DISTINCT ?drawing) AS ?drawings) WHERE {
  ?drawing metadata:isOnPage ?page .
  ?page aprov:belongsToFile ?file .
}
GROUP BY ?file HAVING (COUNT(DISTINCT ?drawing) > 1)
```

### CQ Group I — Integration / Multi-field Queries

| ID     | Competency Question                                                                                  | FRs exercised               |
| ------ | ---------------------------------------------------------------------------------------------------- | --------------------------- |
| CQ-I 1 | What sheets in project "X" contain a `MEP` Layout and were approved by "R. Jones" after March 2024?  | FR 2, FR 4, FR 5, FR 7      |
| CQ-I 2 | What sheets at scale 1:50 contain a `Structural` Layout and belong to project "Y"? (Only sheets with a sheet-level scale are returned; see CQ 1.3.) | FR 1, FR 2, FR 5            |
| CQ-I 3 | What sheets in project "X" contain a `Structural` Layout of content type `Detail`?                   | FR 2, FR 5, FR 6            |

---

## 5. SPARQL Validation

The following example demonstrates that the term inventory is sufficient to answer integration query CQ-I 1.

**CQ-I 1:** *What sheets in project "X" contain a MEP Layout and were approved by "R. Jones" after March 2024?*

```sparql
PREFIX metadata: <https://w3id.org/adiro/aec_drawing_metadata#>
PREFIX dcommon:  <https://w3id.org/adiro/aec_domain_common#>
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

### Scale competency questions

CQ 1.3 and the scale questions CQ 1.4–1.7 are expressible without a reasoner. Each path lists the parent property together with its sub-property, so values written with either are found whether or not sub-property entailment has been applied: a sheet's scale is read with `(metadata:drawingScale|metadata:hasScale)` and a layout's with `(metadata:layoutScale|metadata:hasScale)`. A sheet's layouts are reached with `metadata:contains`, as in CQ-I 1. The queries were run with rdflib, without a reasoner, on a small example: a sheet with a title-block scale and three layouts (one with its own scale, one with none, one marked "NTS"), a sheet whose scale was written with `hasScale`, a sheet with no scale, and a sheet with a single detected layout.

**CQ 1.3:** *What drawing sheets are drawn at scale 1:50?* Only a sheet with a sheet-level scale is returned: a layout's scale is never copied to its sheet, so a sheet whose only scale is in the caption of its single layout is not returned.

```sparql
PREFIX metadata: <https://w3id.org/adiro/aec_drawing_metadata#>

SELECT ?sheet WHERE {
  ?sheet  a                                         metadata:DrawingSheet ;
          (metadata:drawingScale|metadata:hasScale) "1:50" .
}
```

**CQ 1.4:** *What scale applies to this layout: its own, or otherwise its sheet's?*

```sparql
PREFIX metadata: <https://w3id.org/adiro/aec_drawing_metadata#>

SELECT ?layout ?scale ?basis WHERE {
  ?sheet  a metadata:DrawingSheet ;
          metadata:contains ?layout .
  ?layout a metadata:Layout .
  OPTIONAL { ?layout (metadata:layoutScale|metadata:hasScale)  ?own }
  OPTIONAL { ?sheet  (metadata:drawingScale|metadata:hasScale) ?nominal }
  BIND(COALESCE(?own, ?nominal) AS ?scale)
  BIND(IF(BOUND(?own), "own",
          IF(BOUND(?nominal), "assumed from sheet", "none")) AS ?basis)
}
```

**CQ 1.5:** *Which drawing sheets state no scale at all?*

```sparql
PREFIX metadata: <https://w3id.org/adiro/aec_drawing_metadata#>

SELECT ?sheet WHERE {
  ?sheet a metadata:DrawingSheet .
  FILTER NOT EXISTS { ?sheet (metadata:drawingScale|metadata:hasScale) ?scale }
}
```

**CQ 1.6:** *Which layouts have no scale of their own and sit on a sheet with no scale, so that their scale cannot be determined?*

```sparql
PREFIX metadata: <https://w3id.org/adiro/aec_drawing_metadata#>

SELECT ?layout WHERE {
  ?sheet  a metadata:DrawingSheet ;
          metadata:contains ?layout .
  ?layout a metadata:Layout .
  FILTER NOT EXISTS { ?layout (metadata:layoutScale|metadata:hasScale)  ?own }
  FILTER NOT EXISTS { ?sheet  (metadata:drawingScale|metadata:hasScale) ?nominal }
}
```

**CQ 1.7:** *Which layouts are drawn at a different scale from their sheet?*

```sparql
PREFIX metadata: <https://w3id.org/adiro/aec_drawing_metadata#>

SELECT ?layout ?own ?nominal WHERE {
  ?sheet  a metadata:DrawingSheet ;
          (metadata:drawingScale|metadata:hasScale) ?nominal ;
          metadata:contains ?layout .
  ?layout a metadata:Layout ;
          (metadata:layoutScale|metadata:hasScale) ?own .
  FILTER (?own != ?nominal)
}
```

CQ 1.5 and CQ 1.6 are the closed-world checks for a missing scale (see §2.2).

---

## 6. Traceability Matrix

| OWL Term                       | Module                 | Action | CQ(s)                                          | FR(s)                              |
| ------------------------------ | ---------------------- | ------ | ---------------------------------------------- | ---------------------------------- |
| `metadata:DrawingSheet`        | `aec_drawing_metadata` | REUSE  | CQ 1.x, CQ 2.x, CQ 3.x, CQ 5.x, CQ 6.x, CQ 8.x | FR 1, FR 2, FR 3, FR 5, FR 6, FR 8 |
| `metadata:Layout`              | `aec_drawing_metadata` | REUSE  | CQ 1.4, CQ 1.6, CQ 1.7, CQ 5.x, CQ 6.x, CQ-I 1, CQ-I 2, CQ-I 3         | FR 5, FR 6                         |
| `metadata:LayoutContentType`   | `aec_drawing_metadata` | REUSE  | CQ 6.x, CQ-I 3                                 | FR 6                               |
| `metadata:DrawingRevision`     | `aec_drawing_metadata` | NEW    | CQ 3.x, CQ 4.x, CQ 7.x                         | FR 3, FR 4, FR 7                   |
| `metadata:Project`             | `aec_drawing_metadata` | NEW    | CQ 2.x, CQ-I 1                                 | FR 2                               |
| `metadata:Person`              | `aec_drawing_metadata` | NEW    | CQ 4.x, CQ-I 1                                 | FR 4                               |
| `dcommon:Discipline`           | `aec_domain_common`    | REUSE  | CQ 5.x, CQ-I 1, CQ-I 2, CQ-I 3                 | FR 5                               |
| `metadata:StatusCode`          | `aec_drawing_metadata` | NEW    | CQ 7.x, CQ 8.2                                 | FR 7                               |
| `metadata:DrawingPackage`      | `aec_drawing_metadata` | NEW    | CQ 8.x                                         | FR 8                               |
| `metadata:contains`            | `aec_drawing_metadata` | REUSE  | CQ 1.4, CQ 1.6, CQ 1.7, CQ-I 1, CQ-I 2, CQ-I 3                         | (structural)                       |
| `metadata:hasRevision`         | `aec_drawing_metadata` | NEW    | CQ 3.x                                         | FR 3                               |
| `metadata:isAuthoredBy`           | `aec_drawing_metadata` | NEW    | CQ 4.1, CQ 4.4                                 | FR 4                               |
| `metadata:isCheckedBy`          | `aec_drawing_metadata` | NEW    | CQ 4.2, CQ 4.5                                 | FR 4                               |
| `metadata:isApprovedBy`         | `aec_drawing_metadata` | NEW    | CQ 4.3, CQ 4.5, CQ-I 1                         | FR 4                               |
| `metadata:assertsRevision`      | `aec_drawing_metadata` | NEW    | CQ 3.4                                         | FR 3                               |
| `metadata:hasStatusCode`       | `aec_drawing_metadata` | NEW    | CQ 7.x, CQ 8.2                                 | FR 7                               |
| `metadata:belongsToProject`    | `aec_drawing_metadata` | NEW    | CQ 2.x, CQ-I 1, CQ-I 2, CQ-I 3                 | FR 2                               |
| `metadata:assertsProject`      | `aec_drawing_metadata` | NEW    | CQ 2.3, CQ 2.4                                 | FR 2                               |
| `dcommon:hasDiscipline`        | `aec_domain_common`    | REUSE  | CQ 5.x, CQ-I 1, CQ-I 2, CQ-I 3                 | FR 5                               |
| `metadata:hasProperty`         | `aec_drawing_metadata` | REUSE  | CQ 6.x, CQ-I 3                                 | FR 6                               |
| `metadata:belongsToPackage`    | `aec_drawing_metadata` | NEW    | CQ 8.x                                         | FR 8                               |
| `aprov:DrawingFile`            | `aec_provenance`       | NEW    | CQ 9.2, CQ 9.3                                 | FR 9                               |
| `aprov:FilePage`               | `aec_provenance`       | NEW    | CQ 9.1, CQ 9.3                                 | FR 9                               |
| `metadata:isOnPage`            | `aec_drawing_metadata` | NEW    | CQ 9.1, CQ 9.2, CQ 9.3, CQ 9.4                 | FR 9                               |
| `aprov:belongsToFile`          | `aec_provenance`       | NEW    | CQ 9.1, CQ 9.2, CQ 9.3, CQ 9.4                 | FR 9                               |
| `aprov:fileName`, `aprov:pageNumber` | `aec_provenance` | NEW    | CQ 9.1, CQ 9.2                                 | FR 9                               |
| `aprov:fileModifiedAt`         | `aec_provenance`       | NEW    | CQ 9.4                                         | FR 9                               |
| `aprov:storageLocation`, `aprov:contentHash`, `aprov:hashAlgorithm`, `aprov:mediaType`, `aprov:fileCreatedAt`, `aprov:fileCreatedBy`, `aprov:fileModifiedBy`, `aprov:pageCount`, `aprov:fileSize` | `aec_provenance` | NEW | none yet: they identify, locate and describe the file (the first set of the file brainstorm) | FR 9 |
| `metadata:assertsPackage`      | `aec_drawing_metadata` | NEW    | CQ 8.3, CQ 8.4                                 | FR 8                               |
| `metadata:drawingIdentifier`       | `aec_drawing_metadata` | NEW    | CQ 1.1, CQ 1.2                                 | FR 1                               |
| `metadata:drawingTitle`        | `aec_drawing_metadata` | NEW    | CQ 1.2                                         | FR 1                               |
| `metadata:hasScale`            | `aec_drawing_metadata` | NEW    | CQ 1.3–1.7, CQ-I 2                                 | FR 1                               |
| `metadata:drawingScale`          | `aec_drawing_metadata` | NEW    | CQ 1.3–1.7, CQ-I 2 (directly, or through `hasScale` with entailment) | FR 1                               |
| `metadata:layoutScale`         | `aec_drawing_metadata` | NEW    | CQ 1.4, CQ 1.6, CQ 1.7 (directly, or through `hasScale` with entailment) | FR 1                               |
| `metadata:sheetSize`           | `aec_drawing_metadata` | NEW    | —                                              | FR 1                               |
| `metadata:revisionCode`        | `aec_drawing_metadata` | NEW    | CQ 3.1, CQ 3.3                                 | FR 3                               |
| `metadata:issueDate`           | `aec_drawing_metadata` | NEW    | CQ 3.2, CQ 3.3, CQ-I 1                         | FR 3                               |
| `aprov:Person`                 | `aec_provenance`       | NEW    | CQ 4.x, CQ-I 1                                 | FR 4                               |
| `metadata:personName`          | `aec_drawing_metadata` | NEW    | CQ 4.x, CQ-I 1                                 | FR 4                               |
| `metadata:statusLabel`         | `aec_drawing_metadata` | NEW    | CQ 7.x                                         | FR 7                               |
| `metadata:projectName`         | `aec_drawing_metadata` | NEW    | CQ 2.x                                         | FR 2                               |
| `metadata:projectNumber`       | `aec_drawing_metadata` | NEW    | CQ 2.x                                         | FR 2                               |
| `metadata:packageName`         | `aec_drawing_metadata` | NEW    | CQ 8.x                                         | FR 8                               |

---

## 7. Module Alignment Summary

This section makes the placement of every UC-01 term in the existing module hierarchy explicit, per [PR #15](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/15) review point #2 (@alelom).

**Module hierarchy** *(updated in [v0.6](#9-version-history))*:

```
aec_provenance                      (NEW - foundational, domain-neutral)
        |
        +---- aec_geometry          (NEW - foundational: BoundingBox + CoordinateFrame; imports aec_provenance)
                |
                +---- aec_drawing_metadata
                        |
                        +---- aec_common_symbols       (imports aec_drawing_metadata only)
                        |
                        +---- aec_domain_common        (imports aec_drawing_metadata only)
                                |
                                +---- aec_facade_domain   (also imports aec_drawing_metadata)
```

**Term placement:**

| Module                 | UC-01 contribution                                                                                                                                                          |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `aec_drawing_metadata` | **New classes:** `DrawingRevision`, `Project`, `StatusCode`, `DrawingPackage`. **New properties:** all UC-01 datatype properties; `hasRevision` (⊂ `contains`), `hasStatusCode` (⊂ `hasProperty`), `belongsToProject`, `belongsToPackage`, `isAuthoredBy`, `isCheckedBy`, `isApprovedBy`, `isOnPage`. |
| `aec_provenance`       | **New classes:** `DrawingFile`, `FilePage`, and the agents `Party`, `Person` and `Organisation` (moved here from `aec_drawing_metadata`), with the file and page properties of FR 9. **Reused (new module):** `FieldAssertion`, `InferenceMeta`, `hasConfidence`, `capturedCaption`, `assertedBy`, `inferredBy`/`inferredWith`/`inferredFrom`/`inferredAt`, and the `TitleblockFieldScheme` binding via `assertsFieldKind`. Carries **extracted** title-block values before validation - see the design note in §2.1. |
| `aec_geometry`         | **Reused (new module):** the `Titleblock` region may carry a `BoundingBox` (via `hasBoundingBox`) interpreted by a `CoordinateFrame` (which reads the page the drawing is on, via `describesPage`) — i.e. *where the title block sits on the page*. The extracted field values are read from within that one region and are **not** individually localised. *(Added in [v0.5](#9-version-history).)* |
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

All other new object properties (`belongsToProject`, `belongsToPackage`, `isAuthoredBy`, `isCheckedBy`, `isApprovedBy`, `assertsRevision`, `assertsProject`, `assertsPackage`) are declared at the top level — they are associative or role-differentiated and do not fit the "containment" or "characterising property" generalisations.

---

## 8. Open Issues — Pending Team Discussion

These items affect UC-01 but cannot be unilaterally decided in the ORSD; recording for review.

| ID  | Issue                                                                                                                                                              |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| G5  | Should `hasDiscipline` domain move from `LayoutContentType` to `Layout`? v0.3 proposes yes — discipline characterises the layout, not its content type.            |
| G5b | Should `DrawingSheet` itself carry a `hasDiscipline` (a "primary discipline" for the whole sheet) in addition to Layout-level discipline?                          |
| G11 | **Direct properties vs `FieldAssertion`.** The assertion layer carries extracted, unvalidated title-block values alongside UC-01's direct datatype properties on `DrawingSheet`. Open: at what point does a value get promoted, who performs the promotion, must both representations be kept, and do the direct properties eventually deprecate? Tracked in [#85](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/85). |
| G12 | **A missing person is two different facts.** "The extraction did not find the author" and "the drawing names none" must be told apart (the first is retried or reviewed, the second is a defect of the drawing). Decided: record absence as a value-less `FieldAssertion` with an outcome. Open: the vocabulary, tracked in [#187](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/187) and [#179](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/179). |
| G10 | ~~`:Metadata` class name misleading~~ — **resolved**: renamed to `:MetadataContainer` (team decision). The class models visual supporting regions (titleblock, legend, etc.), not semantic metadata. |
| —   | ~~Project-wide convention for `owl:inverseOf`~~ — **resolved** in [#21](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/21): ADIRO does not declare inverse properties. `isRevisionOf` removed; use `^metadata:hasRevision`. |
| —   | ~~"Civil" discipline~~ — **resolved**: `Civil` to be added as a direct subclass of `dcommon:Discipline` (team decision).                                           |

---

## 9. Version History

### v0.9 (current — draft)

Changes from v0.8, made when the file a drawing is stored in was modelled ([#192](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/192)). MAJOR in substance (entities and relations added, one moved, one removed); the number stays in the 0.x series because the document is still a draft:

- **FR 9 and CQ Group 9 added** (§3, §4): the file a drawing is stored in, and the page of it. `DrawingFile`, `FilePage`, `isOnPage` and `belongsToFile` are new (§2.1, §2.3, §6), with the properties that describe a file and a page; CQ 9.1 and CQ 9.3 are recorded as queries. The design is in [the file a drawing is stored in](../../design-decisions/file-and-page-metadata.md).
- **`Person` moved to `aec_provenance`** (§2.1, §6), with its new parent `Party` and `Organisation`: they are domain-neutral, and a file's creator needs them too. `personName` stays in `aec_drawing_metadata`.
- **`hasCoordinateFrame` removed**: the coordinate frames of a drawing are reached with `isOnPage` and `describesPage`. A region of the drawing stays a `BoundingBox` (`hasBoundingBox`), now stated as a restriction on `MetadataContainer`, on `Layout` and on `DrawingElement`, so the title block, a revision table, a legend, a key plan, a note, a layout and any symbol or component may each carry one.

### v0.8 (draft)

Changes from v0.7, made when the person roles were extended to the drawing and the revision table was linked to its revisions ([#179](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/179), [#69](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/69)). MAJOR in substance (relations re-scoped and added, competency questions added); the number stays in the 0.x series because the document is still a draft:

- **`isAuthoredBy`, `isCheckedBy` and `isApprovedBy` now apply to a `DrawingSheet` as well as a `DrawingRevision`** (§2.3, FR 4, §6). The title block names who drew, checked and approved the drawing; a revision can be made by other people, so the two are different facts and both are kept. The "Person vs Role" note is amended. The domain is the union of the two classes; no cardinality, because an extraction may find nobody (#84). A drawing that records no author is read as authored by its revisions' authors (a path, not an entailment).
- **`assertsRevision` added** (`RevisionTable` to `DrawingRevision`, §2.3, FR 3, §6): one link per row of a printed revision table, so a table with revisions A, B and C asserts three. It records which table a revision was read from; it does not say which revision is the latest (that is read from `issueDate`).
- **`issueDate` applies to a `DrawingSheet` as well as a `DrawingRevision`** (§2.2): the title block's date is the drawing's, and "date authored" is the same property, not a second one.
- **`assertsProject` added** (`Titleblock` to `Project`, §2.3, FR 2, §6) with CQ 2.3 and CQ 2.4: the project a title block names is a claim, and the project a drawing is filed under (`belongsToProject`) is a fact; the two can differ, and CQ 2.4 finds the drawings where they do.
- **`assertsPackage` added** (`Titleblock` to `DrawingPackage`, §2.3, FR 8, §6) with CQ 8.3 and CQ 8.4, on the pattern of `assertsProject`. A title block may or may not name a package, so it is optional (no cardinality, nothing to compare when it names none).
- **CQ 3.4, CQ 4.4 and CQ 4.5 added**, with the queries for CQ 3.4 and CQ 4.4. A drawing must have an author; a checker and an approver are optional. CQ 4.4 is a closed-world check, and the same rule is a data-validation shape.
- **Open issue G12 added**: a missing person is two different facts (not found, not printed); decided in principle, vocabulary open.

### v0.7 (draft)

Changes from v0.6, made when the scale was split into a sheet-level and a layout-level property ([#162](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/162)). MAJOR in substance (attributes added); the number stays in the 0.x series because the document is still a draft:

- **`metadata:drawingScale` (on `DrawingSheet`) and `metadata:layoutScale` (on `Layout`) added** as sub-properties of `metadata:hasScale`, in the §2.2 attributes table, the FR 1 derived terms and the §6 traceability matrix. `drawingScale` is the scale of the sheet as a whole (usually in the title block); `layoutScale` is the scale in a layout's own caption.
- **`hasScale` is unchanged; CQ 1.3 and CQ-I 2 are about the sheet's scale and are answered with or without entailment**: with sub-property entailment a value asserted with `drawingScale` is also a `hasScale` value; without it, the sheet's scale is read with the property path `metadata:hasScale|metadata:drawingScale`. CQ 1.3 and CQ-I 2 are unchanged in substance; their text now states that they return only sheets with a sheet-level scale, so a sheet whose only scale is in its single layout's caption is not returned.
- **Where a scale is printed.** §2.2 gains a table of where a scale is printed and which property records it. `drawingScale` is the scale of the sheet as a whole (the title block is the usual place, and a general note outside any layout also counts, judged from context at extraction); `layoutScale` is the scale in a layout's own caption, "NTS" / "As shown" are recorded verbatim, and a layout that prints no scale gets none. A layout's scale is not copied to the sheet: a scale belongs to a drawing view, and a `drawingScale` taken from the only layout detected would stop being true once more layouts are detected.
- **CQ 1.4–1.7 added** (Group 1): the scale that applies to a layout, sheets with no scale, layouts whose scale cannot be determined, and layouts at a different scale from their sheet. `layoutScale` is now named by CQ 1.4, 1.6 and 1.7. A missing scale is a closed-world check, answered by a query and not by an OWL restriction. §5 gives the SPARQL for CQ 1.3–1.7, run without a reasoner.
- **`sheetSize` naming noted.** `sheetSize` keeps "sheet" because a sheet of paper has a size, while the printed fields say "drawing"; "drawing size" is recorded as a synonym (`skos:altLabel`) so that a second term is not added. No requirement changed.
- **Labelling.** `drawingIdentifier`, `drawingTitle` and `drawingScale` are marked `isComputerVisionLabel`, so annotation tooling can box each as a text field. No requirement changed.

### v0.6 (draft)

Changes from v0.5, made when the unused `owl:imports` of `aec_common_symbols` was removed from `aec_domain_common` and `aec_facade_domain` ([#134](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/134)). MINOR — suite-accuracy only, no UC-01 term changes:

- **§7 module hierarchy corrected.** `aec_common_symbols` and `aec_domain_common` each import `aec_drawing_metadata` only, and `aec_facade_domain` imports `aec_drawing_metadata` and `aec_domain_common`; the earlier diagram drew a single linear chain through `aec_common_symbols`, which was never the import graph.

### v0.5 (draft)

Changes from v0.4, made in [PR #76](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/76) when the `aec_geometry` module was added ([#90](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/90)). MINOR:

- **New foundational module `aec_geometry` added to the §7 module hierarchy** — a second foundational root
  (imports `aec_provenance`), which `aec_drawing_metadata` now imports.
- **`aec_geometry` row added to the §7 term-placement table:** the `Titleblock` region may carry a page
  `BoundingBox` (via `hasBoundingBox`) interpreted by a `CoordinateFrame` (owned by the sheet via
  `hasCoordinateFrame`). Title-block **fields are not individually localised** — only the title block itself
  carries a box.

### v0.4 (draft)

Changes from v0.3, made in [PR #76](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/76) when `aec_provenance` was added to the suite:

- **New design note in §2.1, "curated values vs extracted assertions."** UC-01's datatype properties on
  `DrawingSheet` remain the query surface for a *validated* value; a machine-extracted, not-yet-validated
  value now travels as an `aprov:FieldAssertion` carrying `capturedCaption`, `assertedBy`,
  `hasInferenceMeta` and `hasConfidence`, and is promoted via `aprov:mapsToFieldProperty`.
- **`aec_provenance` row added to the §7 term-placement table.**
- **§7 module hierarchy updated** — `aec_provenance` is a new foundational root above
  `aec_drawing_metadata`.
- **New open issue G11** — when a value is promoted from an assertion to a direct property, and whether the
  direct properties eventually deprecate
  ([#85](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/85)).

- **BREAKING — `metadata:isRevisionOf` removed.** [#21](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/21) decided project-wide that ADIRO declares no
  named inverse properties and no `owl:inverseOf` axioms. Navigate from a revision to its sheet with the
  SPARQL inverse path `^metadata:hasRevision`. The §2.3 relations table, the FR 3 derived terms, the
  traceability matrix and the §7 module table are updated; no competency question changed, and no SPARQL
  validation query in this document used the removed property.

A relation was removed, so this is a **MAJOR** revision in substance; the number stays in the 0.x series
because the document is still a draft and v0.4 was never released.

### v0.3

Aligned with the existing ontology modules (`aec_drawing_metadata`, `aec_domain_common`) per [PR #15](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/15) review (@alelom):

- `Drawing` → `metadata:DrawingSheet`; `Layout` added as a first-class entity (G1).
- `dcommon:hasDiscipline` proposed to move from `LayoutContentType` to `Layout` (G5 — open issue).
- Reuse `dcommon:Discipline` class hierarchy; drop `disciplineCode` string property (G3).
- Reuse `metadata:LayoutContentType`; drop `DrawingType` / `hasDrawingType` / `typeLabel` (G4).
- Datatype properties (`drawingIdentifier`, `drawingTitle`, `hasScale`, `sheetSize`) attached directly to `DrawingSheet` — no intermediate entity (G2).
- New object properties wired into `metadata:contains` / `metadata:hasProperty` via `rdfs:subPropertyOf` (G6).
- SPARQL placeholder namespace replaced with real module prefixes (G8).
- Only `isRevisionOf` materialised as `owl:inverseOf`; other inverses deferred (G9). *(Reversed in v0.4 — no inverse properties are declared at all.)*
- Stray editing artifact on FR 4 removed.
- New §7 Module Alignment Summary added.

### v0.2 and earlier

Predate this changelog.

---

*End of ORSD — UC-01 v 0.3*
