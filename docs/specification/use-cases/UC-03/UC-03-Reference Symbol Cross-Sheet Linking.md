# UC-03: Reference Symbol Cross-Sheet Linking

> **Methodology:** LOT (Linked Open Terms) · **Use Case ID:** UC-03 · **Version:** 0.5 (semantic extension implemented on this branch, pending review — see [§8](#8-open-issues-pending-team-discussion) for deferred items, [§10](#10-version-history) for changelog)

---

## 1. Use Case

| Field             | Content                                                                                                                                                                                                                                              |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **ID**            | UC-03                                                                                                                                                                                                                                                |
| **Title**         | Reference Symbol Cross-Sheet Linking                                                                                                                                                                                                                 |
| **Statement**     | As a designer, I want to discover accepted connections between drawings through graphical reference symbols and evidenced inline or standalone sheet references, so that I can trace how a building element is documented across sheets and drawing sets in both directions. |
| **Primary Actor** | Designer                                                                                                                                                                                                                                             |
| **Goal**          | Given a drawing sheet or Layout, retrieve accepted target Layouts reached through graphical markers and accepted sheet/layout targets reached through evidenced textual references; keep outgoing and incoming source relationships queryable. |

> **Terminology note:** A `DrawingSheet` and its `Layout` are target identities, while a `SheetNoMention` is one occurrence of source text. Graphical symbols normally reference a specific Layout, such as view 2 on ST-201. An evidenced standalone sheet-number reference may denote a DrawingSheet without claiming a Layout target or an emitted PDF link. *(Amended in [v0.5](#10-version-history).)*

---

## 2. Information Needs Analysis

### 2.1 Entities

| Entity                   | Module                 | Action | Rationale                                                                                                                              |
| ------------------------ | ---------------------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| `DrawingSheet`           | `aec_drawing_metadata` | REUSE  | Parent container of the Layouts being linked. Carries `drawingIdentifier`. UC-01 owns this.                                                |
| `Layout`                 | `aec_drawing_metadata` | REUSE  | The source/target view for a graphical symbol and an accepted target for an inline reference. Carries `layoutIdentifier`. |
| `LayoutContentType`      | `aec_drawing_metadata` | REUSE  | Plan / Section / Detail / Elevation / Table / Perspective. UC-03 can derive a ReferenceSymbol's type when its target Layout is accepted. |
| `ReferenceSymbol`        | `aec_common_symbols`   | REUSE | A graphical linking entity drawn on a source Layout and pointing to an accepted target Layout. |
| `ReferenceExpression` | `aec_drawing_metadata` | NEW | Common type for a complete graphical, inline or standalone reference; no extra wrapper individual is required. |
| `SheetNoMention` / `LayoutNoMention` | `aec_drawing_metadata` | NEW | Distinct, evidenced occurrences of source number text, separate from target identities. |
| `InlineLayoutSheetReference` | `aec_drawing_metadata` | NEW | One complete inline expression, possibly with several layout-number components and accepted target Layouts. |
| `StandaloneSheetReference` | `aec_drawing_metadata` | NEW | One occurrence typed as both `SheetNoMention` and `ReferenceExpression`. |

> **Design note — graphical symbols and text.** `csymbol:ReferenceSymbol` is the established class for graphical cross-sheet markers. `metadata:ReferenceExpression` now groups it with inline and standalone textual forms for source-reference queries. A graphical marker is still a `metadata:DrawingElement`; its accepted `csymbol:referencesLayout` target remains Layout-level. *(Amended in [v0.5](#10-version-history).)*

> **Design note — Layout-level mounting.** v0.1 had ReferenceSymbol link `Drawing → Drawing`. v0.2 links `Layout → Layout`: a marker like "2/ST-201" specifies view 2 on sheet ST-201, a specific Layout. Layout-level mounting also keeps ReferenceSymbol architecturally consistent with `Dimension`, `Grid`, and other `DrawingElement` subclasses, which are all contained by Layout, not Sheet.

> **Design note — resolved identity and source evidence.** `ReferenceSymbol` still has no raw-text datatype property. Its accepted target can supply a display label, but that derived label does not replace the text actually printed on the source. Keep source text, localisation and extraction decisions in evidence; whether a direct raw-text term belongs on the symbol remains open in [#20](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/20). Separate source occurrences retain separate RDF identities even when they display the same number. *(Amended in [v0.5](#10-version-history).)*

> **Design note — localisation.** Source occurrences need evidence locating them on the original PDF. The shared `aec_geometry` module supplies `BoundingBox` and `CoordinateFrame`; UC-03 geometry roles and output navigation regions are tracked in [#93](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/93). The semantic classes here do not invent a `LayoutRegion` or require a geometry by OWL cardinality. *(Amended in [v0.5](#10-version-history).)*

### 2.2 Attributes — Datatype Properties

| Attribute       | Entity            | Module                 | Action | Expected Type | Notes                                                                                              |
| --------------- | ----------------- | ---------------------- | ------ | ------------- | -------------------------------------------------------------------------------------------------- |
| `drawingIdentifier` | `DrawingSheet`    | `aec_drawing_metadata` | REUSE  | `xsd:string`  | Owned by UC-01 v0.3.                                                                                |
| `layoutIdentifier`  | `Layout`          | `aec_drawing_metadata` | REUSE | `xsd:string` | The number assigned to a Layout in its title strip (e.g. the "2" in "SECTION 2 — SCALE 1:50"); interpreted in the context of its parent DrawingSheet. |

`layoutIdentifier` already exists in `aec_drawing_metadata`; UC-03 reuses it to distinguish Layouts within a target DrawingSheet.

**ReferenceSymbol currently has no datatype properties.** Direct storage of source text remains under discussion in [#20](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/20); the target-derived display label is not a substitute for original evidence.

The new mention classes likewise add no raw-text datatype property. Text, character spans and candidate
decisions remain in immutable source evidence; an accepted target edge is asserted only after resolution.

### 2.3 Relations — Object Properties

| Relation              | Domain            | Range             | Module                 | Action | `subPropertyOf`         |
| --------------------- | ----------------- | ----------------- | ---------------------- | ------ | ----------------------- |
| `hasLayout`            | `DrawingSheet`    | `Layout`          | `aec_drawing_metadata` | REUSE  | `metadata:contains`     |
| `hasReferenceSymbol`  | `Layout`          | `ReferenceSymbol` | `aec_common_symbols`   | NEW    | `metadata:contains`     |
| `referencesLayout`    | `ReferenceSymbol` | `Layout`          | `aec_common_symbols`   | NEW    | (top-level)             |
| `hasSheetNoMention` / `hasLayoutNoMention` | `ReferenceExpression` | `SheetNoMention` / `LayoutNoMention` | `aec_drawing_metadata` | NEW | `metadata:contains` |
| `denotesDrawingSheet` | `SheetNoMention` | `DrawingSheet` | `aec_drawing_metadata` | NEW | (top-level) |
| `inlineAppearsOn` | `InlineLayoutSheetReference` | `Layout` | `aec_drawing_metadata` | NEW | (top-level) |
| `inlineReferencesLayout` | `InlineLayoutSheetReference` | `Layout` | `aec_drawing_metadata` | NEW | (top-level) |

> **Design note — inverse properties.** ADIRO declares **no** named inverse properties and no `owl:inverseOf` axioms. Only the forward direction of each pair is modelled: `hasReferenceSymbol` (Layout → ReferenceSymbol, ⊂ `metadata:contains`) and `referencesLayout` (ReferenceSymbol → Layout). Reverse navigation uses the SPARQL inverse path, e.g. `?sym ^csymbol:hasReferenceSymbol ?layout`, or simply reads the forward triple in the other direction. Decided project-wide in [#21](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/21). *(Changed in [v0.3](#10-version-history).)*

`csymbol:referencesLayout` keeps its symbol-only domain; inline targets use `metadata:inlineReferencesLayout`.
`metadata:denotesDrawingSheet` resolves a text occurrence's sheet identity without introducing the general
`referencesSheet` relation deferred in [#38](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/38).
See the [semantic design note](../../../design-decisions/uc03-semantic-references.md) for the model boundaries.

---

## 3. Functional Requirements

**Obligation levels:** MUST = mandatory for current scope; SHOULD = important but deferrable; MAY = optional extension.

---

**FR 1 — Reference Symbol as a First-Class Entity**

> The ontology MUST represent Reference Symbols as distinct entities, each a subclass of `metadata:ReferenceExpression` and therefore `metadata:DrawingElement`, such that an accepted linking relationship between Layouts is expressed through an intermediate node rather than a direct property between two Layouts (or two Sheets).

- Source: UC-03
- Derived terms: existing `csymbol:ReferenceSymbol` (its additional superclass is part of FR 7)
- Note: ReferenceSymbol carries no datatype properties. Its accepted target and display label are queryable from relational links; the actual printed text and extraction decisions stay in source evidence.

---

**FR 2 — Source Layout Association**

> The ontology MUST represent the relationship between a Reference Symbol and the Layout on which it is drawn, such that all reference symbols present on a given Layout (and, transitively, on a given DrawingSheet) can be retrieved.

- Source: UC-03
- Derived terms: `csymbol:hasReferenceSymbol` (NEW; ⊂ `metadata:contains`)

---

**FR 3 — Target Layout Association**

> The ontology MUST represent the relationship between a Reference Symbol and the Layout it references, such that the target Layout (and, transitively, the target Sheet) can be identified from any given Reference Symbol.

- Source: UC-03
- Derived terms: `csymbol:referencesLayout` (NEW)

---

**FR 4 — Bidirectional Navigation**

> The ontology MUST support navigation in both directions: from a source Layout/Sheet to all Layouts it references through its symbols, and from a referenced Layout/Sheet back to all source Layouts/Sheets that contain a symbol pointing to it.

- Source: UC-03
- Derived terms: none — reverse navigation uses SPARQL inverse paths rather than declared inverse properties ([#21](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/21))

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

**FR 7 — Source Reference Occurrences** — MUST

> The ontology MUST distinguish each evidenced sheet/layout-number text occurrence from its target identity,
> group graphical, inline and standalone complete references for queries, and avoid creating a duplicate
> wrapper for a standalone sheet-number reference.

- Source: UC-03 reference extraction and cross-sheet linking ([#95](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/95))
- Derived terms: `metadata:ReferenceExpression`, `SheetNoMention`, `LayoutNoMention`,
  `InlineLayoutSheetReference`, `StandaloneSheetReference`, `hasSheetNoMention`, `hasLayoutNoMention`
- Export condition: a semantic Mention has source-text and original-PDF localisation evidence; incomplete
  candidates remain in extraction evidence. OWL subclassing does not itself verify that condition.

---

**FR 8 — Accepted Textual Targets** — MUST

> The ontology MUST relate a resolved sheet-number occurrence to its accepted DrawingSheet and an inline
> expression to its accepted Layout targets, while allowing unresolved members to have no target edge.

- Source: UC-03 source-to-target traceability ([#95](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/95))
- Derived terms: `metadata:denotesDrawingSheet`, `inlineAppearsOn`, `inlineReferencesLayout`
- Detailed component-to-target pairing stays in structured evidence; the graph contains the supported
  target set. This does not add the graphical whole-sheet relation deferred in
  [#38](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/38) or claim that a PDF hyperlink was emitted.

---

*(FR 2 from v0.1 — Symbol Type Classification — was removed in v0.2. Symbol type can be derived when the target Layout and its `LayoutContentType` are known. See decision §3 below.)*

---

## 4. Competency Questions

CQs are grouped by query shape. The original three symbol-focused groups remain; Group 4 covers the new source-occurrence forms. *(Amended in [v0.5](#10-version-history).)*

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

### CQ Group 4 — Source reference occurrences (validates FR 7, FR 8)

| ID | Competency Question |
|---|---|
| CQ 4.1 | Which distinct sheet-number occurrences are embedded in a symbol or inline reference, and which are standalone references? |
| CQ 4.2 | For `1, 3, 5 & 7/S601`, which accepted target Layouts belong to S601? |
| CQ 4.3 | Which accepted DrawingSheet does a given evidenced sheet-number occurrence denote, if any? |

### CQ Group I — Integration / Multi-field Queries

| ID     | Competency Question                                                                          | FRs exercised                       |
| ------ | -------------------------------------------------------------------------------------------- | ----------------------------------- |
| CQ-I 1 | What Section views in project "X" are referenced from sheet "GA-001"?                        | FR 3, UC-01/FR 2, UC-01/FR 6        |
| CQ-I 2 | Which sheets in project "X" contain markers pointing at any Detail on sheet "ST-201"?         | FR 2, FR 3, UC-01/FR 2              |

---

## 5. SPARQL Validation

**CQ 3.3:** *What is the complete set of sheets connected to sheet "GA-001" through reference symbols in either direction?*

```sparql
PREFIX metadata: <https://w3id.org/adiro/aec_drawing_metadata#>
PREFIX csymbol:  <https://w3id.org/adiro/aec_common_symbols#>

SELECT DISTINCT ?connectedSheet WHERE {
  ?GA001 metadata:drawingIdentifier "GA-001" ;
         metadata:hasLayout     ?sourceLayout .

  {
    # Outgoing: layouts on GA-001 that reference something
    ?sourceLayout csymbol:hasReferenceSymbol ?sym .
    ?sym          csymbol:referencesLayout  ?targetLayout .
    ?connectedSheet metadata:hasLayout       ?targetLayout .
  }
  UNION
  {
    # Incoming: someone else's layout has a symbol pointing into GA-001
    ?sym          csymbol:referencesLayout   ?sourceLayout .
    ?otherLayout  csymbol:hasReferenceSymbol ?sym .
    ?connectedSheet metadata:hasLayout       ?otherLayout .
  }

  FILTER(?connectedSheet != ?GA001)
}
```

Notes:
- The query uses the current `w3id.org` module namespaces and the existing `metadata:hasLayout` relationship.
- Both directions are expressible using the defined forward properties; no named inverse property is required.
- The query traverses Sheet → Layout → ReferenceSymbol → Layout → Sheet at both ends, demonstrating that Layout-level mounting (decision §2) does not obstruct sheet-level user queries — sheet-level results emerge from a single extra hop.

**CQ 2.1 (composite-label resolution) example:**

```sparql
PREFIX metadata: <https://w3id.org/adiro/aec_drawing_metadata#>
PREFIX csymbol:  <https://w3id.org/adiro/aec_common_symbols#>

# Given composite label "2/ST-201":
SELECT ?sym ?targetLayout WHERE {
  ?targetSheet  metadata:drawingIdentifier "ST-201" ;
                metadata:hasLayout     ?targetLayout .
  ?targetLayout metadata:layoutIdentifier  "2" .
  ?sym csymbol:referencesLayout ?targetLayout .
}
```

This demonstrates FR 5: parse the composite label into sheet and layout identifiers, then retrieve symbols
with an **accepted** edge to the resolved Layout. The query does not prove what text was printed inside any
particular symbol; inspect that symbol's source evidence for a text comparison.

**CQ 4.2 (accepted inline targets) example:**

```sparql
PREFIX metadata: <https://w3id.org/adiro/aec_drawing_metadata#>

SELECT DISTINCT ?targetLayout WHERE {
  ?inline a metadata:InlineLayoutSheetReference ;
          metadata:hasSheetNoMention ?sheetMention ;
          metadata:inlineReferencesLayout ?targetLayout .
  ?sheetMention metadata:denotesDrawingSheet ?sheet .
  ?sheet metadata:drawingIdentifier "S601" ;
         metadata:hasLayout ?targetLayout .
}
```

The query returns only asserted target edges. It does not invent an edge for every number in the source
string; member-level pairings and unresolved decisions require the indexed evidence record.

---

## 6. Traceability Matrix

| OWL Term                       | Module                 | Action | CQ(s)                                | FR(s)            |
| ------------------------------ | ---------------------- | ------ | ------------------------------------ | ---------------- |
| `metadata:DrawingSheet`        | `aec_drawing_metadata` | REUSE  | CQ 1.x, CQ 3.x, CQ-I 1, CQ-I 2       | (structural)     |
| `metadata:Layout`              | `aec_drawing_metadata` | REUSE  | CQ 1.x, CQ 2.x, CQ 3.x, CQ-I 1, CQ-I 2 | FR 2, FR 3, FR 5 |
| `metadata:LayoutContentType`   | `aec_drawing_metadata` | REUSE  | CQ 1.3, CQ 1.4, CQ-I 1               | (derives type)   |
| `csymbol:ReferenceSymbol`      | `aec_common_symbols`   | NEW    | CQ 1.x, CQ 2.x, CQ 3.x, CQ-I 1, CQ-I 2 | FR 1             |
| `metadata:hasLayout`           | `aec_drawing_metadata` | REUSE  | CQ 1.x, CQ 3.x, CQ 4.2, CQ-I 1, CQ-I 2 | (structural)     |
| `csymbol:hasReferenceSymbol`   | `aec_common_symbols`   | NEW    | CQ 1.x, CQ 3.x                       | FR 2             |
| `csymbol:referencesLayout`    | `aec_common_symbols`   | NEW    | CQ 2.x, CQ 3.x, CQ-I 1, CQ-I 2       | FR 3             |
| `metadata:drawingIdentifier`       | `aec_drawing_metadata` | REUSE  | CQ 2.x                               | FR 5 (UC-01 v0.3) |
| `metadata:layoutIdentifier`        | `aec_drawing_metadata` | REUSE | CQ 2.x | FR 5 |
| `metadata:ReferenceExpression` | `aec_drawing_metadata` | NEW | CQ 4.1 | FR 7 |
| `metadata:SheetNoMention` / `LayoutNoMention` | `aec_drawing_metadata` | NEW | CQ 4.1–4.3 | FR 7, FR 8 |
| `metadata:InlineLayoutSheetReference` / `StandaloneSheetReference` | `aec_drawing_metadata` | NEW | CQ 4.1–4.3 | FR 7 |
| `metadata:hasSheetNoMention` / `hasLayoutNoMention` | `aec_drawing_metadata` | NEW | CQ 4.1, CQ 4.2 | FR 7 |
| `metadata:denotesDrawingSheet` | `aec_drawing_metadata` | NEW | CQ 4.2, CQ 4.3 | FR 8 |
| `metadata:inlineAppearsOn` / `inlineReferencesLayout` | `aec_drawing_metadata` | NEW | CQ 4.2 | FR 8 |

---

## 7. Module Alignment Summary

Per the project's import hierarchy and [PR #15](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/15) review point #2 (@alelom), every UC-03 term is placed in its proper module.

**Module hierarchy** *(updated in [v0.4](#10-version-history))*:

```
aec_provenance                      (NEW - foundational, domain-neutral)
        |
        +---- aec_geometry          (NEW - foundational: BoundingBox + CoordinateFrame; imports aec_provenance)
                |
                +---- aec_drawing_metadata
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
| `aec_drawing_metadata` | Reuses `DrawingSheet`, `Layout`, `hasLayout`, `layoutIdentifier` and `drawingIdentifier`; adds complete reference/number-occurrence classes plus their composition and accepted textual target relations (FR 7–8). |
| `aec_common_symbols`   | `ReferenceSymbol` now also subclasses `metadata:ReferenceExpression`; its `hasReferenceSymbol` and `referencesLayout` properties retain their graphical-symbol scope. |
| `aec_domain_common`    | No UC-03 contribution.                                                                                                                                              |
| `aec_facade_domain`    | No UC-03 contribution.                                                                                                                                              |

**Subproperty wiring:**

```
metadata:contains (existing)
  ├── csymbol:hasReferenceSymbol
  ├── metadata:hasSheetNoMention
  └── metadata:hasLayoutNoMention
```

`referencesLayout`, `inlineReferencesLayout` and `denotesDrawingSheet` remain top-level target relations, not
containment. `inlineAppearsOn` is a source-membership relation, not an inverse of `hasReferenceSymbol`.

---

## 8. Open Issues — Pending Team Discussion

These items were raised during UC-03 drafting. **UC03-1 and UC03-2 are resolved** in `src/`. **UC03-3, UC03-4 and the graphical whole-sheet case in UC03-5 remain tracked separately.** The inverse-property convention is decided. The textual occurrence model in FR 7–8 does not settle those deferred cases. *(Amended in [v0.5](#10-version-history).)*

| ID    | Issue                                                                                                                                                                                                                                       |
| ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| UC03-1 | **✅ RESOLVED (implemented).** Adopted `ReferenceSymbol` and removed the earlier `Callout` class (option b) — see `src/aec_common_symbols.ttl`. *(Original question: name/relationship of the cross-sheet linking class vs `Callout`; scope was agreed, name was open.)* |
| UC03-2 | **✅ RESOLVED (implemented).** `metadata:layoutIdentifier` is now declared in `aec_drawing_metadata` (`src/`). *(Original: UC-03 introduced it provisionally, pending UC-01 formally adopting it as an identity field.)* |
| UC03-3 | **→ Tracked as [#36](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/36) (deferred).** A GeoSPARQL WKT/CRS profile and source-Layout spatial containment queries remain optional. The shared `BoundingBox` / `CoordinateFrame` already exist in PR #76; UC-03 localisation and navigation geometry are separately tracked in [#93](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/93). A title/number strip is not a full Layout polygon, and spatial overlap alone does not establish accepted source membership. |
| UC03-4 | **→ Tracked as [#37](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/37) (backlog; out of UC-03 core scope).** Match Lines and other reference symbol types. Industry usage extends beyond Detail/Section/Elevation markers (Match Lines for split-sheet continuation, Schedule references, Key Plan references, etc.). UC-03's current scope covers the three primary types; broader coverage may need additional modelling if a CQ requires it. |
| UC03-5 | **→ Tracked as [#38](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/38) (backlog).** A graphical marker targeting an entire DrawingSheet remains an open case; the existing `csymbol:referencesLayout` is Layout-level and no general `referencesSheet` property is introduced here. For textual sources, `metadata:TextualNote.refersToDrawingId` remains available for a note's identifier string. The new `StandaloneSheetReference` instead represents one evidenced sheet-number occurrence whose accepted sheet identity may be expressed by `denotesDrawingSheet`; it does not change the graphical-marker question. |
| —     | **✅ RESOLVED — [#21](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/21).** Inverse-property convention (project-wide, not UC-03-specific). Decided: ADIRO declares **no** named inverse properties and no `owl:inverseOf` axioms; reverse navigation uses SPARQL inverse paths. `appearsOn` and `isReferencedBy` removed from `aec_common_symbols`; `isRevisionOf` removed from `aec_drawing_metadata`. *(Applied in [v0.3](#10-version-history).)* |

---

## 9. Design Decisions — Reasoning Index

For the full design-debate reasoning behind the v0.2 modelling choices, see the accompanying *UC-03 Design Debate* note. The key decisions, in summary:

1. **§1 — Ontology role:** The semantic terms hold accepted reference identities, composition and targets. Parsing, candidate decisions and original-text evidence remain in referenced extraction records. *(Amended in [v0.5](#10-version-history).)*
2. **§2 — Layout-level mounting:** Both ends of a ReferenceSymbol link `Layout → Layout`, not `Sheet → Sheet`. Better precision; aligns with the existing DrawingElement architecture.
3. **§3 — No `SymbolType`:** Marker type (Detail / Section / Elevation) can be derived from an accepted target Layout's `LayoutContentType` when known. FR 2 from v0.1 removed.
4. **§4 — No `symbolLabel`:** An accepted target can provide a display label, but it is not evidence of the original printed text. Raw-text placement remains open in [#20](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/20). *(Amended in [v0.5](#10-version-history).)*
5. **§5 — No `symbolNumber`:** The accepted target Layout provides a number for navigation; the source occurrence is retained separately in evidence. The present `ReferenceSymbol` still has no datatype property. *(Amended in [v0.5](#10-version-history).)*
6. **§6 — Reusable principle:** *"The ontology models facts, not their display derivatives."* Three-step check for any new datatype property — derivability test, independent-assertion test, optimisation warning.
7. **§7 — RDF identity ≠ domain identity:** Instance uniqueness is provided by RDF URI, never by adding a datatype property. Multiple identical markers are distinct URIs, not distinct values.

---

## 10. Version History

### v0.5 (current branch — pending review)

Substantive UC-03 semantic extension under [#95](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/95):
FR 7–8 and CQ Group 4 add source-number occurrences, complete inline/standalone expressions, and accepted
textual target relations. `ReferenceSymbol` now subclasses `ReferenceExpression`; its original Layout-level
target relation remains unchanged. This is a **MAJOR scope change within the pre-release 0.x series**.

The earlier document represented UC-03 solely through graphical markers and said that textual whole-sheet
references were outside scope. The new model distinguishes an evidenced text occurrence from its target
DrawingSheet while retaining `TextualNote.refersToDrawingId` for note-level identifier strings. It does not
add a general graphical `referencesSheet` property, a Binding node, a raw-text datatype property, or a
NavigationLink class. Geometry and provenance extensions remain in
[#93](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/93) and
[#96](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/96).

The SPARQL examples now use the current `w3id.org` IRIs, existing `hasLayout`, and accepted target edges.
Their query shapes are illustrative until ABox/SPARQL validation under
[#22](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/22) is performed.

### v0.4 (reviewed & implemented)

Changes from v0.3, made in [PR #76](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/76) when the `aec_geometry` module was added ([#90](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/90)). MINOR — suite-accuracy only, no UC-03 term change:

- **§7 module hierarchy updated** — the new foundational `aec_geometry` module (bounding boxes + coordinate
  frames; imports `aec_provenance`) is shown as a second foundational root that `aec_drawing_metadata` imports.
  UC-03 gains no geometry terms here; its own geometry extension (reference-symbol boxes, coordinate transforms,
  clickable/navigation geometry) remains future work on `aec_geometry`.

### v0.3 (reviewed & implemented)

Changes from v0.2, made in [PR #76](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/76) when `aec_provenance` was added to the suite:

- **§9 Design Decision 1 amended — provenance removed from the exclusion.** The decision previously read
  *"this ontology is a query layer, not a raw-storage layer. Parsing, OCR clean-up, **and provenance** live
  upstream/elsewhere."* The parsing and OCR-clean-up half stands unchanged. The provenance half was a
  statement about **one module** read as though it settled the matter for **ADIRO, which is a suite**: a
  decision that a query-layer module should not store OCR intermediates says nothing about whether the suite
  models provenance at all. ADIRO now does, in the foundational `aec_provenance` module — reified
  assertions carrying `assertedBy`, `hasInferenceMeta`, `hasConfidence` and `capturedCaption` — which serves
  suite ORSD **CQ 2.4, 3.1, 3.2 and 4.4**. Whether `ReferenceSymbol` specifically should carry as-extracted
  text and provenance remains open in
  [#20](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/20); `aprov:capturedCaption` is the pattern
  that answers *where* the raw value lives — on the assertion, not on the semantic property.
- **§7 module hierarchy updated** — `aec_provenance` is a new foundational root.

- **BREAKING — `csymbol:appearsOn` and `csymbol:isReferencedBy` removed.** [#21](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/21) decided project-wide
  that ADIRO declares no named inverse properties and no `owl:inverseOf` axioms. Only the forward direction
  of each pair survives: `hasReferenceSymbol` (Layout → ReferenceSymbol, ⊂ `metadata:contains`) and
  `referencesLayout` (ReferenceSymbol → Layout). The §2.3 relations table, the FR 2 / FR 4 derived terms, the
  §6 traceability matrix and the §7 module table are updated, and **the CQ 3.3 SPARQL query is rewritten** to
  read the two surviving properties in the other direction. No competency question changed — CQ 3.1, 3.2 and
  3.3 are direction-agnostic and remain answerable.
- **§8 open issues revised**: every GitHub issue reference is now a link, and the inverse-property row is
  marked resolved. UC03-3 / UC03-4 / UC03-5 were re-checked against their issues and still stand.

A relation was removed, so this is a **MAJOR** revision in substance; the number stays in the 0.x series
because v0.3 was never released.

### v0.2 (reviewed & implemented)

Aligned with the existing ontology modules (`aec_drawing_metadata`, `aec_common_symbols`) per [PR #15](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/15) review (@alelom, @AhmedElnagar1):

- Fixed: all internal `UC-02` references corrected to `UC-03` (v0.1 used the wrong ID throughout).
- `Drawing` → `metadata:DrawingSheet`; ReferenceSymbol now mounts on `metadata:Layout` (not on Sheet) — see G1, [§2](#2-information-needs-analysis).
- The class for cross-sheet linking symbols is introduced in `aec_common_symbols`. Its **scope** is confirmed (Detail / Section / Elevation markers and similar cross-sheet linkers); its **name** (`ReferenceSymbol`, `Callout`, or an alternative) and its relationship to the existing `csymbol:Callout` class are left for team review — see Open Issue UC03-1.
- **ReferenceSymbol is a pure relational node** — zero datatype properties. v0.1's `symbolLabel`, `symbolNumber`, and `SymbolType` / `hasSymbolType` / `typeLabel` all removed; see [§9 Design Decisions](#9-design-decisions-reasoning-index) §3–§5 and the *design-debate* note.
- `hasReferenceSymbol` wired via `rdfs:subPropertyOf metadata:contains` (G6).
- SPARQL placeholder namespace replaced with real module prefixes (G8).
- CQ groups consolidated from 5 → 3 (Discovery / Navigation / Network) per @AhmedElnagar1's "competency questions repeat themselves".
- Identified cross-UC dependency: UC-03 needs `metadata:layoutIdentifier`, which properly belongs in UC-01 v0.4 — flagged in Open Issues.

### v0.1

Predates this changelog.

---

*End of ORSD — UC-03 v 0.2*
