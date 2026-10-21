# Ontologies

Reference documentation for each ADIRO ontology, generated from the Turtle sources. Each page also links to an interactive HTML view (pyLODE) and to OntoCanvas.

## Dependencies

The ADIRO ontologies are modular and build on one another via `owl:imports`. Arrows point from an ontology to the ontologies it imports.

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
    click adiro_provenance "adiro_provenance/" "Adiro Provenance reference page"
    click adiro_geometry "adiro_geometry/" "Adiro Geometry reference page"
    click adiro_drawing_metadata "adiro_drawing_metadata/" "Adiro Drawing Metadata reference page"
    click adiro_common_symbols "adiro_common_symbols/" "Adiro Common Symbols reference page"
    click adiro_domain_common "adiro_domain_common/" "Adiro Domain Common reference page"
    click adiro_facade_domain "adiro_facade_domain/" "Adiro Facade Domain reference page"
    classDef base fill:#16305f,stroke:#0e2247,stroke-width:2px,color:#9ecbff;
    class adiro_provenance,adiro_geometry,adiro_drawing_metadata,adiro_common_symbols,adiro_domain_common,adiro_facade_domain base;
```

## Available ontologies

<div class="grid cards" markdown>

-   ### [Adiro Provenance](adiro_provenance.md)

    Foundational, domain-neutral module for provenance. It lets any value inferred from a drawing be recorded as an assertion that carries its own source, confidence, and how it was produced, aligned to W3C PROV-O. The drawing modules import it.

-   ### [Adiro Geometry](adiro_geometry.md)

    Foundational, domain-neutral module for geometry. It records where something sits on a drawing page as a bounding box, read against an explicit coordinate frame. Each box carries its own provenance and confidence. It reuses GeoSPARQL, is imported by the drawing modules, and is shared across use cases.

    *Imports: adiro_provenance*

-   ### [Adiro Drawing Metadata](adiro_drawing_metadata.md)

    The core drawing vocabulary. It describes the structure of a drawing sheet: its layouts, title block, revisions, and the fields read from them. It imports the provenance module (which also holds the file, the page and the agents) and the geometry module (where a title block's region is located), and the discipline modules build on it.

    *Imports: adiro_geometry, adiro_provenance*

-   ### [Adiro Common Symbols](adiro_common_symbols.md)

    Reusable symbols that appear across disciplines, such as dimensions, grids, levels, and reference symbols. Every symbol is a kind of drawing element from the drawing-metadata module. The discipline modules build on these shared symbols.

    *Imports: adiro_drawing_metadata*

-   ### [Adiro Domain Common](adiro_domain_common.md)

    Concepts shared by several engineering domains. It sits between the common symbols and the discipline-specific modules, holding abstractions that more than one domain reuses, so they are defined once.

    *Imports: adiro_drawing_metadata*

-   ### [Adiro Facade Domain](adiro_facade_domain.md)

    Facade-engineering concepts and symbols, such as curtain-wall systems and glazing units. It is a discipline-specific module at the end of the dependency chain, building on the shared drawing, symbol, and domain vocabularies.

    *Imports: adiro_domain_common, adiro_drawing_metadata*

</div>
