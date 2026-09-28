# Locating a title block: bounding boxes, coordinate frames and provenance — a worked example

> Companion to the [`aec_geometry`](../ontologies/aec_geometry.md) and [`aec_provenance`](../ontologies/aec_provenance.md)
> reference pages. It shows, end to end, how a title block's **region**, its **coordinate frame**, and an
> extracted **field value** fit together — and how the page coordinates are meant to be read. Introduced with
> [#90](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/90); the model is shared with the UC-03
> geometry work (tracked in [#93](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/93)).

## 1. The shape, end to end

An extraction pipeline reads an A1 landscape sheet, detects the title-block region, and reads the client field
from inside it. In ADIRO that is:

```turtle
@prefix geom:  <https://w3id.org/adiro/aec_geometry#> .
@prefix aprov: <https://w3id.org/adiro/aec_provenance#> .
@prefix md:    <https://w3id.org/adiro/aec_drawing_metadata#> .
@prefix ex:    <https://example.org/adiro/demo#> .
@prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .

ex:sheet-A101 a md:DrawingSheet ;
    md:contains ex:tb-A101 ;
    geom:hasCoordinateFrame ex:frame-A101 .          # the sheet owns its page frame

ex:frame-A101 a geom:CoordinateFrame ;
    geom:coordinateSpace "page_display_pt" ;         # top-left origin, x right, y down, points
    geom:unit "pt" ;
    geom:frameArtifactRef "sha256:9f2c…" ;           # pins the exact PDF page
    geom:pageIndex 0 ;
    geom:displayWidthPt 2384 ; geom:displayHeightPt 1684 ;
    geom:pdfRotationDeg 0 .

ex:tb-A101 a md:Titleblock ;
    geom:hasBoundingBox ex:bbox-tb-A101 .            # the TITLE BLOCK carries a box…

ex:bbox-tb-A101 a geom:BoundingBox ;
    geom:bboxXYXY "[1900, 1400, 2360, 1660]" ;       # …its region, in the sheet's frame
    geom:inCoordinateFrame ex:frame-A101 ;
    aprov:hasConfidence 0.97 ;                        # confidence in the BOX (the detector)
    aprov:hasInferenceMeta [ a aprov:InferenceMeta ;
        aprov:inferredWith <https://example.org/models/titleblock-detector@2.1> ;
        aprov:inferredAt "2026-09-20T14:03:00Z"^^xsd:dateTime ] .

ex:fa-client-A101 a aprov:FieldAssertion ;           # a value read from within that title block
    aprov:assertsFieldKind md:ClientField ;
    aprov:hasLiteralValue "Acme Corp" ;
    aprov:capturedCaption "Client" ;
    aprov:assertedBy ex:tb-A101 ;                     # read FROM the title-block region
    aprov:hasConfidence 0.88 ;                        # confidence in the VALUE (a different model)
    aprov:hasInferenceMeta [ a aprov:InferenceMeta ;
        aprov:inferredWith <https://example.org/models/vlm-extractor@5> ] .
```

Two things are worth reading off this:

- **Only the title block is localised, not each field.** `hasBoundingBox` sits on the `Titleblock` region; the
  field values are read from *within* that one region (`assertedBy ex:tb-A101`) and are not given their own
  boxes.
- **Two independent inferences, two confidences.** The detector found the *box* (0.97, via a detector model);
  a different model read the *value* (0.88, via a VLM). Each is an `InferredEntity`, so each carries its own
  `hasInferenceMeta` / `hasConfidence`. A **human** annotation is the same shape with `inferredWith` omitted and
  the agent (`aprov:inferredBy`) a person.

## 2. Reading the numbers: coordinate frames

`bboxXYXY "[1900, 1400, 2360, 1660]"` is meaningless on its own — the `CoordinateFrame` it points at is what
makes it interpretable. ADIRO's primary space is **`page_display_pt`**: **origin top-left, x increasing
rightwards, y increasing downwards, in points** (1 pt = 1/72 inch). So the box is a rectangle from
`(1900, 1400)` (its top-left corner) to `(2360, 1660)` (bottom-right) — the bottom-right strip of a
2384 × 1684 pt (A1 landscape) page.

The same rectangle looks different in other spaces, which is exactly why the frame is explicit:

| Space | Top-left corner of the box | How it relates to `page_display_pt` |
|---|---|---|
| **`page_display_pt`** (ADIRO primary) | `(1900, 1400)` | — origin top-left, y down |
| Native PDF user space | `(1900, 284)` | origin **bottom-left**: `y_native = displayHeight − y_display = 1684 − 1400` (corners also swap in y) |
| Rendered raster @ 150 DPI | `(≈3958, ≈2917) px` | scale by `150/72 ≈ 2.083`; DPI changes pixels but **not** the pt box |

Notes:

- **We store `page_display_pt`** as the single primary representation (it matches the extraction pipeline's page
  geometry). Native-PDF and pixel values are *derived* views; record them as evidence if a downstream writer
  needs them, but do not silently interchange the coordinate-space names.
- **Rotation is already baked in.** `pdfRotationDeg` is recorded for interpretation/validation, but
  `page_display_pt` coordinates already include the page mapping — do not rotate them again. A page at a
  different rotation or file version is a *different* `CoordinateFrame`.
- **GeoSPARQL, lightly.** `BoundingBox` is a subclass of `geo:Geometry` so tools recognise it as a spatial
  shape, but ADIRO does not adopt a GeoSPARQL CRS or spatial-query profile here — WKT serialisation and spatial
  queries are deferred ([#36](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/36)). Page points are
  not longitude/latitude.

## 3. Why this shape

Modelling the box as a first-class, provenance-bearing class (rather than a bare literal on the field) is what
lets ADIRO answer "*where* is the title block, *who* said so, and *how sure*" separately from "*what* does the
title block say, and how sure". It also keeps UC-01 and UC-03 on one representation: UC-03 reference symbols
will carry `BoundingBox` / `CoordinateFrame` the same way, adding only their own geometry roles
([#93](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/93)). The reasoning for reusing GeoSPARQL and
for keeping Croissant at the dataset layer is in [external ontology imports](external-ontology-imports.md) and
the [Croissant comparison](croissant-comparison.md).
