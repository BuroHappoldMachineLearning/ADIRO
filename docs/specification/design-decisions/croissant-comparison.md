# Croissant, PROV-O and DAnO: what each does, and where Croissant fits ADIRO

> How ADIRO relates to the [Croissant](https://mlcommons.org/working-groups/data/croissant/) metadata format,
> set against PROV-O and DAnO. Background: [#91](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/91).
> The geometry point is carried further by the `aec_geometry` module and
> [#90](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/90).

!!! info "Where the decision lives"
    Background: [#91](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/91). Related design pages:
    [External ontology imports](external-ontology-imports.md), [DAnO comparison](dano-comparison.md),
    [Usage of annotation properties](usage-of-annotation-properties.md). Sources are linked inline and collected
    at the end.

## Summary

**Croissant does not compete with `aec_provenance`; it operates one layer up.** Croissant describes a *dataset*
— a whole corpus: its files, its record/field structure, its splits, its licence, and (via the RAI extension)
how it was collected. PROV-O, DAnO and ADIRO's `aec_provenance` describe *a single claim or detection* — who
inferred this value, from where, when, and with what confidence. A Croissant file answers "what is this dataset
and how do I load it"; an `aec_provenance` `FieldAssertion` answers "how sure are we that *this* title block
says *this* client, and what produced that reading". Both are useful, and they do not overlap where it matters.

In short: **`aec_provenance` (PROV-O-aligned) carries in-graph, per-assertion provenance; Croissant is used at
the dataset-publication and discovery layer; and `aec_geometry`'s bounding box borrows Croissant's `format`
convention ([#90](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/90)) so ADIRO's boxes are
recognised by mainstream ML tooling.**

## 1. What Croissant is

**[Croissant](https://docs.mlcommons.org/croissant/docs/croissant-spec.html)** (MLCommons, v1.0, 2024) is a
JSON-LD metadata format for **ML-ready datasets**, built on **schema.org** (`sc:`) with its own namespace
`cr: <http://mlcommons.org/croissant/>`. Its goals are discoverability, portability (load the same dataset into
PyTorch/TF/JAX), reproducibility, and Responsible AI documentation. It **describes** a dataset; it does not
contain the data (beyond small inline enumerations/examples).

It is organised in four layers:

1. **Dataset metadata** — `sc:Dataset` with `name`, `description`, `url`, `license`, `creator`,
   `datePublished`, `version` (SemVer), `citeAs`, `sha256`, `isLiveDataset`, `dct:conformsTo`.
2. **Resource layer** — `cr:FileObject` (a file: `contentUrl`, `contentSize`, `encodingFormat`, `sha256`,
   `containedIn`) and `cr:FileSet` (a homogeneous set, with `includes`/`excludes` globs).
3. **Structure layer** — `cr:RecordSet` (homogeneous records) of `cr:Field`s. A `Field` carries a `dataType`,
   a `source` (which file/column it comes from), an `extract` method (`column`, `jsonPath`, `fileProperty`…),
   a `transform` (regex/delimiter/jsonQuery), a `format`, `references` (a foreign key to another Field), and
   `repeated`/`subField` for arrays and nesting.
4. **Semantic layer** — ML-specific typing: `cr:Split` (train/val/test), `cr:Label`, and computer-vision
   annotation types **`cr:BoundingBox`** and **`cr:SegmentationMask`**, each with a `format` specifier.

Two features matter for us specifically:

- **Semantic typing of fields.** A `Field`'s `dataType` can be a schema.org type (`sc:Integer`,
  `sc:ImageObject`), a Wikidata entity, **or an external ontology term**, and `equivalentProperty` lets a Field
  declare that it *is* a particular ontology property. This is the hook by which a Croissant dataset can point
  back into ADIRO.
- **The RAI extension** (`rai: <http://mlcommons.org/croissant/RAI/>`) documents the dataset *lifecycle*: data
  collection, labelling protocol, participatory scenarios, safety/fairness, and traceability — i.e. how the
  corpus was produced, at the corpus level.

## 2. What PROV-O is, and how ADIRO already uses it

**[PROV-O](https://www.w3.org/TR/prov-o/)** (W3C Recommendation) is a *generic, granularity-agnostic*
provenance vocabulary: `prov:Entity` (a thing), `prov:Activity` (something that happened), `prov:Agent` (who is
responsible), related by `prov:wasGeneratedBy`, `prov:used`, `prov:wasAssociatedWith`, `prov:endedAtTime`, …
It says nothing about drawings or datasets; it is the shared shape any domain specialises.

`aec_provenance` aligns to it at the **assertion** level: a `FieldAssertion` **is** a `prov:Entity`, an
`InferenceMeta` **is** the `prov:Activity` that generated it (`inferredBy`/`inferredWith`/`inferredFrom`/
`inferredAt`), and confidence lives per-assertion as `hasConfidence`. This is the finest granularity of the
three — one printed field, one claim, its own confidence (the `InferenceMeta` activity may be shared by several
claims).

## 3. What DAnO does

**[DAnO](dano-comparison.md)** models provenance at the **drawing-element** level: a `DrawingElementMeta`
object carrying `inferredBy`/`inferredWith`/`inferredFrom`/`inferredAt` (datatype/string properties) and
`hasConfidence` on the drawing element. ADIRO supersedes these with its own PROV-O-aligned terms (reasons in
the [DAnO comparison](dano-comparison.md)); the point here is only the *granularity*: per detected element,
between Croissant's per-dataset and `aec_provenance`'s per-assertion.

## 4. The crux: they sit at different granularities

| | **Croissant** | **PROV-O** | **DAnO** | **ADIRO `aec_provenance`** |
|---|---|---|---|---|
| Granularity | **Dataset / corpus** | Any (generic) | Per drawing element | **Per assertion (one field value)** |
| Question answered | "What is this dataset, how do I load it, how was it collected?" | "What generated what, by whom?" | "How was this element detected?" | "How sure are we of *this* value, and what read it?" |
| Encoding | JSON-LD on schema.org | OWL/RDF | OWL/RDF | OWL/RDF (Turtle) |
| Provenance depth | Coarse: field←file/column/`extract`/`transform`; `version`; `sha256`; `citeAs`; RAI lifecycle | Full activity/agent model | `inferredBy/With/From/At`, `hasConfidence` | `inferredBy/With/From/At`, `hasConfidence`, `capturedCaption`, per-value |
| Confidence | No per-value confidence | Not built-in | Per element | **Per assertion**, `xsd:decimal [0,1]` |
| Geometry / bbox | **`cr:BoundingBox` + `format` (e.g. `CENTER_XYWH`)** | None | (geometry not its focus) | `aec_geometry:BoundingBox` ([#90](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/90)) |
| Tool recognition | Wide (HF, Kaggle, TFDS, Google Dataset Search) | Wide (semantic web) | Niche | ADIRO-specific |
| Role for ADIRO | **Publish/discover the annotated dataset** | **Aligned to, in the core** | Compared, not reused | **The in-graph provenance model** |

The single most important row is the first: **Croissant answers a question `aec_provenance` never asks, and vice
versa.** Trying to record per-title-block-field confidence in Croissant would be forcing corpus-level metadata
to do assertion-level work; trying to make `aec_provenance` describe a dataset's files and splits would be the
reverse mistake.

## 5. Where each fits ADIRO

- **`aec_provenance` (PROV-O-aligned) is the in-graph provenance model.** It carries the per-assertion
  confidence/agent/activity that UC-01 (and later UC-03) need, and Croissant offers no equivalent.
- **Croissant fits at the dataset-publication layer**, not in the ontology. When an ADIRO-annotated corpus of
  drawings is published (for internal discovery/retrieval, or as a public evaluation dataset for the SPARQL
  competency-question work), a Croissant manifest is how it becomes findable and loadable by standard tooling.
  This is an *application of* ADIRO, not a change *to* it.
- **DAnO stays a documented comparison**, not reused (see the [DAnO comparison](dano-comparison.md)).

## 6. How ADIRO uses Croissant

**In the ontology — the bounding-box `format` convention.** `aec_geometry:BoundingBox` records its rectangle as
an `XYXY` string aligned to Croissant's `cr:BoundingBox` `XYXY` token, so an exporter can map an ADIRO box to
Croissant/CV formats. ADIRO adds what Croissant leaves out: a `CoordinateFrame` (which PDF/page, units and
origin the coordinates use) and the box's own provenance and confidence — a detection or a human annotation,
distinct from confidence in the field *value*. See
[#90](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/90) and
[Bounding boxes and coordinate frames](geometry-coordinate-frames.md).

**For dataset publication — outside the TBox.** When an ADIRO-annotated corpus is published, Croissant makes it
findable and loadable by standard tooling without changing the ontology:

- A **Croissant manifest** models the corpus as a `cr:RecordSet` whose `cr:Field`s are semantically typed back
  into ADIRO field-kinds/properties via `dataType` / `equivalentProperty` (§1). The manifest describes the
  dataset; the semantic types point into ADIRO.
- The **RAI extension** documents the extraction pipeline at corpus level (data collection, labelling protocol).
  It complements the `InferenceMeta` model rather than duplicating it: `InferenceMeta` describes the inference
  *activity* behind a result (and may be shared by several results, with confidence carried per result), while
  RAI describes how the whole corpus was built.
- The **dataset-level vocabulary** ADIRO already uses in its module headers (`dcterms:` title, licence, creator,
  publisher) carries over to a manifest's schema.org / Dublin-Core fields (`license`, `version`, `citeAs`,
  `datePublished`), keeping the metadata consistent from ontology to dataset.

Croissant does not replace `aec_provenance` — it has no per-assertion confidence, agent or activity for an
individual field value — and its terms do not enter the ADIRO TBox: the two meet only at publication time,
through semantic typing that points into ADIRO.

## Open points

For the future dataset-publication work:

- Where a published dataset's Croissant manifest lives — generated by the inference/publication pipeline, or
  checked in alongside a public evaluation dataset.
- Whether the RAI lifecycle documentation sits with the dataset or is cross-referenced from a design page here.

## Sources

- Croissant specification — <https://docs.mlcommons.org/croissant/docs/croissant-spec.html>
- Croissant paper (NeurIPS 2024 D&B) — <https://arxiv.org/abs/2403.19546>
- MLCommons Croissant working group — <https://mlcommons.org/working-groups/data/croissant/>
- W3C PROV-O — <https://www.w3.org/TR/prov-o/>
- ADIRO [DAnO comparison](dano-comparison.md) and [External ontology imports](external-ontology-imports.md)
