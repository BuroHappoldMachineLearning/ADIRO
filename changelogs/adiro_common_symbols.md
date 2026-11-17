# Changelog — adiro_common_symbols

Per-module SemVer. See [../docs/contribute/versioning/](../docs/contribute/versioning/).
Format: [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- **The UC-03 reference terms are defined here** ([#277](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/277), with [#271](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/271)): `ReferenceExpression` (the superclass of a complete reference, graphical, inline or standalone), `DrawingIdentifierMention`, `LayoutIdentifierMention`, `InlineLayoutDrawingReference` ("Inline Layout and Drawing Reference"), `StandaloneDrawingReference` ("Standalone Drawing Reference"), and the properties `denotesDrawingSheet` and `inlineReferencesLayout`. They were released in `adiro_drawing_metadata` as `ReferenceExpression`, `DrawingIdentifierMention`, `LayoutIdentifierMention`, `InlineLayoutSheetReference`, `StandaloneSheetReference`, `denotesDrawingSheet` and `inlineReferencesLayout`; those IRIs stay there, deprecated and equivalent to the new terms. The definitions, superclasses, example images (also served from this module's folder) and `isComputerVisionLabel` markers are the ones they had. `ReferenceSymbol` is now a subclass of this module's own `ReferenceExpression`. The module's introduction is widened to say it holds the reference terms.
  Downstream consumers may need adjustments: the annotation tooling takes these labels from the class IRIs, so each label is offered from this module, under the new names for the two reference classes.

### Changed
- **`ReferenceSymbol` specialises this module's `ReferenceExpression`** ([#277](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/277)), not the `ReferenceExpression` of `adiro_drawing_metadata`, which is equivalent to it. The meaning is unchanged, but the compatibility diff reads a new superclass IRI as a superclass change, so this module's next release is a MAJOR one.

## [5.0.0] — 2026-10-21

### Changed
- **BREAKING: renamed from `aec_common_symbols`** ([#171](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/171)). The module, its ontology IRI and the IRI of every term it defines now use `adiro_common_symbols` (`https://w3id.org/adiro/adiro_common_symbols`) instead of `aec_common_symbols`; the title says "ADIRO" instead of "AEC". Nothing else changes: the terms, their definitions and their axioms are those of `aec_common_symbols`'s final release, whose version this release follows with a MAJOR bump. Every release of the old module stays published at its own IRI and is named here with `owl:priorVersion`; its history is in [its changelog](aec_common_symbols.md). The example images are published under the new module's path. `migration/aec_to_adiro.ttl` maps each old term IRI to the new one, and `scripts/migrate_aec_to_adiro.py` rewrites a graph or a list of links. Downstream consumers need to move to the new IRIs, including the annotation tooling, which reads the class IRIs and the labelling annotations.

