# Aec Provenance

[![OntoCanvas](https://raw.githubusercontent.com/alelom/OntoCanvas/main/OntoCanvas.png){ .ontocanvas-icon } Open in OntoCanvas](https://alelom.github.io/OntoCanvas/?onto=https://burohappoldmachinelearning.github.io/ADIRO/aec_provenance.html){ .md-button target=_blank }
[:material-file-document-outline: TTL source](https://burohappoldmachinelearning.github.io/ADIRO/aec_provenance.ttl){ .md-button }
[:material-file-code: pyLODE HTML](https://burohappoldmachinelearning.github.io/ADIRO/aec_provenance.html){ .md-button }

Foundational, domain-neutral vocabulary for representing an inferred/extracted assertion together with its provenance and confidence. It exists so that a value read off a drawing (a title-block field, a detected symbol, ...) can be modelled as a first-class assertion carrying: which region asserted it, what produced it, from where, when, and with what confidence - independently of the value itself. Imported by the drawing modules (e.g. aec_drawing_metadata); aligned to W3C PROV-O for interoperability.

- **IRI:** `https://w3id.org/adiro/aec_provenance`
- **Version:** 1.0.0

## Dependencies

Arrows point from an ontology to the ontologies it imports; the current ontology is highlighted.

```mermaid
%%{init: {"themeCSS": ".base .nodeLabel,.base .nodeLabel p,.base text,.base tspan{fill:#9ecbff !important;color:#9ecbff !important}.current .nodeLabel,.current .nodeLabel p,.current text,.current tspan{fill:#16305f !important;color:#16305f !important}"} }%%
graph BT
    aec_provenance["Aec Provenance"]
    aec_drawing_metadata["Aec Drawing Metadata"]
    aec_common_symbols["Aec Common Symbols"]
    aec_domain_common["Aec Domain Common"]
    aec_facade_domain["Aec Facade Domain"]
    aec_dano_alignment["Aec Dano Alignment"]
    aec_drawing_metadata --> aec_provenance
    aec_common_symbols --> aec_drawing_metadata
    aec_domain_common --> aec_common_symbols
    aec_domain_common --> aec_drawing_metadata
    aec_facade_domain --> aec_common_symbols
    aec_facade_domain --> aec_domain_common
    aec_facade_domain --> aec_drawing_metadata
    aec_dano_alignment --> aec_drawing_metadata
    aec_dano_alignment --> aec_provenance
    click aec_provenance "../aec_provenance/" "Aec Provenance reference page"
    click aec_drawing_metadata "../aec_drawing_metadata/" "Aec Drawing Metadata reference page"
    click aec_common_symbols "../aec_common_symbols/" "Aec Common Symbols reference page"
    click aec_domain_common "../aec_domain_common/" "Aec Domain Common reference page"
    click aec_facade_domain "../aec_facade_domain/" "Aec Facade Domain reference page"
    click aec_dano_alignment "../aec_dano_alignment/" "Aec Dano Alignment reference page"
    classDef base fill:#16305f,stroke:#0e2247,stroke-width:2px,color:#9ecbff;
    class aec_drawing_metadata,aec_common_symbols,aec_domain_common,aec_facade_domain,aec_dano_alignment base;
    classDef current fill:#f58a1f,stroke:#16305f,stroke-width:3px,color:#16305f;
    class aec_provenance current;
```

## Classes

### Agent {#Agent}

- **IRI:** `http://www.w3.org/ns/prov#Agent`

### Field Assertion {#FieldAssertion}

A single reified assertion that some source makes a value-claim about a field kind. Reifying the claim (rather than attaching the value straight to a subject) lets each printed occurrence carry its own provenance - which region asserted it (assertedBy), what produced it (hasInferenceMeta), and with what confidence (hasConfidence) - independently of the value it states. The value is a literal (hasLiteralValue) for datatype-valued fields or an entity (hasValueEntity) for object-valued fields. Validated assertions are promoted to direct statements on the subject downstream; conflicting assertions across sources are surfaced, not silently merged.

- **IRI:** `https://w3id.org/adiro/aec_provenance#FieldAssertion`

### Inference Meta {#InferenceMeta}

Provenance metadata for an inferred or extracted assertion: what produced it (inferredBy / inferredWith), the source it was derived from (inferredFrom), and when (inferredAt). Modelled as a separate object so several assertions can share one inference record and so provenance can be added without touching the value. Analogous to DANO's DrawingElementMeta, but aligned to PROV-O.

- **IRI:** `https://w3id.org/adiro/aec_provenance#InferenceMeta`

## Object Properties

### assertedBy {#assertedBy}

The source that makes this assertion - typically the drawing region it was read from (e.g. a Titleblock or a Layout). This is the provenance that lets the same field kind asserted by different regions be distinguished (e.g. a sheet-level scale in the title block versus a per-layout scale in a layout corner), which a fixed domain on a per-field property cannot express.

- **IRI:** `https://w3id.org/adiro/aec_provenance#assertedBy`
- **Domain:** [Field Assertion](#FieldAssertion)

### assertsFieldKind {#assertsFieldKind}

The field kind (a SKOS concept in a field-kind scheme, e.g. a title-block field such as Scale or Client) that this assertion is about. Keeping the kind as a referenced concept - rather than a bespoke property per field - is what lets names/synonyms live on the concept and keeps the number of relationships small.

- **IRI:** `https://w3id.org/adiro/aec_provenance#assertsFieldKind`
- **Domain:** [Field Assertion](#FieldAssertion)
- **Range:** `skos:Concept`

### hasInferenceMeta {#hasInferenceMeta}

Links an assertion to the InferenceMeta describing what produced it, from where, and when.

- **IRI:** `https://w3id.org/adiro/aec_provenance#hasInferenceMeta`
- **Domain:** [Field Assertion](#FieldAssertion)
- **Range:** [Inference Meta](#InferenceMeta)

### hasValueEntity {#hasValueEntity}

For object-valued field kinds, the entity that is the asserted value - e.g. a Person or Organisation. Used instead of hasLiteralValue when the field references a thing rather than states a string, which is what makes cross-sheet questions ('everything checked by X') answerable.

- **IRI:** `https://w3id.org/adiro/aec_provenance#hasValueEntity`
- **Domain:** [Field Assertion](#FieldAssertion)

### inferredBy {#inferredBy}

The actor, organisation or software that produced this inference. Aligned to prov:wasAttributedTo.

- **IRI:** `https://w3id.org/adiro/aec_provenance#inferredBy`
- **Sub property of:** [wasAttributedTo](#wasAttributedTo)
- **Domain:** [Inference Meta](#InferenceMeta)
- **Range:** [Agent](#Agent)

### inferredFrom {#inferredFrom}

The source the value was derived from - e.g. the origin file, page or region. Aligned to prov:wasDerivedFrom.

- **IRI:** `https://w3id.org/adiro/aec_provenance#inferredFrom`
- **Sub property of:** [wasDerivedFrom](#wasDerivedFrom)
- **Domain:** [Inference Meta](#InferenceMeta)

### inferredWith {#inferredWith}

The algorithm or model (ideally with version) used to produce this inference. Distinct from inferredBy, which names the responsible actor; inferredWith names the tool.

- **IRI:** `https://w3id.org/adiro/aec_provenance#inferredWith`
- **Domain:** [Inference Meta](#InferenceMeta)

### wasAttributedTo {#wasAttributedTo}

- **IRI:** `http://www.w3.org/ns/prov#wasAttributedTo`

### wasDerivedFrom {#wasDerivedFrom}

- **IRI:** `http://www.w3.org/ns/prov#wasDerivedFrom`

## Datatype Properties

### capturedCaption {#capturedCaption}

The caption/label text exactly as printed on the drawing for this assertion (e.g. 'Verfasser', 'Dwg. Desc.'). Retained even when the field kind is uncertain, so the ground truth of what was on the sheet is never lost and mapping can be revisited later.

- **IRI:** `https://w3id.org/adiro/aec_provenance#capturedCaption`
- **Domain:** [Field Assertion](#FieldAssertion)
- **Range:** `xsd:string`

### generatedAtTime {#generatedAtTime}

- **IRI:** `http://www.w3.org/ns/prov#generatedAtTime`

### hasConfidence {#hasConfidence}

Confidence of the inference behind this assertion, as a decimal in [0,1]. Carried on the assertion (an individual) rather than on a triple, which keeps confidence in the graph without requiring RDF-star or statement reification.

- **IRI:** `https://w3id.org/adiro/aec_provenance#hasConfidence`
- **Domain:** [Field Assertion](#FieldAssertion)
- **Range:** `xsd:decimal`

### hasLiteralValue {#hasLiteralValue}

For datatype-valued field kinds, the literal value asserted, kept verbatim (not normalised, expanded or translated at extraction time).

- **IRI:** `https://w3id.org/adiro/aec_provenance#hasLiteralValue`
- **Domain:** [Field Assertion](#FieldAssertion)
- **Range:** `rdfs:Literal`

### inferredAt {#inferredAt}

The time the inference was produced. Aligned to prov:generatedAtTime.

- **IRI:** `https://w3id.org/adiro/aec_provenance#inferredAt`
- **Sub property of:** [generatedAtTime](#generatedAtTime)
- **Domain:** [Inference Meta](#InferenceMeta)
- **Range:** `xsd:dateTime`

## Annotation Properties

### expectedRange {#expectedRange}

On a field-kind concept: the expected type of its asserted value - a datatype (e.g. xsd:string, xsd:date) for literal-valued fields, or a class (e.g. Person, Organisation) for object-valued fields. Signals whether an assertion of this kind uses hasLiteralValue or hasValueEntity.

- **IRI:** `https://w3id.org/adiro/aec_provenance#expectedRange`

### mapsToFieldProperty {#mapsToFieldProperty}

On a field-kind concept: the canonical ADIRO property that a validated assertion of this field kind is promoted to (the bridge from the reified assertion to a direct statement on the subject). Annotation only - the promotion is performed by tooling on validation, not by reasoning.

- **IRI:** `https://w3id.org/adiro/aec_provenance#mapsToFieldProperty`
