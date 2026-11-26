# Changelog — adiro_geometry

Per-module SemVer. See [../docs/contribute/versioning/](../docs/contribute/versioning/).
Format: [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Changed
- **The module is licensed CC BY 4.0** ([#276](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/276)), not GPL-3.0: `dcterms:license` names <https://creativecommons.org/licenses/by/4.0/>. Reuse needs attribution only, so another ontology can import or extend its terms under its own licence. Earlier releases keep the licence they were released under. `LICENSING.md` says what in the repository is under which licence. No IRI, axiom or term changes.
- **The header carries the metadata vocabulary catalogues read** ([#284](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/284)): `vann:preferredNamespacePrefix` and `vann:preferredNamespaceUri`, `dcterms:issued` (the first release under this name) and `dcterms:modified` (the latest release, which the release cut now keeps up to date). `dcterms:description` is the module's introduction, the same text as its `rdfs:comment`; it was an older, shorter text that said something else. No IRI, axiom or term changes.

## [3.1.1] — 2026-11-26

### Changed
- **A term's definition is a `skos:definition`, and `rdfs:comment` is its commentary** ([#273](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/273)). For each of the module's twelve terms (`BoundingBox`, `CoordinateFrame` and their properties) the first sentence of its comment, which says what the term is, is now its `skos:definition`, and the rest of the comment stays in `rdfs:comment`; `profileRef`, whose comment is one sentence, has a `skos:definition` and no `rdfs:comment`. Three definitions are adjusted so that each stands alone on the page's *Definition* row: `CoordinateFrame` names its three datatype properties (`coordinateSpace`, `unit`, `profileRef`) instead of saying "below", and the examples in the definitions of `BoundingBox` and `coversRegion` (a title-block field's caption; "usually `page_display_pt`") move to the start of their comments. No IRI, axiom or label changes. The definitions are tagged `@en`; the comments, like those of the other modules, carry no language tag. Downstream consumers that read a term's `rdfs:comment` as its definition may need adjustments. A comment now continues its definition: where it starts with "this" or "it" (the comments of `hasBoundingBox` and `inCoordinateFrame`), the word refers to the term the definition has just named, so read a comment together with its definition. The `Geometry` stub of the GeoSPARQL class is not ADIRO's to define and is unchanged.
- **The prefix of the module's names is `adgeom:`** ([#289](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/289)), not `geom:`, and the module's own use of the provenance prefix is `adprov:`. A prefix is a label: no IRI changes.

## [3.1.0] — 2026-10-29

### Added
- **What a model saw** ([#239](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/239)). Every image of a page an extraction feeds to a model is a pixel `CoordinateFrame` with its resolution, the new **`resolutionDpi`** (a decimal); a crop is a frame limited to a region, the new **`coversRegion`** (frame → `BoundingBox`); a step records the frame it used with `prov:used`. An image that is kept is an `aprov:DrawingFile` linked to its frame by the new **`imageOf`**. No crop class and no transform term: between frames there is only a uniform scale. `CoordinateFrame`'s definition says so.

## [3.0.0] — 2026-10-21

### Changed
- **BREAKING: renamed from `aec_geometry`** ([#171](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/171)). The module, its ontology IRI and the IRI of every term it defines now use `adiro_geometry` (`https://w3id.org/adiro/adiro_geometry`) instead of `aec_geometry`; the title says "ADIRO" instead of "AEC". Nothing else changes: the terms, their definitions and their axioms are those of `aec_geometry`'s final release, whose version this release follows with a MAJOR bump. Every release of the old module stays published at its own IRI and is named here with `owl:priorVersion`; its history is in [its changelog](aec_geometry.md). The example images are published under the new module's path. `migration/aec_to_adiro.ttl` maps each old term IRI to the new one, and `scripts/migrate_aec_to_adiro.py` rewrites a graph or a list of links. Downstream consumers need to move to the new IRIs, including the annotation tooling, which reads the class IRIs and the labelling annotations.

