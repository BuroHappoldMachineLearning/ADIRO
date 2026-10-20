# Changelog — aec_geometry

Per-module SemVer. See [../docs/contribute/versioning/](../docs/contribute/versioning/).
Format: [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

_Pending changes accumulate here. `owl:versionInfo` / `owl:versionIRI` are bumped only at a release cut._

### Changed
- **BREAKING: a `CoordinateFrame` states only its coordinate convention** ([#192](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/192)). `pageIndex`, `frameArtifactRef`, `pdfRotationDeg`, `displayWidthPt` and `displayHeightPt` leave it: they are facts about a page of a file, and move to `aec_provenance:FilePage` (the page number is counted from 1, the file is a `DrawingFile` with its content hash). The frame points to its page with the new `describesPage`. A page can now have several frames (the primary `page_display_pt` in points, and `px` for raster evidence) without repeating the page. Downstream consumers that read these properties from a frame need to adjust.
- `profileRef`'s comment no longer lists the page extent among what a profile defines.


## [1.0.1] — 2026-10-20

### Changed
- The `rdfs:comment` of `bboxXYXY` no longer names a repository file path; it points to the public issue [#91](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/91) instead, because a path is not an address that resolves and a release cannot be corrected afterwards. Annotation change only; no term, domain or range changes.


## [1.0.0] — 2026-10-09

### Added
- **New foundational module `aec_geometry` (v1.0.0)** ([#90](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/90)).
  Domain-neutral geometry for locating a detection on a drawing page:
  - **`BoundingBox`** — a rectangular region, held as an xyxy string (`bboxXYXY`, aligned to the Croissant
    `cr:BoundingBox` `XYXY` format token). Modelled as a first-class, **provenance-bearing** individual:
    `rdfs:subClassOf geo:Geometry` **and** `aec_provenance:InferredEntity`, so a box carries its own
    `aprov:hasInferenceMeta` (a detector, or a human annotator) and `aprov:hasConfidence` (detector score) —
    distinct from the confidence in a value read at that box.
  - **`CoordinateFrame`** — the context that makes coordinates interpretable: `coordinateSpace`
    (primary `page_display_pt` — top-left origin, x-right, y-down), `unit`, `frameArtifactRef`, `pageIndex`
    (0-based), `displayWidthPt`/`displayHeightPt`, `pdfRotationDeg`, `profileRef`.
  - Object properties: `inCoordinateFrame` (`geo:Geometry` → `CoordinateFrame`) and `hasBoundingBox`
    (→ `BoundingBox`; domain-neutral, used on the `Titleblock` region — title-block **fields are not**
    individually localised, only the title block itself carries a box).
  - **GeoSPARQL `geo:Geometry` reused as a local typing stub** (option 1A per
    `external-ontology-imports.md`); no `owl:imports`, resolved offline via `catalog-v001.xml`. WKT
    serialisation and spatial queries are **deferred** ([#36](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/36)).
  - `owl:imports aec_provenance`.
- **Shared across use cases by design:** UC-01 (title-block field regions) and UC-03 (reference-symbol
  geometry) use the same `BoundingBox` / `CoordinateFrame` model. This PR introduces only what UC-01 needs;
  UC-03-specific geometry (coordinate transforms, crop/symbol metrics, clickable/navigation geometry) is left
  for the UC-03 work and slots into this module without conflict. Rationale:
  [croissant-comparison.md](../docs/specification/design-decisions/croissant-comparison.md).

### Notes
- All additive; first in-repo version. `owl:versionInfo` is set at the first release cut (tag `aec_geometry-v1.0.0`).
