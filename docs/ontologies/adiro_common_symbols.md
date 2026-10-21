# Adiro Common Symbols

<div class="adiro-actions" markdown="span">
<details class="adiro-version">
<summary class="md-button">Version 5.0.0 (latest)</summary>
<ul>
<li><a href="./" class="adiro-version-current" aria-current="page">5.0.0 (latest)</a></li>
<li><a href="../aec_common_symbols/">aec_common_symbols 4.0.1</a></li>
<li><a href="../aec_common_symbols/4.0.0/">aec_common_symbols 4.0.0</a></li>
<li><a href="../aec_common_symbols/3.0.1/">aec_common_symbols 3.0.1</a></li>
<li><a href="../aec_common_symbols/3.0.0/">aec_common_symbols 3.0.0</a></li>
<li><a href="../aec_common_symbols/2.0.0/">aec_common_symbols 2.0.0</a></li>
<li><a href="../aec_common_symbols/1.0.0/">aec_common_symbols 1.0.0</a></li>
</ul>
</details>
[![OntoCanvas](https://raw.githubusercontent.com/alelom/OntoCanvas/main/OntoCanvas.png){ .ontocanvas-icon } Open in OntoCanvas](https://alelom.github.io/OntoCanvas/?onto=https://w3id.org/adiro/adiro_common_symbols.html){ .md-button target=_blank }
[:material-file-document-outline: TTL source](https://w3id.org/adiro/adiro_common_symbols.ttl){ .md-button }
[:material-file-code: pyLODE HTML](https://w3id.org/adiro/adiro_common_symbols.html){ .md-button }
</div>

Reusable symbols that appear across disciplines, such as dimensions, grids, levels, and reference symbols. Every symbol is a kind of drawing element from the drawing-metadata module. The discipline modules build on these shared symbols.

- **IRI:** `https://w3id.org/adiro/adiro_common_symbols`
- **Versioned IRI:** `https://w3id.org/adiro/adiro_common_symbols/5.0.0`
- **Imports:** `adiro_drawing_metadata`

## Interactive view

<iframe src="https://alelom.github.io/OntoCanvas/?onto=https://w3id.org/adiro/adiro_common_symbols.html" title="Adiro Common Symbols in OntoCanvas" loading="lazy" style="width: 100%; height: 480px; border: 1px solid var(--md-default-fg-color--lightest); border-radius: 4px;"></iframe>

## Dependencies

Arrows point from an ontology to the ontologies it imports; the current ontology is highlighted.

```mermaid
%%{init: {"themeCSS": ".base .nodeLabel,.base .nodeLabel p,.base text,.base tspan{fill:#9ecbff !important;color:#9ecbff !important}.current .nodeLabel,.current .nodeLabel p,.current text,.current tspan{fill:#16305f !important;color:#16305f !important}"} }%%
graph BT
    adiro_provenance["Adiro Provenance"]
    adiro_geometry["Adiro Geometry"]
    adiro_drawing_metadata["Adiro Drawing Metadata"]
    adiro_common_symbols["Adiro Common Symbols"]
    adiro_domain_common["Adiro Domain Common"]
    adiro_facade_domain["Adiro Facade Domain"]
    adiro_geometry --> adiro_provenance
    adiro_drawing_metadata --> adiro_geometry
    adiro_drawing_metadata --> adiro_provenance
    adiro_common_symbols --> adiro_drawing_metadata
    adiro_domain_common --> adiro_drawing_metadata
    adiro_facade_domain --> adiro_domain_common
    adiro_facade_domain --> adiro_drawing_metadata
    click adiro_provenance "../adiro_provenance/" "Adiro Provenance reference page"
    click adiro_geometry "../adiro_geometry/" "Adiro Geometry reference page"
    click adiro_drawing_metadata "../adiro_drawing_metadata/" "Adiro Drawing Metadata reference page"
    click adiro_common_symbols "../adiro_common_symbols/" "Adiro Common Symbols reference page"
    click adiro_domain_common "../adiro_domain_common/" "Adiro Domain Common reference page"
    click adiro_facade_domain "../adiro_facade_domain/" "Adiro Facade Domain reference page"
    classDef base fill:#16305f,stroke:#0e2247,stroke-width:2px,color:#9ecbff;
    class adiro_provenance,adiro_geometry,adiro_drawing_metadata,adiro_domain_common,adiro_facade_domain base;
    classDef current fill:#f58a1f,stroke:#16305f,stroke-width:3px,color:#16305f;
    class adiro_common_symbols current;
```

## Classes

### Dimension {#Dimension}

A dimension line or dimension annotation on a drawing, indicating measurements or distances.

- **IRI:** `https://w3id.org/adiro/adiro_common_symbols#Dimension`
- **Sub class of:** `metadata:DrawingElement`

*Example images:*

![Dimension — example](https://w3id.org/adiro/adiro_common_symbols/exampleImage/Dimension_01.png)

### Grid {#Grid}

A grid line or grid system used for alignment and reference in architectural drawings.

- **IRI:** `https://w3id.org/adiro/adiro_common_symbols#Grid`
- **Sub class of:** `metadata:DrawingElement`

*Example images:*

![Grid — example](https://w3id.org/adiro/adiro_common_symbols/exampleImage/Grid_01.png)

### ReferenceSymbol {#ReferenceSymbol}

A symbol drawn on a Layout that references another Layout (on the same or a different DrawingSheet). Replaces the earlier Callout class. Typical instances include Detail Markers, Section Markers, and Elevation Markers. The marker type is not modelled — it is derivable from the target Layout's LayoutContentType.

- **IRI:** `https://w3id.org/adiro/adiro_common_symbols#ReferenceSymbol`
- **Sub class of:** `metadata:ReferenceExpression`

*Example images:*

![ReferenceSymbol — example](https://w3id.org/adiro/adiro_common_symbols/exampleImage/ReferenceSymbol_01.png)

## Object Properties

### hasReferenceSymbol {#hasReferenceSymbol}

A Layout contains one or more ReferenceSymbols. To navigate from a symbol back to the Layout it is drawn on, use the SPARQL inverse path ^csymbol:hasReferenceSymbol - ADIRO declares no named inverse properties and no owl:inverseOf axioms (see GitHub issue #21).

- **IRI:** `https://w3id.org/adiro/adiro_common_symbols#hasReferenceSymbol`
- **Sub property of:** `metadata:contains`
- **Domain:** `metadata:Layout`
- **Range:** [ReferenceSymbol](#ReferenceSymbol)

### referencesLayout {#referencesLayout}

Target Layout — the Layout this ReferenceSymbol points to. The target is Layout-level, not DrawingSheet-level. To find the symbols pointing AT a Layout, use the SPARQL inverse path ^csymbol:referencesLayout - ADIRO declares no named inverse properties and no owl:inverseOf axioms (see GitHub issue #21).

- **IRI:** `https://w3id.org/adiro/adiro_common_symbols#referencesLayout`
- **Domain:** [ReferenceSymbol](#ReferenceSymbol)
- **Range:** `metadata:Layout`
