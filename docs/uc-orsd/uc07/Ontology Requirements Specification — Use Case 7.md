
> **Methodology:** LOT (Linked Open Terms) **Use Case ID:** UC-07 **Version:** 0.2 (draft) **Changes from v 0.1:** Introduced North Arrow as drawing-level orientation datum; introduced numeric scale ratio; distinguished on-drawing measurements from real-world dimensions; repositioned FacingDirection from a primary assertion to a classification derivable from geometric data.

---

## 1. Use Case

|Field|Content|
|---|---|
|**ID**|UC-07|
|**Title**|Wall Orientation Identification & Measurement in Plan Drawings|
|**Statement**|As an engineer, I want to identify all walls that are facing north or east in a plan drawing and retrieve their dimensional measurements — both as measured on the drawing and as real-world dimensions.|
|**Primary Actor**|Engineer|
|**Goal**|Given a plan drawing, use its North Arrow (orientation datum) and scale (dimension datum) to determine each wall's real-world facing direction and real-world dimensions, filter by orientation criteria, and return results.|

---

## 2. Information Needs Analysis

### 2.1 Entities

|Entity|Rationale|
|---|---|
|Drawing|The carrier on which walls appear; already defined in UC-01. This use case adds orientation and scale properties to it.|
|BuildingElement|Generic superclass for building components depicted on a drawing.|
|Wall|Subclass of `BuildingElement`, carrying orientation and dimensional properties.|
|FacingDirection|Controlled vocabulary for the real-world outward-facing direction of a wall surface.|

> **Design note — Two datums: North Arrow and Scale**
> 
> All geometric information on a plan drawing must be calibrated through two datums before it becomes real-world semantics:
> 
> |Datum|On-drawing raw value|Transform|Real-world semantics|
> |---|---|---|---|
> |**North Arrow**|Wall angle on page|+ North Arrow rotation|Wall's real-world facing direction|
> |**Scale**|Wall line length on page|× scale ratio|Wall's real-world length|
> 
> Thus, `NorthArrow` is to direction what `Scale` is to dimension — they are two independent transformation axes from drawing coordinate space to real-world coordinate space.

> **Design note — Modelling the North Arrow**
> 
> The North Arrow is modelled as a datatype property `:northArrowAngle` on `Drawing` (`xsd:decimal`, in degrees, measured clockwise from page-up). For example: North Arrow pointing straight up → `0.0`; pointing upper-right at 45° → `45.0`. This is a drawing-level property, not belonging to any individual wall.
> 
> The North Arrow is not modelled as a separate entity because it carries no attributes of its own beyond a single angle value and has no relation network. A datatype property is sufficient to satisfy all current CQs.

> **Design note — Enhanced Scale representation**
> 
> UC-01 already defines `:hasScale` as `xsd:string` (e.g. `"1:50"`). This use case adds `:scaleRatio` (`xsd:decimal`), storing the numerical denominator of the scale (e.g. `50.0` for `1:50`). This allows SPARQL queries to perform multiplication directly: `realWorldLength = onDrawingLength × scaleRatio`. The string `:hasScale` is retained as a human-readable label.

