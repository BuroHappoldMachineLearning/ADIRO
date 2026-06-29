
> **⚠️ Draft v0.1 — not yet aligned with the current ontology. This use case will be revised in a follow-up PR.**

> **Methodology:** LOT (Linked Open Terms) **Use Case ID:** UC-06 **Version:** 0.1 (draft)

---

## 1. Use Case

|Field|Content|
|---|---|
|**ID**|UC-06|
|**Title**|Drawing Content Aggregation & Hazardous Material Identification|
|**Statement**|As an engineer, I want to aggregate and summarise the content of many different drawings so they can be grouped by material — especially hazardous materials — for inclusion in a report or archiving, supporting Building Safety Act compliance review.|
|**Primary Actor**|Engineer|
|**Goal**|Given a project, retrieve all materials mentioned across its drawings, identify hazardous materials (by name or symbol), and support aggregation queries by material, hazard classification, and drawing — enabling the generation of safety review reports.|

---

## 2. Information Needs Analysis

### 2.1 Entities

|Entity|Rationale|
|---|---|
|Drawing|The carrier on which materials appear; already defined in UC-01.|
|Material|A building material mentioned or depicted on a drawing. Each material has a name and optionally an abbreviation/symbol.|
|HazardClassification|Controlled vocabulary distinguishing the hazard category of a material (e.g. Asbestos-containing, Lead-based, Non-hazardous).|

> **Design note — Material as a first-class entity:** `Material` must be an independent class, not a simple string property on `Drawing`. Three reasons: (1) the same material may appear on multiple drawings, requiring cross-drawing aggregation; (2) a material carries its own attributes (name, symbol/abbreviation, hazard classification); (3) under the Building Safety Act scenario, filtering and counting by material dimension requires material to exist as an independent node in the knowledge graph.

> **Design note — HazardClassification as controlled vocabulary:** Hazard classification uses a controlled vocabulary rather than free text, ensuring consistent querying across drawings and projects. Initial values include `Asbestos-containing`, `Lead-based`, `Toxic`, `Flammable`, `Non-hazardous`. This vocabulary can be extended in the future as regulations evolve.

> **Design note — Reuse from UC-01:** This use case reuses `Drawing`, `Project`, `belongsToProject`, `Discipline` and other terms already defined in UC-01. The report aggregation scenario requires filtering drawings by project and discipline, then further filtering by material and hazard classification — these cross-use-case combined queries are reflected in CQ Group I.

### 2.2 Attributes

|Attribute|Entity|Expected Type|Notes|
|---|---|---|---|
|Material name|Material|xsd:string|Full material name, e.g. `"Asbestos Insulating Board"`, `"Lead Paint"` |
|Material symbol|Material|xsd:string|Abbreviation or symbol notation used on drawings, e.g. `"ACM"`, `"Pb"`, `"AIB"` |
|Hazard label|HazardClassification|xsd:string|e.g. `"Asbestos-containing"`, `"Lead-based"` |

### 2.3 Relations

|Relation|Domain|Range|Notes|
|---|---|---|---|
|depicts material|Drawing|Material|The drawing contains an annotation or depiction of the material|
|is depicted on|Material|Drawing|Inverse of `depictsMaterial` |
|has hazard classification|Material|HazardClassification|The hazard category of the material|

---

## 3. Functional Requirements

**Obligation levels:** MUST = mandatory for current scope; SHOULD = important but deferrable; MAY = optional extension.

---

**FR 1 — Material as a First-Class Entity**

> The ontology MUST represent materials as distinct entities, each carrying a name and an optional symbol/abbreviation, such that materials can be aggregated and retrieved across multiple drawings.

- Source: UC-06
- Derived terms: `:Material`, `:materialName`, `:materialSymbol`

---

**FR 2 — Drawing–Material Association**

> The ontology MUST represent the relationship between a drawing and the materials depicted or annotated on it, such that all materials on a given drawing can be retrieved, and all drawings depicting a given material can be retrieved.

