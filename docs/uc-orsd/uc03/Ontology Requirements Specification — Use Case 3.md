# Reference Symbol Cross-Sheet Linking

> **Methodology:** LOT (Linked Open Terms) **Use Case ID:** UC-03 **Version:** 0.2 (draft)
>
> **Changes from v 0.1:** Aligned with existing ontology modules (`aec_drawing_metadata`, `aec_common_symbols`) per @alelom's and @AhmedElnagar1's PR review. Key changes:
> - Fixed: all internal `UC-02` references corrected to `UC-03` (v0.1 used the wrong ID throughout).
> - `Drawing` → `metadata:DrawingSheet`; ReferenceSymbol now mounts on `metadata:Layout` (not on Sheet) — see G1, decision §2.
> - The class for cross-sheet linking symbols is introduced in `aec_common_symbols`. Its **scope** is confirmed (Detail / Section / Elevation markers and similar cross-sheet linkers); its **name** (`ReferenceSymbol`, `Callout`, or an alternative) and its relationship to the existing `csymbol:Callout` class are left for team review — see Open Issue UC03-1.
> - **ReferenceSymbol is a pure relational node** — zero datatype properties. v0.1's `symbolLabel`, `symbolNumber`, and `SymbolType` / `hasSymbolType` / `typeLabel` all removed; see decisions §3–§5 and the *design-debate* note.
> - `hasReferenceSymbol` wired via `rdfs:subPropertyOf metadata:contains` (G6).
> - SPARQL placeholder namespace replaced with real module prefixes (G8).
> - CQ groups consolidated from 5 → 3 (Discovery / Navigation / Network) per @AhmedElnagar1's "competency questions repeat themselves".
> - Identified cross-UC dependency: UC-03 needs `metadata:layoutIdentifier`, which properly belongs in UC-01 v0.4 — flagged in Open Issues.

---

## 1. Use Case

| Field             | Content                                                                                                                                                                                                                                              |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **ID**            | UC-03                                                                                                                                                                                                                                                |
| **Title**         | Reference Symbol Cross-Sheet Linking                                                                                                                                                                                                                 |
| **Statement**     | As a designer, I want to navigate between a drawing and all drawings connected to it through reference symbols — such as Detail Markers, Section Markers, and Elevation Markers — so that I can trace how a building element is documented across sheets and drawing sets in both directions. |
| **Primary Actor** | Designer                                                                                                                                                                                                                                             |
| **Goal**          | Given any drawing sheet (or specific Layout within it), retrieve the complete set of Layouts linked to it through reference symbols, navigable in both directions: outgoing (what this drawing references) and incoming (what references this drawing). |

> **Terminology note:** Where v0.1 used "Drawing" as the atomic linked unit, v0.2 distinguishes between the user-facing "drawing" (= `metadata:DrawingSheet`) and the semantically-precise link target (= `metadata:Layout`). Reference Symbols link Layouts to Layouts, not whole sheets to whole sheets — the marker "2/ST-201" precisely identifies *view 2 on sheet ST-201*, a specific Layout.

---

## 2. Information Needs Analysis

### 2.1 Entities

| Entity                   | Module                 | Action | Rationale                                                                                                                              |
| ------------------------ | ---------------------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| `DrawingSheet`           | `aec_drawing_metadata` | REUSE  | Parent container of the Layouts being linked. Carries `drawingIdentifier`. UC-01 owns this.                                                |
| `Layout`                 | `aec_drawing_metadata` | REUSE  | The actual unit linked at both ends of a ReferenceSymbol. Carries `layoutIdentifier`.                                                      |
| `LayoutContentType`      | `aec_drawing_metadata` | REUSE  | Plan / Section / Detail / Elevation / Table / Perspective. UC-03 derives a ReferenceSymbol's "type" from the target Layout's content type. |
| `ReferenceSymbol`        | `aec_common_symbols`   | NEW (see UC03-1 re naming) | The linking entity itself — a `metadata:DrawingElement` subclass drawn on a source Layout, pointing to a target Layout. |

