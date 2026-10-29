# Changelog — adiro_drawing_metadata

Per-module SemVer. See [../docs/contribute/versioning/](../docs/contribute/versioning/).
Format: [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Changed
- **The labelling annotations' definitions say they are named for their application** ([#216](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/216)): `isComputerVisionLabel` and `isComputerVisionOptionalLabel` serve computer-vision annotation, and another application gets its own pair. The Turtle comment block above them, which said so along with the history of their names (recorded under [#141](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/141) in the `aec_drawing_metadata` changelog), is removed: a `#` comment is not part of the graph any tool reads. Downstream consumers need no change.

## [7.0.0] — 2026-10-21

### Changed
- **BREAKING: renamed from `aec_drawing_metadata`** ([#171](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/171)). The module, its ontology IRI and the IRI of every term it defines now use `adiro_drawing_metadata` (`https://w3id.org/adiro/adiro_drawing_metadata`) instead of `aec_drawing_metadata`; the title says "ADIRO" instead of "AEC". Nothing else changes: the terms, their definitions and their axioms are those of `aec_drawing_metadata`'s final release, whose version this release follows with a MAJOR bump. Every release of the old module stays published at its own IRI and is named here with `owl:priorVersion`; its history is in [its changelog](aec_drawing_metadata.md). The example images are published under the new module's path. `migration/aec_to_adiro.ttl` maps each old term IRI to the new one, and `scripts/migrate_aec_to_adiro.py` rewrites a graph or a list of links. Downstream consumers need to move to the new IRIs, including the annotation tooling, which reads the class IRIs and the labelling annotations.

