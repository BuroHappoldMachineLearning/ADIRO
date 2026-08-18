# Aec Common Symbols

[![OntoCanvas](https://raw.githubusercontent.com/alelom/OntoCanvas/main/OntoCanvas.png){ .ontocanvas-icon } Open in OntoCanvas](https://alelom.github.io/OntoCanvas/?onto=https://burohappoldmachinelearning.github.io/ADIRO/aec_common_symbols.html){ .md-button target=_blank }
[:material-file-document-outline: TTL source](https://burohappoldmachinelearning.github.io/ADIRO/aec_common_symbols.ttl){ .md-button }
[:material-file-code: pyLODE HTML](https://burohappoldmachinelearning.github.io/ADIRO/aec_common_symbols.html){ .md-button }

Cross-discipline layout content. Generic symbol classes like dimensions, reference symbols, grids, etc. (mostly reusable non-domain symbols). All symbols are subclasses of DrawingElement from the drawing metadata ontology.

- **IRI:** `https://w3id.org/adiro/aec_common_symbols`
- **Version:** 2.0.0
- **Imports:** `aec_drawing_metadata`

## Dependencies

Arrows point from an ontology to the ontologies it imports; the current ontology is highlighted.

```mermaid
%%{init: {"themeCSS": ".base .nodeLabel,.base .nodeLabel p,.base text,.base tspan{fill:#9ecbff !important;color:#9ecbff !important}.current .nodeLabel,.current .nodeLabel p,.current text,.current tspan{fill:#16305f !important;color:#16305f !important}"} }%%
graph BT
    aec_drawing_metadata["Aec Drawing Metadata"]
    aec_titleblock["Aec Titleblock"]
    aec_common_symbols["Aec Common Symbols"]
    aec_domain_common["Aec Domain Common"]
    aec_facade_domain["Aec Facade Domain"]
    aec_titleblock --> aec_drawing_metadata
    aec_common_symbols --> aec_drawing_metadata
    aec_domain_common --> aec_common_symbols
    aec_domain_common --> aec_drawing_metadata
    aec_facade_domain --> aec_common_symbols
    aec_facade_domain --> aec_domain_common
    aec_facade_domain --> aec_drawing_metadata
    classDef base fill:#16305f,stroke:#0e2247,stroke-width:2px,color:#9ecbff;
    class aec_drawing_metadata,aec_titleblock,aec_domain_common,aec_facade_domain base;
    classDef current fill:#f58a1f,stroke:#16305f,stroke-width:3px,color:#16305f;
    class aec_common_symbols current;
```

## Classes

### Dimension {#Dimension}

A dimension line or dimension annotation on a drawing, indicating measurements or distances.

- **IRI:** `https://w3id.org/adiro/aec_common_symbols#Dimension`
- **Sub class of:** `metadata:DrawingElement`

### Grid {#Grid}

A grid line or grid system used for alignment and reference in architectural drawings.

- **IRI:** `https://w3id.org/adiro/aec_common_symbols#Grid`
- **Sub class of:** `metadata:DrawingElement`

### ReferenceSymbol {#ReferenceSymbol}

A symbol drawn on a Layout that references another Layout (on the same or a different DrawingSheet). Replaces the earlier Callout class. Typical instances include Detail Markers, Section Markers, and Elevation Markers. The marker type is not modelled — it is derivable from the target Layout's LayoutContentType.

- **IRI:** `https://w3id.org/adiro/aec_common_symbols#ReferenceSymbol`
- **Sub class of:** `metadata:DrawingElement`

## Object Properties

### appearsOn {#appearsOn}

Source Layout — the Layout on which this ReferenceSymbol is drawn.

- **IRI:** `https://w3id.org/adiro/aec_common_symbols#appearsOn`
- **Domain:** [ReferenceSymbol](#ReferenceSymbol)
- **Range:** `metadata:Layout`
- **Inverse of:** [hasReferenceSymbol](#hasReferenceSymbol)

### hasReferenceSymbol {#hasReferenceSymbol}

Inverse of appearsOn. A Layout contains one or more ReferenceSymbols.

- **IRI:** `https://w3id.org/adiro/aec_common_symbols#hasReferenceSymbol`
- **Sub property of:** `metadata:contains`
- **Domain:** `metadata:Layout`
- **Range:** [ReferenceSymbol](#ReferenceSymbol)

### isReferencedBy {#isReferencedBy}

Inverse of referencesLayout. A Layout that is the target of one or more ReferenceSymbols.

- **IRI:** `https://w3id.org/adiro/aec_common_symbols#isReferencedBy`
- **Domain:** `metadata:Layout`
- **Range:** [ReferenceSymbol](#ReferenceSymbol)

### referencesLayout {#referencesLayout}

Target Layout — the Layout this ReferenceSymbol points to. The target is Layout-level, not DrawingSheet-level.

- **IRI:** `https://w3id.org/adiro/aec_common_symbols#referencesLayout`
- **Domain:** [ReferenceSymbol](#ReferenceSymbol)
- **Range:** `metadata:Layout`
- **Inverse of:** [isReferencedBy](#isReferencedBy)
