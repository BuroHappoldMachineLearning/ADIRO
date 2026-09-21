# Aec Dano Alignment

[![OntoCanvas](https://raw.githubusercontent.com/alelom/OntoCanvas/main/OntoCanvas.png){ .ontocanvas-icon } Open in OntoCanvas](https://alelom.github.io/OntoCanvas/?onto=https://burohappoldmachinelearning.github.io/ADIRO/aec_dano_alignment.html){ .md-button target=_blank }
[:material-file-document-outline: TTL source](https://burohappoldmachinelearning.github.io/ADIRO/aec_dano_alignment.ttl){ .md-button }
[:material-file-code: pyLODE HTML](https://burohappoldmachinelearning.github.io/ADIRO/aec_dano_alignment.html){ .md-button }

OPTIONAL compatibility layer mapping ADIRO terms to the Drawing Analysis Ontology (DAnO, https://w3id.org/dano). Nothing in the ADIRO core imports this module and no ADIRO core module mentions DAnO, so a consumer who wants the DAnO crosswalk loads this file explicitly and everyone else never sees it. Every mapping is annotation-level (skos:closeMatch) and carries no logical force: no rdfs:subPropertyOf alignment to a DAnO term is available, and the DAnO IRIs are not declared here or anywhere else in ADIRO. Kept separate from the core for lifecycle reasons - DAnO has no releases, and an unreleased third-party vocabulary should not force a version bump on a module downstream consumers pin. Full rationale and per-term verdicts: https://burohappoldmachinelearning.github.io/ADIRO/design-decisions/dano-comparison/

- **IRI:** `https://w3id.org/adiro/aec_dano_alignment`
- **Version:** 1.0.0
- **Imports:** `aec_drawing_metadata`, `aec_provenance`
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
    class aec_provenance,aec_drawing_metadata,aec_common_symbols,aec_domain_common,aec_facade_domain base;
    classDef current fill:#f58a1f,stroke:#16305f,stroke-width:3px,color:#16305f;
    class aec_dano_alignment current;
```
