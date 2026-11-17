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
[![OntoCanvas](https://burohappoldmachinelearning.github.io/OntoCanvas/OntoCanvas.png){ .ontocanvas-icon } Open in OntoCanvas](https://burohappoldmachinelearning.github.io/OntoCanvas/?onto=https://w3id.org/adiro/adiro_common_symbols.html){ .md-button target=_blank }
[:material-file-document-outline: TTL source](https://w3id.org/adiro/adiro_common_symbols.ttl){ .md-button }
[:material-file-code: pyLODE HTML](https://w3id.org/adiro/adiro_common_symbols.html){ .md-button }
</div>

Reusable symbols and text that appear across disciplines, such as dimensions, grids, levels and references to another layout or drawing: the graphical reference symbol, the inline and standalone reference expressions, and the occurrences of drawing and layout identifiers they are made of. Every one is a kind of drawing element from the drawing-metadata module. The discipline modules build on them.

- **IRI:** `https://w3id.org/adiro/adiro_common_symbols`
- **Versioned IRI:** `https://w3id.org/adiro/adiro_common_symbols/5.0.0`
- **Imports:** `adiro_drawing_metadata`

## Interactive view

<iframe src="https://burohappoldmachinelearning.github.io/OntoCanvas/?onto=https://w3id.org/adiro/adiro_common_symbols.html" title="Adiro Common Symbols in OntoCanvas" loading="lazy" style="width: 100%; height: 480px; border: 1px solid var(--md-default-fg-color--lightest); border-radius: 4px;"></iframe>

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
- **Sub class of:** [`metadata:DrawingElement`](adiro_drawing_metadata.md#DrawingElement)

*Example images:*

![Dimension — example](https://w3id.org/adiro/adiro_common_symbols/exampleImage/Dimension_01.png)

### Drawing identifier mention {#DrawingIdentifierMention}

One evidenced occurrence of drawing-identifier (sheet-identifier) text on a source drawing, distinct from the [DrawingSheet](adiro_drawing_metadata.md#DrawingSheet) that the text may denote. Source-text evidence and an immutable source identity are admission requirements for exported UC-03 mentions. Precise localisation is required for navigation, not for an independently accepted sheet resolution: an unlocalisable text block may retain its accepted [denotesDrawingSheet](#denotesDrawingSheet) edge without a fabricated bounding box or clickable link. Unresolved candidates remain in extraction evidence; no geometry cardinality axiom is imposed.

- **IRI:** `https://w3id.org/adiro/adiro_common_symbols#DrawingIdentifierMention`
- **Sub class of:** [`metadata:DrawingElement`](adiro_drawing_metadata.md#DrawingElement)

*Example images:*

![Drawing identifier mention — example](https://w3id.org/adiro/adiro_common_symbols/exampleImage/DrawingIdentifierMention_01.png)

### Grid {#Grid}

A grid line or grid system used for alignment and reference in architectural drawings.

- **IRI:** `https://w3id.org/adiro/adiro_common_symbols#Grid`
- **Sub class of:** [`metadata:DrawingElement`](adiro_drawing_metadata.md#DrawingElement)

*Example images:*

![Grid — example](https://w3id.org/adiro/adiro_common_symbols/exampleImage/Grid_01.png)

### Inline Layout and Drawing Reference {#InlineLayoutDrawingReference}

A complete inline textual expression relating layout number(s) to a sheet number, such as '1, 3, 5 & 7/S601'. The component mentions retain their own identities; accepted [Layout](adiro_drawing_metadata.md#Layout) targets are connected separately by [inlineReferencesLayout](#inlineReferencesLayout). Expected composition: one sheet-identifier mention and at least one layout-identifier mention, attached with contains; this is checked as an application-profile condition, not asserted as an OWL restriction.

- **IRI:** `https://w3id.org/adiro/adiro_common_symbols#InlineLayoutDrawingReference`
- **Sub class of:** [Reference expression](#ReferenceExpression)

*Example images:*

![Inline Layout and Drawing Reference — example](https://w3id.org/adiro/adiro_common_symbols/exampleImage/InlineLayoutDrawingReference_01.png)

### Layout identifier mention {#LayoutIdentifierMention}

One evidenced occurrence of layout-identifier text (a small integer or letter), distinct from a target [Layout](adiro_drawing_metadata.md#Layout). A complete inline reference may contain several such occurrences, attached with contains; no target is inferred from matching text alone.

- **IRI:** `https://w3id.org/adiro/adiro_common_symbols#LayoutIdentifierMention`
- **Sub class of:** [`metadata:DrawingElement`](adiro_drawing_metadata.md#DrawingElement)

*Example images:*

![Layout identifier mention — example](https://w3id.org/adiro/adiro_common_symbols/exampleImage/LayoutIdentifierMention_01.png)

### Reference expression {#ReferenceExpression}

A complete source reference expression, whether graphical, inline or a standalone sheet-number reference. This superclass groups those forms for queries; it does not require a second individual around any of them.

- **IRI:** `https://w3id.org/adiro/adiro_common_symbols#ReferenceExpression`
- **Sub class of:** [`metadata:DrawingElement`](adiro_drawing_metadata.md#DrawingElement)

### ReferenceSymbol {#ReferenceSymbol}

A symbol drawn on a [Layout](adiro_drawing_metadata.md#Layout) that references another Layout (on the same or a different [DrawingSheet](adiro_drawing_metadata.md#DrawingSheet)). Replaces the earlier Callout class. Typical instances include Detail Markers, Section Markers, and Elevation Markers. The marker type is not modelled — it is derivable from the target Layout's [LayoutContentType](adiro_drawing_metadata.md#LayoutContentType).

- **IRI:** `https://w3id.org/adiro/adiro_common_symbols#ReferenceSymbol`
- **Sub class of:** [Reference expression](#ReferenceExpression)

*Example images:*

![ReferenceSymbol — example](https://w3id.org/adiro/adiro_common_symbols/exampleImage/ReferenceSymbol_01.png)

### Standalone Drawing Reference {#StandaloneDrawingReference}

A drawing-identifier occurrence that itself constitutes a complete reference. One individual is both the [DrawingIdentifierMention](#DrawingIdentifierMention) and the [ReferenceExpression](#ReferenceExpression): no duplicate wrapper, self-directed hasDrawingIdentifierMention edge or second geometry is needed. An ungrouped mention is not automatically standalone merely because its parent has not been identified.

- **IRI:** `https://w3id.org/adiro/adiro_common_symbols#StandaloneDrawingReference`
- **Sub class of:**
    - [Drawing identifier mention](#DrawingIdentifierMention)
    - [Reference expression](#ReferenceExpression)

*Example images:*

![Standalone Drawing Reference — example](https://w3id.org/adiro/adiro_common_symbols/exampleImage/StandaloneDrawingReference_01.png)

## Object Properties

### denotesDrawingSheet {#denotesDrawingSheet}

The accepted [DrawingSheet](adiro_drawing_metadata.md#DrawingSheet) identity denoted by one sheet-number occurrence. It does not assert that a [Layout](adiro_drawing_metadata.md#Layout) target or an output-PDF navigation link was resolved. A mention is expected to have at most one accepted sheet; this is an application-profile condition, not an OWL functional axiom, because a functional axiom would make a reasoner merge two sheets instead of reporting the conflict.

- **IRI:** `https://w3id.org/adiro/adiro_common_symbols#denotesDrawingSheet`
- **Domain:** [Drawing identifier mention](#DrawingIdentifierMention)
- **Range:** [`metadata:DrawingSheet`](adiro_drawing_metadata.md#DrawingSheet)

### hasReferenceSymbol {#hasReferenceSymbol}

A Layout contains one or more [ReferenceSymbol](#ReferenceSymbol)s. To navigate from a symbol back to the [Layout](adiro_drawing_metadata.md#Layout) it is drawn on, use the SPARQL inverse path ^csymbol:hasReferenceSymbol - ADIRO declares no named inverse properties and no owl:inverseOf axioms (see GitHub issue #21).

- **IRI:** `https://w3id.org/adiro/adiro_common_symbols#hasReferenceSymbol`
- **Sub property of:** [`metadata:contains`](adiro_drawing_metadata.md#contains)
- **Domain:** [`metadata:Layout`](adiro_drawing_metadata.md#Layout)
- **Range:** [ReferenceSymbol](#ReferenceSymbol)

### inlineReferencesLayout {#inlineReferencesLayout}

An accepted target [Layout](adiro_drawing_metadata.md#Layout) of an inline layout/sheet reference. Multiple supported targets may be asserted; unresolved members do not acquire target edges.

- **IRI:** `https://w3id.org/adiro/adiro_common_symbols#inlineReferencesLayout`
- **Domain:** [Inline Layout and Drawing Reference](#InlineLayoutDrawingReference)
- **Range:** [`metadata:Layout`](adiro_drawing_metadata.md#Layout)

### referencesLayout {#referencesLayout}

Target Layout — the [Layout](adiro_drawing_metadata.md#Layout) this [ReferenceSymbol](#ReferenceSymbol) points to. The target is Layout-level, not DrawingSheet-level. To find the symbols pointing AT a Layout, use the SPARQL inverse path ^csymbol:referencesLayout - ADIRO declares no named inverse properties and no owl:inverseOf axioms (see GitHub issue #21).

- **IRI:** `https://w3id.org/adiro/adiro_common_symbols#referencesLayout`
- **Domain:** [ReferenceSymbol](#ReferenceSymbol)
- **Range:** [`metadata:Layout`](adiro_drawing_metadata.md#Layout)
