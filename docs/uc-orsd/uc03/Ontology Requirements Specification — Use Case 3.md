# Reference Symbol Cross-Sheet Linking

> **Methodology:** LOT (Linked Open Terms) **Use Case ID:** UC-02 **Version:** 0.1 (draft)

---

## 1. Use Case

|Field|Content|
|---|---|
|**ID**|UC-02|
|**Title**|Reference Symbol Cross-Sheet Linking|
|**Statement**|As a designer, I want to navigate between a drawing and all drawings connected to it through reference symbols — such as Detail Markers, Section Markers, and Elevation Markers — so that I can trace how a building element is documented across sheets and drawing sets in both directions.|
|**Primary Actor**|Designer|
|**Goal**|Given any drawing, retrieve the complete set of drawings linked to it through reference symbols, navigable in both directions: from source drawing to referenced drawings, and from a referenced drawing back to all drawings that point to it.|

---

## 2. Information Needs Analysis

### 2.1 Entities

|Entity|Rationale|
|---|---|
|Drawing|The primary object on both ends of any link; already defined in UC-01|
|ReferenceSymbol|The linking mechanism itself — not a simple property but a first-class entity carrying its own type, number, and label|
|SymbolType|Controlled vocabulary distinguishing Detail Marker, Section Marker, and Elevation Marker|

> **Design note — ReferenceSymbol as an entity:** `ReferenceSymbol` must be an independent class, not a direct Property between two Drawings. The symbol carries its own information (type, number, composite label) and sits asymmetrically between a source drawing (where it appears) and a target drawing (what it references). A direct `Drawing → referencesDrawing → Drawing` property would lose this intermediate information and would not support queries such as "what type of symbol connects these two drawings" or "how many symbols on this drawing reference the same target."

> **Design note — ReferenceSymbol links to Drawing, not LayoutRegion:** The target end of a reference symbol points to a drawing as a whole — a Detail Marker references a complete Detail drawing; a Section Marker references a complete Section drawing. Linking to `Drawing` is therefore semantically correct for the target end.
> 
> For the source end, a `ReferenceSymbol` does occupy a specific spatial position on its source drawing, and that position (bounding box) could in principle be useful for UX highlighting. However, bounding boxes belong to the geometric layer, which is outside the current ontology scope (see Architecture & Provenance Extension document). The property `:hasLocation → LayoutRegion` is reserved as a future geometric-layer extension, to be introduced when a dedicated Use Case and Competency Questions justify it. It does not conflict with the current design.

### 2.2 Attributes

|Attribute|Entity|Expected Type|Notes|
|---|---|---|---|
|Symbol number|ReferenceSymbol|xsd:string|Local identifier within source drawing context, e.g. `"2"` |
|Symbol label|ReferenceSymbol|xsd:string|Composite callout as it appears on the drawing, e.g. `"2/ST-201"` |
|Type label|SymbolType|xsd:string|e.g. `"Detail Marker"`, `"Section Marker"` |

### 2.3 Relations

|Relation|Domain|Range|Notes|
|---|---|---|---|
|appears on|ReferenceSymbol|Drawing|Source drawing — where the symbol is drawn|
|references drawing|ReferenceSymbol|Drawing|Target drawing — what the symbol points to|
|has reference symbol|Drawing|ReferenceSymbol|Inverse of `appearsOn` |
|is referenced by|Drawing|ReferenceSymbol|Inverse of `referencesDrawing` |
|has symbol type|ReferenceSymbol|SymbolType|Type classification|

---

## 3. Functional Requirements

**Obligation levels:** MUST = mandatory for current scope; SHOULD = important but deferrable; MAY = optional extension.

---

**FR 1 — Reference Symbol as a First-Class Entity**

> The ontology MUST represent Reference Symbols as distinct entities, each carrying a symbol type, symbol number, and composite label, such that the linking relationship between drawings is expressed through an intermediate node rather than a direct drawing-to-drawing property.

- Source: UC-02
- Derived terms: `:ReferenceSymbol`, `:symbolNumber`, `:symbolLabel`

---

**FR 2 — Symbol Type Classification**

> The ontology MUST represent the type of each Reference Symbol using a controlled vocabulary (Detail Marker, Section Marker, Elevation Marker), such that drawings can be filtered and navigated by the type of reference relationship.

- Source: UC-02
- Derived terms: `:SymbolType`, `:hasSymbolType`, `:typeLabel`

---

**FR 3 — Source Drawing Association**

> The ontology MUST represent the relationship between a Reference Symbol and the drawing on which it appears, such that all reference symbols present on a given drawing can be retrieved.

- Source: UC-02
- Derived terms: `:appearsOn`, `:hasReferenceSymbol`

---

**FR 4 — Target Drawing Association**

> The ontology MUST represent the relationship between a Reference Symbol and the drawing it references, such that the target drawing can be identified from any given reference symbol.

- Source: UC-02
- Derived terms: `:referencesDrawing`, `:isReferencedBy`

---

**FR 5 — Bidirectional Navigation**

> The ontology MUST support navigation in both directions: from a source drawing to all drawings it references through its symbols, and from a referenced drawing back to all source drawings that contain a symbol pointing to it.

- Source: UC-02
- Derived terms: inverse properties `:hasReferenceSymbol` / `:isReferencedBy`
- Note: Bidirectional navigation is implemented via `owl:inverseOf` declarations; a reasoner can infer both directions from a single assertion direction.

---

**FR 6 — Symbol Number and Composite Label**

> The ontology MUST represent the symbol number and composite label of each Reference Symbol, such that individual symbols can be uniquely identified within the context of their source drawing and the full callout notation can be reproduced.

