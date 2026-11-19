# Changelog — checks

The data-validation shapes (`data-validation/`) and the UC-01 competency queries, released together as their own versioned
artefact ([#240](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/240)): tag `checks-v<semver>`, served under
`https://w3id.org/adiro/checks/<semver>/`. How to pin them, and what a version bump means here, is in
[../docs/contribute/data-validation.md](../docs/contribute/data-validation.md).
Format: [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Changed
- **The UC-03 composition shapes follow the reference terms to `adiro_drawing_symbology`** ([#277](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/277), with [#271](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/271)): the inline-reference shape targets `InlineLayoutDrawingReference` of `adiro_drawing_symbology` and, still, the `InlineLayoutSheetReference` of `adiro_drawing_metadata`; the mention counts and the `denotesDrawingSheet` limit read the classes and the property from either module, so data typed with the IRIs the terms had in `adiro_drawing_metadata` is checked as before. Its two messages say "inline layout and drawing reference" instead of "inline layout and sheet reference".

## [1.0.0] — 2026-10-29

### Added
- **The first release of the checks** ([#240](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/240)). Every shape file of `data-validation/`, the public-release shapes included, and every recorded UC-01 competency query (CQ 1.3 to CQ 11.4, and the promotion; the integration example CQ-I 1 needs a reasoner and is not one), each in its own `.rq` file, with a `manifest.json` naming the module versions they were tested with.
