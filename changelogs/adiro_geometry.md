# Changelog — adiro_geometry

Per-module SemVer. See [../docs/contribute/versioning/](../docs/contribute/versioning/).
Format: [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

## [3.1.0] — 2026-10-29

### Added
- **What a model saw** ([#239](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/239)). Every image of a page an extraction feeds to a model is a pixel `CoordinateFrame` with its resolution, the new **`resolutionDpi`** (a decimal); a crop is a frame limited to a region, the new **`coversRegion`** (frame → `BoundingBox`); a step records the frame it used with `prov:used`. An image that is kept is an `aprov:DrawingFile` linked to its frame by the new **`imageOf`**. No crop class and no transform term: between frames there is only a uniform scale. `CoordinateFrame`'s definition says so.

## [3.0.0] — 2026-10-21

### Changed
- **BREAKING: renamed from `aec_geometry`** ([#171](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/171)). The module, its ontology IRI and the IRI of every term it defines now use `adiro_geometry` (`https://w3id.org/adiro/adiro_geometry`) instead of `aec_geometry`; the title says "ADIRO" instead of "AEC". Nothing else changes: the terms, their definitions and their axioms are those of `aec_geometry`'s final release, whose version this release follows with a MAJOR bump. Every release of the old module stays published at its own IRI and is named here with `owl:priorVersion`; its history is in [its changelog](aec_geometry.md). The example images are published under the new module's path. `migration/aec_to_adiro.ttl` maps each old term IRI to the new one, and `scripts/migrate_aec_to_adiro.py` rewrites a graph or a list of links. Downstream consumers need to move to the new IRIs, including the annotation tooling, which reads the class IRIs and the labelling annotations.