- Source: UC-02
- Derived terms: `:symbolNumber`, `:symbolLabel`

---

**FR 7 — Cross-Drawing-Set Linking**

> The ontology MAY support linking across drawing sets, such that a reference symbol on a drawing in one set can reference a drawing that belongs to a different set.

- Source: UC-02
- Obligation: MAY — optional extension
- Note: No `DrawingSet` class is defined in the current scope. This FR is passively satisfied by ensuring `:referencesDrawing` carries no restriction to the same drawing set. No additional modelling is required unless a future Use Case introduces `DrawingSet` as a first-class entity with its own Competency Questions.

---

## 4. Competency Questions

### CQ Group 1 — Symbol Discovery (validates FR 1, FR 2, FR 3)

|ID|Competency Question|
|---|---|
|CQ 1.1|What reference symbols appear on drawing "GA-001"?|
|CQ 1.2|What Detail Markers appear on drawing "GA-001"?|
|CQ 1.3|What types of reference symbols are used across project "X"?|

---

### CQ Group 2 — Source Drawing Lookup (validates FR 3)

|ID|Competency Question|
|---|---|
|CQ 2.1|On which drawing does reference symbol "2/ST-201" appear?|
|CQ 2.2|How many reference symbols appear on drawing "GA-001"?|

---

### CQ Group 3 — Target Drawing Lookup (validates FR 4)

|ID|Competency Question|
|---|---|
|CQ 3.1|What drawing does Detail Marker "2" on drawing "GA-001" reference?|
|CQ 3.2|What drawing is referenced by the symbol labelled "2/ST-201"?|

---

### CQ Group 4 — Bidirectional Navigation (validates FR 5)

|ID|Competency Question|
|---|---|
|CQ 4.1|What drawings are referenced by drawing "GA-001" through its reference symbols?|
|CQ 4.2|Which drawings contain a reference symbol pointing to drawing "ST-201"?|
|CQ 4.3|What is the complete set of drawings connected to drawing "GA-001" through reference symbols in either direction?|

---

### CQ Group 5 — Symbol Identity (validates FR 6)

|ID|Competency Question|
|---|---|
|CQ 5.1|What is the symbol number of the Detail Marker on drawing "GA-001" that references drawing "ST-201"?|
|CQ 5.2|Are there multiple reference symbols on drawing "GA-001" that reference the same target drawing?|

---

### CQ Group I — Integration / Multi-field Queries

|ID|Competency Question|FRs exercised|
|---|---|---|
|CQ-I 1|What Section drawings in project "X" are referenced from drawing "GA-001"?|FR 2, FR 4, UC-01/FR 2|
|CQ-I 2|Which drawings in project "X" contain Detail Markers pointing to drawing "ST-201"?|FR 2, FR 3, UC-01/FR 2|
|CQ-I 3|What is the full reference symbol network of drawing "GA-001" — both outgoing and incoming links?|FR 3, FR 4, FR 5|

---

## 5. SPARQL Validation

**CQ 4.3:** _What is the complete set of drawings connected to drawing "GA-001" through reference symbols in either direction?_

```sparql
PREFIX : <https://example.org/aec-ontology#>

SELECT DISTINCT ?connected WHERE {
  {
    # Outgoing: drawings that GA-001 references
    :GA001  :hasReferenceSymbol  ?sym .
    ?sym    :referencesDrawing   ?connected .
  }
  UNION
  {
    # Incoming: drawings that reference GA-001
    ?sym    :referencesDrawing   :GA001 ;
            :appearsOn           ?connected .
  }
}
```

Both directions are expressible using the defined properties. The query confirms that FR 5 (Bidirectional Navigation) is fully covered by the current term inventory.

---

## 6. Traceability Matrix

|OWL Term|CQ(s)|FR(s)|UC|
|---|---|---|---|
| `:ReferenceSymbol` |CQ 1.x, CQ 2.x, CQ 3.x, CQ 4.x, CQ 5.x|FR 1, FR 2, FR 3, FR 4, FR 6|UC-02|
| `:SymbolType` |CQ 1.2, CQ 1.3, CQ-I 1, CQ-I 2|FR 2|UC-02|
| `:appearsOn` |CQ 2.1, CQ 4.3|FR 3|UC-02|
| `:hasReferenceSymbol` |CQ 1.x, CQ 2.2, CQ 4.1, CQ 4.3|FR 3, FR 5|UC-02|
| `:referencesDrawing` |CQ 3.x, CQ 4.1, CQ 4.3|FR 4|UC-02|
| `:isReferencedBy` |CQ 4.2, CQ 4.3|FR 4, FR 5|UC-02|
| `:hasSymbolType` |CQ 1.2, CQ 1.3|FR 2|UC-02|
| `:symbolNumber` |CQ 5.1|FR 6|UC-02|
| `:symbolLabel` |CQ 2.1, CQ 3.2|FR 6|UC-02|
| `:typeLabel` |CQ 1.3|FR 2|UC-02|

---

## 7. Future Extension Note — Geometric Layer

The current design links `ReferenceSymbol` to `Drawing` at the semantic level. A future geometric-layer extension may introduce:

```turtle
# Future extension only — requires a dedicated Use Case and CQs
:hasLocation  rdfs:domain  :ReferenceSymbol ;
              rdfs:range   :LayoutRegion .

:LayoutRegion  :hasBbox    xsd:string ;
               :isPartOf   :Drawing .
```

This extension would enable spatial queries (e.g. "where on the drawing does this symbol appear?") and precise UX highlighting. It does not conflict with the current semantic-layer design and can be added additively when a Use Case justifies it.

---

_End of ORSD — UC-02 v 0.1_