> **Design note — Naming and relationship with the existing `Callout` class.** The existing `csymbol:Callout` is defined as "a callout or detail marker that references another part of the drawing or a detail view" — semantically very close to UC-03's cross-sheet linker. UC-03 uses the working name `ReferenceSymbol` in this document, but the final class name and its relationship to `Callout` (replacement, rename, supertype/subtype, or retention of both with distinct scopes) is left for team review — see Open Issue UC03-1. The *scope* described here (Detail / Section / Elevation markers and similar cross-sheet linkers) is agreed regardless of the naming outcome.

> **Design note — Layout-level mounting.** v0.1 had ReferenceSymbol link `Drawing → Drawing`. v0.2 links `Layout → Layout`: a marker like "2/ST-201" specifies view 2 on sheet ST-201, a specific Layout. Layout-level mounting also keeps ReferenceSymbol architecturally consistent with `Dimension`, `Grid`, and other `DrawingElement` subclasses, which are all contained by Layout, not Sheet.

> **Design note — ReferenceSymbol is a pure relational node.** No datatype properties. v0.1's `symbolLabel` ("2/ST-201") is derivable via `CONCAT`. v0.1's `symbolNumber` ("2") equals the target Layout's `layoutIdentifier` under mainstream NCS / AIA / BS drafting conventions, and is therefore derivable by graph traversal. RDF URIs handle instance uniqueness — multiple identical markers (e.g. three Detail Markers at three locations all reading "2/ST-201") are distinct URIs, not distinct datatype values. See the design-debate note for the full reasoning, including the "RDF identity vs domain identity" distinction.

> **Design note — `:hasLocation → LayoutRegion` still deferred.** Position-level differentiation among identical markers (the only mechanism that would distinguish three "2/ST-201" markers at three places on the same Plan) belongs to a future geometric-layer extension. If a CQ ever requires this, the correct response is to promote `:hasLocation` to UC-03 core, not to re-introduce a string-keyed identifier.

### 2.2 Attributes — Datatype Properties

| Attribute       | Entity            | Module                 | Action | Expected Type | Notes                                                                                              |
| --------------- | ----------------- | ---------------------- | ------ | ------------- | -------------------------------------------------------------------------------------------------- |
| `drawingIdentifier` | `DrawingSheet`    | `aec_drawing_metadata` | REUSE  | `xsd:string`  | Owned by UC-01 v0.3.                                                                                |
| `layoutIdentifier`  | `Layout`          | `aec_drawing_metadata` | NEW¹   | `xsd:string`  | The number assigned to a Layout in its title strip (e.g. the "2" in "SECTION 2 — SCALE 1:50"). Together with the parent sheet's `drawingIdentifier`, uniquely addresses a Layout. |

¹ **Cross-UC dependency.** UC-03 needs `layoutIdentifier` to resolve composite reference labels like "2/ST-201", but as an identity field it properly belongs in UC-01's domain. To be formally introduced in **UC-01 v0.4** (FR 1 — identity fields extension). UC-03 references it as if already present; v0.2 will be re-finalised once UC-01 v0.4 lands.

**ReferenceSymbol has no datatype properties.** See the design-debate note for why `symbolNumber`, `symbolLabel`, and `typeLabel` were all rejected.

### 2.3 Relations — Object Properties

| Relation              | Domain            | Range             | Module                 | Action | `subPropertyOf`         |
| --------------------- | ----------------- | ----------------- | ---------------------- | ------ | ----------------------- |
| `contains` (sheet)    | `DrawingSheet`    | `Layout`          | `aec_drawing_metadata` | REUSE  | —                       |
| `hasReferenceSymbol`  | `Layout`          | `ReferenceSymbol` | `aec_common_symbols`   | NEW    | `metadata:contains`     |
| `appearsOn`           | `ReferenceSymbol` | `Layout`          | `aec_common_symbols`   | NEW    | (inverse of `hasReferenceSymbol`) |
| `referencesLayout`    | `ReferenceSymbol` | `Layout`          | `aec_common_symbols`   | NEW    | (top-level)             |
| `isReferencedBy`      | `Layout`          | `ReferenceSymbol` | `aec_common_symbols`   | NEW    | (inverse of `referencesLayout`) |

