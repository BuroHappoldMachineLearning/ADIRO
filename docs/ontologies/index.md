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
    adiro_drawing_symbology["Adiro Drawing Symbology"]
    adiro_discipline_core["Adiro Discipline Core"]
    adiro_facade_discipline["Adiro Facade Discipline"]
    adiro_geometry --> adiro_provenance
    adiro_drawing_metadata --> adiro_geometry
    adiro_drawing_metadata --> adiro_provenance
    adiro_drawing_symbology --> adiro_drawing_metadata
    adiro_discipline_core --> adiro_drawing_metadata
    adiro_facade_discipline --> adiro_discipline_core
    adiro_facade_discipline --> adiro_drawing_metadata
    click adiro_provenance "adiro_provenance/" "Adiro Provenance reference page"
    click adiro_geometry "adiro_geometry/" "Adiro Geometry reference page"
    click adiro_drawing_metadata "adiro_drawing_metadata/" "Adiro Drawing Metadata reference page"
    click adiro_drawing_symbology "adiro_drawing_symbology/" "Adiro Drawing Symbology reference page"
    click adiro_discipline_core "adiro_discipline_core/" "Adiro Discipline Core reference page"
    click adiro_facade_discipline "adiro_facade_discipline/" "Adiro Facade Discipline reference page"
    classDef base fill:#16305f,stroke:#0e2247,stroke-width:2px,color:#9ecbff;
    class adiro_provenance,adiro_geometry,adiro_drawing_metadata,adiro_drawing_symbology,adiro_discipline_core,adiro_facade_discipline base;
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

-   ### [Adiro Drawing Symbology](adiro_drawing_symbology.md)

    The symbols and marks a drawing uses, shared by every discipline: reusable symbols and text that appear across disciplines, such as dimensions, grids, levels and references to another layout or drawing: the graphical reference symbol, the inline and standalone reference expressions, and the occurrences of drawing and layout identifiers they are made of. Every one is a kind of drawing element from the drawing-metadata module. The discipline modules build on them.

    *Imports: adiro_drawing_metadata*

-   ### [Adiro Discipline Core](adiro_discipline_core.md)

    The vocabulary that several discipline modules share: materials, section shapes and properties, structural components and loads, and the discipline classes. It sits between the drawing symbology and the discipline-specific modules, holding abstractions that more than one discipline reuses, so they are defined once.

    *Imports: adiro_drawing_metadata*

-   ### [Adiro Facade Discipline](adiro_facade_discipline.md)

    Facade-engineering concepts and symbols, such as curtain-wall systems and glazing units. It is a discipline-specific module at the end of the dependency chain, building on the shared drawing, symbology, and discipline-core vocabularies.

    *Imports: adiro_discipline_core, adiro_drawing_metadata*

</div>