- Source: UC-06
- Derived terms: `:depictsMaterial`, `:isDepictedOn`

---

**FR 3 — Hazard Classification**

> The ontology MUST represent the hazard classification of each material using a controlled vocabulary (e.g. Asbestos-containing, Lead-based, Toxic, Flammable, Non-hazardous), such that drawings and materials can be filtered by hazard category.

- Source: UC-06
- Derived terms: `:HazardClassification`, `:hasHazardClassification`, `:hazardLabel`

---

**FR 4 — Search by Material Symbol**

> The ontology MUST represent the abbreviation or symbol notation of a material, such that engineers can retrieve the corresponding material and the drawings on which it appears by the shorthand symbols commonly found on drawings (e.g. `"ACM"`, `"Pb"`, `"AIB"`).

- Source: UC-06
- Derived terms: `:materialSymbol`

---

**FR 5 — Cross-Drawing Material Aggregation**

> The ontology MUST support material aggregation queries across multiple drawings within a project, such that summary reports like "which drawings in project X contain asbestos-containing materials" can be generated.

- Source: UC-06
- Obligation: MUST
- Note: This requirement introduces no new terms; it is satisfied by combining `:depictsMaterial`, `:hasHazardClassification`, and `:belongsToProject` from UC-01.

---

**FR 6 — Material Occurrence Counting**

> The ontology SHOULD support counting the number of drawings in which a given material appears within a project, such that safety review reports can quantify the distribution scope of hazardous materials.

- Source: UC-06
- Obligation: SHOULD
- Note: Implemented via SPARQL `COUNT` aggregation; no additional OWL terms required.

---

## 4. Competency Questions

### CQ Group 1 — Material Discovery (validates FR 1, FR 2)

|ID|Competency Question|
|---|---|
|CQ 1.1|What materials are depicted on drawing "GA-001"?|
|CQ 1.2|On which drawings does the material named "Asbestos Insulating Board" appear?|
|CQ 1.3|What distinct materials are mentioned across all drawings in project "X"?|

---

### CQ Group 2 — Symbol Search (validates FR 4)

|ID|Competency Question|
|---|---|
|CQ 2.1|What material has the symbol "ACM"?|
|CQ 2.2|On which drawings does the material with symbol "Pb" appear?|

---

### CQ Group 3 — Hazard Classification Filtering (validates FR 3)

|ID|Competency Question|
|---|---|
|CQ 3.1|What materials are classified as "Asbestos-containing"?|
|CQ 3.2|Does drawing "GA-001" contain any hazardous materials?|
|CQ 3.3|What hazard classification categories are represented in project "X"?|

---

### CQ Group 4 — Cross-Drawing Aggregation (validates FR 5, FR 6)

|ID|Competency Question|
|---|---|
|CQ 4.1|How many drawings in project "X" contain asbestos-containing materials?|
|CQ 4.2|Which drawings in project "X" depict lead-based materials?|
|CQ 4.3|For each hazardous material in project "X", how many drawings does it appear on?|

---

### CQ Group I — Integration / Multi-field Queries

|ID|Competency Question|FRs exercised|
|---|---|---|
|CQ-I 1|What asbestos-containing materials appear on Structural discipline drawings in project "X"?|FR 2, FR 3, UC-01/FR 2, UC-01/FR 5|
|CQ-I 2|Which drawings approved by "J. Smith" in project "X" contain hazardous materials?|FR 2, FR 3, UC-01/FR 2, UC-01/FR 4|
|CQ-I 3|List all hazardous materials in project "X" with their drawing numbers, grouped by hazard classification.|FR 1, FR 2, FR 3, FR 5, UC-01/FR 1, UC-01/FR 2|

---

## 5. SPARQL Validation

**CQ 4.3:** _For each hazardous material in project "X", how many drawings does it appear on?_