> **Design note — inverse properties.** `owl:inverseOf` is declared for both forward/reverse pairs (`hasReferenceSymbol`/`appearsOn` and `referencesLayout`/`isReferencedBy`). Instance data asserts only one direction; the inverse direction is available via reasoner or SPARQL property-path expansion. This matches the project's tentative convention (cf. UC-01's open issue on inverse-property declaration).

---

## 3. Functional Requirements

**Obligation levels:** MUST = mandatory for current scope; SHOULD = important but deferrable; MAY = optional extension.

---

**FR 1 — Reference Symbol as a First-Class Entity**

> The ontology MUST represent Reference Symbols as distinct entities, each a subclass of `metadata:DrawingElement`, such that the linking relationship between Layouts is expressed through an intermediate node rather than a direct property between two Layouts (or two Sheets).

- Source: UC-03
- Derived terms: `csymbol:ReferenceSymbol` (NEW; working name — see Open Issue UC03-1 for final naming decision)
- Note: ReferenceSymbol carries no datatype properties. Instance identity is handled by RDF URI; all visible information (marker label, target view, target sheet) is derivable from the relational links and the target's own identity fields.

---

**FR 2 — Source Layout Association**

> The ontology MUST represent the relationship between a Reference Symbol and the Layout on which it is drawn, such that all reference symbols present on a given Layout (and, transitively, on a given DrawingSheet) can be retrieved.

- Source: UC-03
- Derived terms: `csymbol:appearsOn`, `csymbol:hasReferenceSymbol` (NEW; `hasReferenceSymbol ⊂ metadata:contains`)

---

**FR 3 — Target Layout Association**

> The ontology MUST represent the relationship between a Reference Symbol and the Layout it references, such that the target Layout (and, transitively, the target Sheet) can be identified from any given Reference Symbol.

- Source: UC-03
- Derived terms: `csymbol:referencesLayout`, `csymbol:isReferencedBy` (NEW)

---

**FR 4 — Bidirectional Navigation**

> The ontology MUST support navigation in both directions: from a source Layout/Sheet to all Layouts it references through its symbols, and from a referenced Layout/Sheet back to all source Layouts/Sheets that contain a symbol pointing to it.

- Source: UC-03
- Derived terms: `owl:inverseOf` declarations linking `hasReferenceSymbol`/`appearsOn` and `referencesLayout`/`isReferencedBy`

---

**FR 5 — Composite-Label Resolution**

> The ontology MUST support resolving a composite marker label of the form `"<symbol number>/<sheet number>"` (e.g. `"2/ST-201"`) to a specific target Layout, given the existence of `metadata:layoutIdentifier` (per UC-01 v0.4) and `metadata:drawingIdentifier` (per UC-01 v0.3).

- Source: UC-03
- Derived terms: none new — uses existing identity fields
- Note: The composite label itself is not stored. Resolution is performed at query time: parse the label, look up the DrawingSheet by `drawingIdentifier`, then locate the Layout within it by `layoutIdentifier`.

---

**FR 6 — Cross-Package Linking** — MAY

> The ontology MAY support linking across drawing packages, such that a reference symbol on a Layout in one package can reference a Layout that belongs to a different package.

- Source: UC-03
- Obligation: MAY — optional extension
- Note: `DrawingPackage` is already a first-class entity in UC-01 v0.3 (FR 8), and `DrawingSheet` carries `belongsToPackage`. This FR is therefore **passively satisfied**: `csymbol:referencesLayout` has no same-package restriction. No additional modelling is required. Cross-package navigation is available via the existing traversal `ReferenceSymbol → referencesLayout → Layout ← contains ← DrawingSheet → belongsToPackage → DrawingPackage`.

---