> **Design note — FacingDirection: stored or derived?**
> 
> Strictly speaking, a wall's real-world facing direction is fully derivable from two raw values: `wallAngleOnDrawing` (wall's angle on the page) + `northArrowAngle` (the drawing's orientation datum) → real-world direction. This is perfectly parallel to "real-world length = on-drawing length × scale ratio."
> 
> However, **also storing the derived classification `FacingDirection` ** in the ontology remains justified: (1) the user's query language is "north-facing walls," not "walls with azimuth 350°–10°" — a controlled vocabulary directly matches query intent; (2) the eight-direction classification provides discretisation buckets for continuous angles, simplifying SPARQL; (3) storing derived values avoids trigonometric computation in every query.
> 
> This design therefore adopts a **dual-layer model**: raw geometric values (`wallAngleOnDrawing`) + derived semantic classification (`hasFacingDirection`). Both coexist without conflict.

### 2.2 Attributes

#### Drawing-level Properties

|Attribute|Entity|Expected Type|Notes|
|---|---|---|---|
|North Arrow angle|Drawing|xsd:decimal|Degrees clockwise from page-up to the North Arrow. 0 = north is straight up.|
|Scale ratio|Drawing|xsd:decimal|Numerical denominator of the scale, e.g. `1:50` → `50.0`.|

#### Element-level Properties

|Attribute|Entity|Expected Type|Notes|
|---|---|---|---|
|Element label|BuildingElement|xsd:string|Element identifier on the drawing, e.g. `"W-03"` |
|Wall length on drawing|Wall|xsd:decimal|Wall length as measured on the drawing (mm on paper)|
|Wall thickness on drawing|Wall|xsd:decimal|Wall thickness as measured on the drawing (mm on paper)|
|Wall real-world length|Wall|xsd:decimal|Real-world length (mm) = on-drawing length × scale ratio|
|Wall real-world thickness|Wall|xsd:decimal|Real-world thickness (mm) = on-drawing thickness × scale ratio|
|Wall angle on drawing|Wall|xsd:decimal|Angle of wall's outward normal on the page (degrees, clockwise from page-up)|
|Direction label|FacingDirection|xsd:string|e.g. `"North"`, `"East"`, `"NE"` |

> **Design note — Why store both on-drawing and real-world values**
> 
> On-drawing values are the direct output of the CV pipeline (detected line lengths, angles) — they are traceable raw data. Real-world values are the semantic data engineers care about. They are linked through scale and North Arrow. Benefits of storing both layers: (1) traceability — the provenance of real-world values can be verified; (2) if the scale is corrected, real-world values can be recomputed without re-running CV; (3) on-drawing values from different drawings are not directly comparable (different scales), but real-world values are.

### 2.3 Relations

|Relation|Domain|Range|Notes|
|---|---|---|---|
|depicts element|Drawing|BuildingElement|The drawing depicts this building element|
|is depicted on|BuildingElement|Drawing|Inverse of `depictsElement` |
|has facing direction|Wall|FacingDirection|Real-world outward-facing direction (derived from wallAngleOnDrawing + northArrowAngle)|

---

## 3. Functional Requirements

**Obligation levels:** MUST = mandatory for current scope; SHOULD = important but deferrable; MAY = optional extension.

---

**FR 1 — Drawing Orientation Datum (North Arrow)**

> The ontology MUST represent the North Arrow angle of a plan drawing, such that directional information on the drawing can be transformed into real-world orientation.

- Source: UC-07
- Derived terms: `:northArrowAngle`

---

**FR 2 — Numeric Scale Representation**

> The ontology MUST represent the numerical ratio of a drawing's scale (in addition to the string representation already defined in UC-01), such that on-drawing measurements can be converted to real-world dimensions via multiplication.

- Source: UC-07
- Derived terms: `:scaleRatio`

---

**FR 3 — Wall as a First-Class Entity**

> The ontology MUST represent walls as distinct entities (as a subclass of `BuildingElement`), each carrying a label, such that walls can be retrieved at the drawing level.

- Source: UC-07
- Derived terms: `:BuildingElement`, `:Wall`, `:elementLabel`

---

**FR 4 — Drawing–Element Association**

> The ontology MUST represent the relationship between a drawing and the building elements depicted on it, such that all elements on a given drawing can be retrieved.

- Source: UC-07
- Derived terms: `:depictsElement`, `:isDepictedOnDrawing`

---

**FR 5 — Dual-Layer Dimensional Representation**

> The ontology MUST represent both the on-drawing measurements (length, thickness) and the real-world dimensions (length, thickness) of each wall, such that both layers of dimensional information can be queried and the real-world dimensions can be verified against the scale.

- Source: UC-07
- Derived terms: `:wallLengthOnDrawing`, `:wallThicknessOnDrawing`, `:wallLengthRealWorld`, `:wallThicknessRealWorld`

---

**FR 6 — Wall Facing Direction Classification**

> The ontology MUST represent the real-world facing direction of each wall using a controlled vocabulary (North, NE, East, SE, South, SW, West, NW), such that walls can be filtered by orientation criteria.

- Source: UC-07
- Derived terms: `:FacingDirection`, `:hasFacingDirection`, `:directionLabel`

---

**FR 7 — Wall On-Drawing Angle**

> The ontology SHOULD represent the on-drawing normal angle of each wall (raw geometric data), such that the derivation of real-world facing direction can be traced and verified (on-drawing angle + North Arrow angle → real-world bearing).

- Source: UC-07
- Obligation: SHOULD
- Derived terms: `:wallAngleOnDrawing`

---

**FR 8 — Multi-Orientation Filtering**

> The ontology MUST support filtering walls by one or more facing direction values (e.g. "north or east"), such that engineers can retrieve all walls matching compound orientation criteria in a single query.

- Source: UC-07
- Note: No new terms; implemented via SPARQL `VALUES` clause.

---

**FR 9 — Plan Drawing Type Filtering**

> The ontology MUST support restricting wall queries to a specific drawing type (e.g. "Plan").

- Source: UC-07
- Note: Satisfied by reusing `:hasDrawingType` from UC-01.

---

**FR 10 — Wall Dimension Aggregation**

> The ontology SHOULD support dimensional aggregation over walls matching given criteria (e.g. computing total real-world length), such that engineers can obtain summary information like "total real-world length of all north-facing walls."

- Source: UC-07
- Obligation: SHOULD
- Note: Implemented via SPARQL `SUM` on `:wallLengthRealWorld`.

---

## 4. Competency Questions

### CQ Group 1 — Drawing Datums (validates FR 1, FR 2)

|ID|Competency Question|
|---|---|
|CQ 1.1|What is the North Arrow angle of drawing "PL-001"?|
|CQ 1.2|What is the scale ratio of drawing "PL-001"?|
|CQ 1.3|Which Plan drawings in project "X" have a non-zero North Arrow angle (i.e. north is not straight up)?|

---

### CQ Group 2 — Wall Discovery (validates FR 3, FR 4)

|ID|Competency Question|
|---|---|
|CQ 2.1|What walls are depicted on drawing "PL-001"?|
|CQ 2.2|How many walls are depicted on drawing "PL-001"?|
|CQ 2.3|On which drawings does wall "W-03" appear?|

---

### CQ Group 3 — Orientation Filtering (validates FR 6, FR 7, FR 8)

|ID|Competency Question|
|---|---|
|CQ 3.1|What north-facing walls are on drawing "PL-001"?|
|CQ 3.2|What walls on drawing "PL-001" face north or east?|
|CQ 3.3|What is the real-world facing direction of wall "W-03"? What is its on-drawing angle?|

---

### CQ Group 4 — Dual-Layer Dimensional Query (validates FR 5)

|ID|Competency Question|
|---|---|
|CQ 4.1|What are the on-drawing length and real-world length of wall "W-03" on drawing "PL-001"?|
|CQ 4.2|Which walls on drawing "PL-001" have a real-world length exceeding 3000 mm?|
|CQ 4.3|Does the real-world length of wall "W-03" equal its on-drawing length multiplied by the drawing's scale ratio?|

---

### CQ Group 5 — Dimensional Aggregation (validates FR 10)

|ID|Competency Question|
|---|---|
|CQ 5.1|What is the total real-world length of all north-facing walls on drawing "PL-001"?|
|CQ 5.2|What is the total real-world wall length per facing direction for north- and east-facing walls on drawing "PL-001"?|

---

### CQ Group I — Integration / Multi-field Queries

|ID|Competency Question|FRs exercised|
|---|---|---|
|CQ-I 1|What are all north- or east-facing walls and their real-world dimensions on Structural Plan drawings in project "X"?|FR 3, FR 4, FR 5, FR 6, FR 8, FR 9, UC-01/FR 2, UC-01/FR 5, UC-01/FR 6|
|CQ-I 2|In project "X", what is the total real-world wall length grouped by facing direction?|FR 5, FR 6, FR 10, UC-01/FR 2|
|CQ-I 3|Verification query: does the on-drawing angle of wall "W-03" on drawing "PL-001" plus the North Arrow angle fall within the angular range of its labelled facing direction?|FR 1, FR 6, FR 7|

---

## 5. SPARQL Validation

**CQ 3.2:** _What walls on drawing "PL-001" face north or east?_

```sparql
PREFIX : <https://example.org/aec-ontology#>

SELECT ?wall ?label ?dirLabel ?lengthRW ?thicknessRW
WHERE {
  :PL001  :depictsElement      ?wall ;
          :northArrowAngle     ?northAngle ;
          :scaleRatio          ?scaleRatio .

  ?wall   a                    :Wall ;
          :elementLabel        ?label ;
          :wallLengthRealWorld ?lengthRW ;
          :wallThicknessRealWorld ?thicknessRW ;
          :hasFacingDirection  ?dir .

  ?dir    :directionLabel      ?dirLabel .

  VALUES ?dirLabel { "North" "East" }
}
```

---

**CQ 4.3:** _Does the real-world length of wall "W-03" equal its on-drawing length multiplied by the scale ratio?_

```sparql
PREFIX : <https://example.org/aec-ontology#>

SELECT ?wall ?onDrawingLen ?scaleRatio ?realWorldLen
       ((?onDrawingLen * ?scaleRatio) AS ?computed)
       (ABS(?realWorldLen - ?onDrawingLen * ?scaleRatio) AS ?delta)
WHERE {
  ?drawing  :depictsElement        ?wall ;
            :scaleRatio            ?scaleRatio .

  ?wall     :elementLabel          "W-03" ;
            :wallLengthOnDrawing   ?onDrawingLen ;
            :wallLengthRealWorld   ?realWorldLen .
}
```

This query demonstrates the traceability of the dual-layer model: on-drawing value × scale ratio = real-world value, and any discrepancy (`?delta`) can be detected.

---

**CQ-I 1:** _North- or east-facing walls on Structural Plan drawings in project "X"_

```sparql
PREFIX : <https://example.org/aec-ontology#>

SELECT ?drawing ?drawingNumber ?wall ?label ?dirLabel
       ?lengthRW ?thicknessRW ?northAngle
WHERE {
  ?drawing  :belongsToProject      :ProjectX ;
            :hasDiscipline         ?disc ;
            :hasDrawingType        ?dtype ;
            :depictsElement        ?wall ;
            :drawingNumber         ?drawingNumber ;
            :northArrowAngle       ?northAngle .

  ?disc     :disciplineCode        "Structural" .
  ?dtype    :typeLabel             "Plan" .

  ?wall     a                      :Wall ;
            :elementLabel          ?label ;
            :wallLengthRealWorld   ?lengthRW ;
            :wallThicknessRealWorld ?thicknessRW ;
            :hasFacingDirection    ?dir .

  ?dir      :directionLabel        ?dirLabel .

  VALUES ?dirLabel { "North" "East" }
}
ORDER BY ?drawingNumber ?label
```

---

## 6. Traceability Matrix

|OWL Term|CQ(s)|FR(s)|UC|
|---|---|---|---|
|`:northArrowAngle`|CQ 1.1, CQ 1.3, CQ-I 3|FR 1|UC-07|
|`:scaleRatio`|CQ 1.2, CQ 4.1, CQ 4.3|FR 2|UC-07|
|`:BuildingElement`|CQ 2.x|FR 3, FR 4|UC-07|
|`:Wall`|CQ 2.x, CQ 3.x, CQ 4.x, CQ 5.x, CQ-I x|FR 3, FR 4, FR 5, FR 6|UC-07|
|`:FacingDirection`|CQ 3.x, CQ 5.x, CQ-I x|FR 6|UC-07|
|`:depictsElement`|CQ 2.x, CQ 3.x, CQ 4.x, CQ 5.x, CQ-I x|FR 4|UC-07|
|`:isDepictedOnDrawing`|CQ 2.3|FR 4|UC-07|
|`:hasFacingDirection`|CQ 3.x, CQ 5.x, CQ-I x|FR 6, FR 8|UC-07|
|`:elementLabel`|CQ 2.3, CQ 3.3, CQ 4.1|FR 3|UC-07|
|`:wallLengthOnDrawing`|CQ 4.1, CQ 4.3|FR 5|UC-07|
|`:wallThicknessOnDrawing`|CQ 4.1|FR 5|UC-07|
|`:wallLengthRealWorld`|CQ 4.1, CQ 4.2, CQ 4.3, CQ 5.x, CQ-I 1, CQ-I 2|FR 5, FR 10|UC-07|
|`:wallThicknessRealWorld`|CQ 4.1, CQ-I 1|FR 5|UC-07|
|`:wallAngleOnDrawing`|CQ 3.3, CQ-I 3|FR 7|UC-07|
|`:directionLabel`|CQ 3.x, CQ 5.2, CQ-I 2|FR 6|UC-07|

---

## 7. Future Extension Notes

### 7.1 Cross-Drawing Element Identity Resolution

Each `Wall` instance is currently bound to one drawing. A future `owl:SymmetricProperty` `:sameElementAs` could link the same physical wall across drawings.

### 7.2 Precise Azimuth

The current design uses eight directions plus optional `wallAngleOnDrawing`. A future `:realWorldAzimuth` (`xsd:decimal`, 0–360°) could store the computed precise bearing directly.

### 7.3 Other Building Element Types

The `BuildingElement` superclass provides an extension point for `:Column`, `:Beam`, `:Slab`, `:Door`, `:Window` and other subclasses in future use cases.

### 7.4 Measurement Ontology Integration

Currently uses `xsd:decimal` (mm by convention). A future extension may integrate QUDT / OM for multi-unit support and unit-conversion reasoning.

---

_End of ORSD — UC-07 v 0.2_