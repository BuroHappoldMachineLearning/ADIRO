# Changelog — adiro_drawing_metadata

Per-module SemVer. See [../docs/contribute/versioning/](../docs/contribute/versioning/).
Format: [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

## [7.1.0] — 2026-11-06

### Changed
- **Every field kind is an `aprov:FieldKind`** ([#254](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/254)): the 17 concepts of the `TitleblockFieldScheme` and the sentinel `UnidentifiedField` are typed `aprov:FieldKind` as well as `skos:Concept`, which stays written on each, so a query that selects field kinds by either type, or by `skos:inScheme`, finds them.
- **The scheme's definitions are shorter and say how a field kind relates to the rest** ([#254](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/254)): an assertion names its kind and the region it was read from, and an accepted value is promoted to the property its kind maps to, whose domain is the class of the subject the value is about (such as `Titleblock`); the scheme itself names no class. The public-content note and the unique-synonym rule are kept, in fewer words, and the sentinel's definition is shorter.
- **The field kinds are on the module's documentation page** ([#255](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/255)), in a Concepts section with their names in each language, examples, value type and mapped property.

## [7.0.1] — 2026-10-29

### Changed
- **The labelling annotations' definitions say they are named for their application** ([#216](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/216)): `isComputerVisionLabel` and `isComputerVisionOptionalLabel` serve computer-vision annotation, and another application gets its own pair. The Turtle comment block above them, which said so along with the history of their names (recorded under [#141](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/141) in the `aec_drawing_metadata` changelog), is removed: a `#` comment is not part of the graph any tool reads. Downstream consumers need no change.

## [7.0.0] — 2026-10-21

### Changed
- **BREAKING: renamed from `aec_drawing_metadata`** ([#171](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/171)). The module, its ontology IRI and the IRI of every term it defines now use `adiro_drawing_metadata` (`https://w3id.org/adiro/adiro_drawing_metadata`) instead of `aec_drawing_metadata`; the title says "ADIRO" instead of "AEC". Nothing else changes: the terms, their definitions and their axioms are those of `aec_drawing_metadata`'s final release, whose version this release follows with a MAJOR bump. Every release of the old module stays published at its own IRI and is named here with `owl:priorVersion`; its history is in [its changelog](aec_drawing_metadata.md). The example images are published under the new module's path. `migration/aec_to_adiro.ttl` maps each old term IRI to the new one, and `scripts/migrate_aec_to_adiro.py` rewrites a graph or a list of links. Downstream consumers need to move to the new IRIs, including the annotation tooling, which reads the class IRIs and the labelling annotations.