*(FR 2 from v0.1 — Symbol Type Classification — is removed in v0.2. Symbol type is derivable from the target Layout's `LayoutContentType`: a Detail Marker points at a `Detail`, a Section Marker at a `Section`, etc. See decision §3 below.)*

---

## 4. Competency Questions

CQs are grouped by their query *shape* (consolidated from v0.1's five overlapping groups into three coherent groups per @AhmedElnagar1's review).

### CQ Group 1 — Discovery (validates FR 1, FR 2)

What reference symbols exist on a given source, and what (broadly) do they point to?

| ID     | Competency Question                                                              |
| ------ | -------------------------------------------------------------------------------- |
| CQ 1.1 | What reference symbols appear on sheet "GA-001"?                                 |
| CQ 1.2 | How many reference symbols appear on sheet "GA-001"?                             |
| CQ 1.3 | What Detail Markers (i.e. symbols whose target Layout is a `Detail`) appear on sheet "GA-001"? |
| CQ 1.4 | What types of reference symbols are used across project "X"? (i.e. what `LayoutContentType`s do its symbols target?) |

### CQ Group 2 — Navigation (validates FR 3, FR 5)

Given a marker (or its composite label), where does it lead?

| ID     | Competency Question                                                                                |
| ------ | -------------------------------------------------------------------------------------------------- |
| CQ 2.1 | Which Layout is referenced by the symbol whose composite label is "2/ST-201"?                      |
| CQ 2.2 | Which drawings reference the Detail at "2/ST-201"? *(rephrased per @AhmedElnagar1: "Which drawings reference this detail sheet?")* |

### CQ Group 3 — Network (validates FR 4)

Bidirectional reachability around a given Sheet or Layout.

| ID     | Competency Question                                                                                                |
| ------ | ------------------------------------------------------------------------------------------------------------------ |
| CQ 3.1 | What Layouts are referenced by sheet "GA-001" through its reference symbols? (outgoing)                            |
| CQ 3.2 | Which Layouts contain a reference symbol pointing to a Layout on sheet "ST-201"? (incoming)                        |
| CQ 3.3 | What is the complete set of Sheets connected to sheet "GA-001" through reference symbols in either direction?      |

### CQ Group I — Integration / Multi-field Queries

| ID     | Competency Question                                                                          | FRs exercised                       |
| ------ | -------------------------------------------------------------------------------------------- | ----------------------------------- |
| CQ-I 1 | What Section views in project "X" are referenced from sheet "GA-001"?                        | FR 3, UC-01/FR 2, UC-01/FR 6        |
| CQ-I 2 | Which sheets in project "X" contain markers pointing at any Detail on sheet "ST-201"?         | FR 2, FR 3, UC-01/FR 2              |

---

## 5. SPARQL Validation

**CQ 3.3:** *What is the complete set of sheets connected to sheet "GA-001" through reference symbols in either direction?*

```sparql
PREFIX metadata: <https://burohappoldmachinelearning.github.io/ADIRO/aec_drawing_metadata#>
PREFIX csymbol:  <https://burohappoldmachinelearning.github.io/ADIRO/aec_common_symbols#>

SELECT DISTINCT ?connectedSheet WHERE {
  ?GA001 metadata:drawingIdentifier "GA-001" ;
         metadata:contains      ?sourceLayout .

  {
    # Outgoing: layouts on GA-001 that reference something
    ?sourceLayout csymbol:hasReferenceSymbol ?sym .
    ?sym          csymbol:referencesLayout  ?targetLayout .
    ?connectedSheet metadata:contains        ?targetLayout .
  }
  UNION
  {
    # Incoming: someone else's layout has a symbol pointing into GA-001
    ?sourceLayout csymbol:isReferencedBy ?sym .
    ?sym          csymbol:appearsOn      ?otherLayout .
    ?connectedSheet metadata:contains    ?otherLayout .
  }

  FILTER(?connectedSheet != ?GA001)
}
```

Notes:
- The placeholder `https://example.org/aec-ontology#` from v0.1 is retired in favour of the real module namespaces.
- Both directions are expressible using the defined properties. Inverse properties are exercised symmetrically.
- The query traverses Sheet → Layout → ReferenceSymbol → Layout → Sheet at both ends, demonstrating that Layout-level mounting (decision §2) does not obstruct sheet-level user queries — sheet-level results emerge from a single extra hop.

**CQ 2.1 (composite-label resolution) example:**

```sparql
PREFIX metadata: <https://burohappoldmachinelearning.github.io/ADIRO/aec_drawing_metadata#>
PREFIX csymbol:  <https://burohappoldmachinelearning.github.io/ADIRO/aec_common_symbols#>

# Given composite label "2/ST-201":
SELECT ?targetLayout WHERE {
  ?targetSheet  metadata:drawingIdentifier "ST-201" ;
                metadata:contains      ?targetLayout .
  ?targetLayout metadata:layoutIdentifier  "2" .
}
```

This demonstrates FR 5: composite labels are parsed at query time, not stored on the symbol.

---

## 6. Traceability Matrix

| OWL Term                       | Module                 | Action | CQ(s)                                | FR(s)            |
| ------------------------------ | ---------------------- | ------ | ------------------------------------ | ---------------- |
| `metadata:DrawingSheet`        | `aec_drawing_metadata` | REUSE  | CQ 1.x, CQ 3.x, CQ-I 1, CQ-I 2       | (structural)     |
| `metadata:Layout`              | `aec_drawing_metadata` | REUSE  | CQ 1.x, CQ 2.x, CQ 3.x, CQ-I 1, CQ-I 2 | FR 2, FR 3, FR 5 |
| `metadata:LayoutContentType`   | `aec_drawing_metadata` | REUSE  | CQ 1.3, CQ 1.4, CQ-I 1               | (derives type)   |
| `csymbol:ReferenceSymbol`      | `aec_common_symbols`   | NEW    | CQ 1.x, CQ 2.x, CQ 3.x, CQ-I 1, CQ-I 2 | FR 1             |
| `metadata:contains`            | `aec_drawing_metadata` | REUSE  | CQ 1.x, CQ 3.x, CQ-I 1, CQ-I 2       | (structural)     |
| `csymbol:hasReferenceSymbol`   | `aec_common_symbols`   | NEW    | CQ 1.x, CQ 3.x                       | FR 2             |
| `csymbol:appearsOn`            | `aec_common_symbols`   | NEW    | CQ 3.2, CQ 3.3                       | FR 2             |
| `csymbol:referencesLayout`    | `aec_common_symbols`   | NEW    | CQ 2.x, CQ 3.x, CQ-I 1, CQ-I 2       | FR 3             |
| `csymbol:isReferencedBy`       | `aec_common_symbols`   | NEW    | CQ 3.2, CQ 3.3                       | FR 4             |
| `metadata:drawingIdentifier`       | `aec_drawing_metadata` | REUSE  | CQ 2.x                               | FR 5 (UC-01 v0.3) |
| `metadata:layoutIdentifier`        | `aec_drawing_metadata` | NEW¹   | CQ 2.x                               | FR 5 (pending UC-01 v0.4) |

---

## 7. Module Alignment Summary

Per the project's import hierarchy and @alelom's cross-cutting review point #2, every UC-03 term is placed in its proper module.

**Module hierarchy** (unchanged):

```
aec_drawing_metadata
        |
        +---- aec_common_symbols
                |
                +---- aec_domain_common
                        |
                        +---- aec_facade_domain
```

**UC-03 term placement:**

| Module                 | UC-03 contribution                                                                                                                                                  |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `aec_drawing_metadata` | **New (cross-UC dependency):** `layoutIdentifier` — properly belongs to UC-01 v0.4. **Reused:** `DrawingSheet`, `Layout`, `LayoutContentType`, `contains`, `drawingIdentifier`. |
| `aec_common_symbols`   | **New classes:** `ReferenceSymbol` (replaces `Callout`). **New properties:** `hasReferenceSymbol` (⊂ `metadata:contains`), `appearsOn`, `referencesLayout`, `isReferencedBy`. |
| `aec_domain_common`    | No UC-03 contribution.                                                                                                                                              |
| `aec_facade_domain`    | No UC-03 contribution.                                                                                                                                              |

**Subproperty wiring:**

```
metadata:contains (existing)
  └── csymbol:hasReferenceSymbol (NEW)
```

`appearsOn`, `referencesLayout`, and `isReferencedBy` remain top-level — they are navigational/relational, not "containment-like".

---

## 8. Open Issues — Pending Team Discussion

These items affect UC-03 but cannot be unilaterally decided in the ORSD.

| ID    | Issue                                                                                                                                                                                                                                       |
| ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| UC03-1 | **Naming and relationship: `ReferenceSymbol` vs `Callout`.** The *scope* of UC-03's cross-sheet linking class is agreed. The **name** is open: (a) keep `ReferenceSymbol` as introduced here; (b) rename the existing `Callout` to `ReferenceSymbol`; (c) keep both with distinct scopes (Callout = same-sheet annotation pointer; ReferenceSymbol = cross-sheet linker); (d) introduce a broader supertype (e.g. `AnnotationSymbol`) above both. Decision for @alelom / @AhmedElnagar1 with reference to the broader `aec_common_symbols` module design. |
| UC03-2 | **`layoutIdentifier` belongs in UC-01.** UC-03 introduces it provisionally. UC-01 v0.4 should formally adopt it as an identity-fields extension; UC-03 v0.2 will be re-finalised at that point.                                                  |
| UC03-3 | **Optional geometric-layer extension (GeoSPARQL).** If a CQ ever demands distinguishing multiple identical markers at different positions on the same source Layout, or precise spatial queries over Layout bounds, the preferred approach is a GeoSPARQL extension: add `geo:hasGeometry` to both `ReferenceSymbol` (point — symbol centre on its source Layout) and `Layout` (polygon — bounding rectangle on the DrawingSheet), using a drawing-local coordinate CRS. This is a better long-term option than a custom `LayoutRegion` class: standard OGC vocabulary, built-in spatial SPARQL functions (`geof:sfWithin` etc.), and interoperability with BIM/IFC spatial data. *Subject* of `hasLocation`-style triples would be `ReferenceSymbol`. Prerequisite: verify the target SPARQL engine's support for custom (non-geographic) CRS. No current CQ requires this; defer until a geometric use case is confirmed. |
| UC03-4 | **Match Lines and other reference symbol types.** Industry usage extends beyond Detail/Section/Elevation markers (Match Lines for split-sheet continuation, Schedule references, Key Plan references, etc.). UC-03's current scope covers the three primary types; broader coverage may need additional modelling if a CQ requires it. |
| UC03-5 | **Sheet-level references (backlog).** UC-03's `referencesLayout` only covers graphical markers (Detail / Section / Elevation Markers), which by definition point to a specific Layout. If a future case arises where a graphical marker refers to an entire DrawingSheet rather than a specific Layout, the ontology may need a `referencesSheet` property or equivalent. Note: textual whole-sheet references ("See drawing ST-201") are already covered by the existing `metadata:TextualNote.refersToDrawingId` and are outside UC-03's scope. |
| —     | **Inverse-property convention** (project-wide, not UC-03-specific): when to declare `owl:inverseOf` vs rely on a reasoner? UC-03 declares inverses for both forward/reverse pairs. UC-01 v0.3 only materialises `isRevisionOf`. The two should be reconciled. |

---

## 9. Design Decisions — Reasoning Index

For the full design-debate reasoning behind the v0.2 modelling choices, see the accompanying *UC-03 Design Debate* note. The key decisions, in summary:

1. **§1 — Ontology role:** This ontology is a **query layer**, not a raw-storage layer. Parsing, OCR clean-up, and provenance live upstream/elsewhere.
2. **§2 — Layout-level mounting:** Both ends of a ReferenceSymbol link `Layout → Layout`, not `Sheet → Sheet`. Better precision; aligns with the existing DrawingElement architecture.
3. **§3 — No `SymbolType`:** Marker type (Detail / Section / Elevation) is derivable from the target Layout's `LayoutContentType`. FR 2 from v0.1 removed.
4. **§4 — No `symbolLabel`:** The composite label "2/ST-201" is derivable via `CONCAT(symbolNumber, "/", targetSheet.drawingIdentifier)`.
5. **§5 — No `symbolNumber`:** Under mainstream NCS / AIA / BS conventions, the number inside a marker bubble equals the target Layout's `layoutIdentifier` — derivable by graph traversal. ReferenceSymbol becomes a pure relational node.
6. **§6 — Reusable principle:** *"The ontology models facts, not their display derivatives."* Three-step check for any new datatype property — derivability test, independent-assertion test, optimisation warning.
7. **§7 — RDF identity ≠ domain identity:** Instance uniqueness is provided by RDF URI, never by adding a datatype property. Multiple identical markers are distinct URIs, not distinct values.

---

*End of ORSD — UC-03 v 0.2*
