# Changelog — adiro_common_symbols

Per-module SemVer. See [../docs/contribute/versioning/](../docs/contribute/versioning/).
Format: [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Deprecated
- **This module is deprecated, and this is its final release** ([#281](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/281)). It is replaced by `adiro_drawing_symbology` (`https://w3id.org/adiro/adiro_drawing_symbology`), the module that holds the symbols and marks a drawing uses, shared by every discipline, under a name that says what it holds. The new module continues this module's version history and every term keeps its local name; only the namespace changes. Nothing in this module changes: the header says `owl:deprecated true` and `dcterms:isReplacedBy` the new module. The new module is introduced in a following release.

## [5.0.0] — 2026-10-21

### Changed
- **BREAKING: renamed from `aec_common_symbols`** ([#171](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/171)). The module, its ontology IRI and the IRI of every term it defines now use `adiro_common_symbols` (`https://w3id.org/adiro/adiro_common_symbols`) instead of `aec_common_symbols`; the title says "ADIRO" instead of "AEC". Nothing else changes: the terms, their definitions and their axioms are those of `aec_common_symbols`'s final release, whose version this release follows with a MAJOR bump. Every release of the old module stays published at its own IRI and is named here with `owl:priorVersion`; its history is in [its changelog](aec_common_symbols.md). The example images are published under the new module's path. `migration/aec_to_adiro.ttl` maps each old term IRI to the new one, and `scripts/migrate_aec_to_adiro.py` rewrites a graph or a list of links. Downstream consumers need to move to the new IRIs, including the annotation tooling, which reads the class IRIs and the labelling annotations.