```sparql
PREFIX : <https://example.org/aec-ontology#>

SELECT ?material ?materialName ?hazardLabel (COUNT(DISTINCT ?drawing) AS ?drawingCount)
WHERE {
  ?drawing    :belongsToProject      :ProjectX ;
              :depictsMaterial        ?material .

  ?material   :materialName          ?materialName ;
              :hasHazardClassification ?hazard .

  ?hazard     :hazardLabel           ?hazardLabel .

  FILTER (?hazardLabel != "Non-hazardous")
}
GROUP BY ?material ?materialName ?hazardLabel
ORDER BY DESC(?drawingCount)
```

All filter conditions map to defined properties. The query confirms that FR 3 (Hazard Classification) and FR 5 (Cross-Drawing Aggregation) are fully covered by the current term inventory.

---

**CQ-I 1:** _What asbestos-containing materials appear on Structural discipline drawings in project "X"?_

```sparql
PREFIX : <https://example.org/aec-ontology#>

SELECT DISTINCT ?material ?materialName ?drawingNumber
WHERE {
  ?drawing    :belongsToProject      :ProjectX ;
              :hasDiscipline         ?disc ;
              :depictsMaterial        ?material ;
              :drawingNumber         ?drawingNumber .

  ?disc       :disciplineCode        "Structural" .

  ?material   :materialName          ?materialName ;
              :hasHazardClassification ?hazard .

  ?hazard     :hazardLabel           "Asbestos-containing" .
}
```

This query combines UC-06 terms (`:depictsMaterial`, `:hasHazardClassification`) with UC-01 terms (`:belongsToProject`, `:hasDiscipline`), validating the feasibility of cross-use-case integration queries.

---

## 6. Traceability Matrix

|OWL Term|CQ(s)|FR(s)|UC|
|---|---|---|---|
|`:Material`|CQ 1.x, CQ 2.x, CQ 3.x, CQ 4.x, CQ-I x|FR 1, FR 2, FR 3, FR 4, FR 5|UC-06|
|`:HazardClassification`|CQ 3.x, CQ 4.x, CQ-I x|FR 3|UC-06|
|`:depictsMaterial`|CQ 1.1, CQ 1.2, CQ 1.3, CQ 4.x, CQ-I x|FR 2, FR 5|UC-06|
|`:isDepictedOn`|CQ 1.2, CQ 2.2|FR 2|UC-06|
|`:hasHazardClassification`|CQ 3.x, CQ 4.x, CQ-I x|FR 3|UC-06|
|`:materialName`|CQ 1.2, CQ 1.3, CQ 3.1, CQ 4.3, CQ-I 1, CQ-I 3|FR 1|UC-06|
|`:materialSymbol`|CQ 2.1, CQ 2.2|FR 1, FR 4|UC-06|
|`:hazardLabel`|CQ 3.1, CQ 3.3, CQ 4.3, CQ-I 3|FR 3|UC-06|

---

## 7. Future Extension Notes

### 7.1 Material Quantity and Location

The current design models "which material appears on a drawing" (qualitative), not "how much" or "where." A future extension may introduce:

```turtle
# Future extension — requires a dedicated Use Case and CQs
:MaterialOccurrence  a  owl:Class .
:hasMaterialOccurrence  rdfs:domain  :Drawing ;
                        rdfs:range   :MaterialOccurrence .
:occurrenceOf           rdfs:domain  :MaterialOccurrence ;
                        rdfs:range   :Material .
:hasQuantity            rdfs:domain  :MaterialOccurrence ;
                        rdfs:range   xsd:string .    # e.g. "50 mm thick", "2 layers"
:hasLocation            rdfs:domain  :MaterialOccurrence ;
                        rdfs:range   :LayoutRegion .  # Aligns with UC-02 geometric-layer extension
```

This extension would enable queries like "What is the thickness of the asbestos board on drawing GA-001?" It does not conflict with the current semantic-layer design and can be introduced additively when a new Use Case justifies it.

### 7.2 Regulatory Clause Linking

A future extension may link `HazardClassification` to specific regulatory clauses (e.g. Building Safety Act Section X, Control of Asbestos Regulations 2012) to support compliance audit traceability. This extension is beyond the current scope.

---

_End of ORSD — UC-06 v 0.1_