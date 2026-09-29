# Croissant, PROV-O and DAnO: what each does, and where Croissant fits ADIRO

> Recorded evaluation for [#91](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/91): an in-depth look at
> the [Croissant](https://mlcommons.org/working-groups/data/croissant/) metadata format, compared with what PROV-O
> and DAnO do, and the resulting direction for ADIRO. The geometry conclusion is developed further in the new
> `aec_geometry` module and [#90](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/90).

!!! info "Where the decision lives"
    Evaluation: [#91](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/91). Related design pages:
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

The recommendation, in one line: **keep `aec_provenance` (PROV-O-aligned) for in-graph, per-assertion
provenance; adopt Croissant at the dataset-publication/discovery layer; and borrow Croissant's bounding-box
`format` convention for the geometry work in [#90](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/90)
so ADIRO's boxes are recognised by mainstream ML tooling.**

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
| Geometry / bbox | **`cr:BoundingBox` + `format` (e.g. `CENTER_XYWH`)** | None | (geometry not its focus) | Proposed in [#90](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/90) |
| Tool recognition | Wide (HF, Kaggle, TFDS, Google Dataset Search) | Wide (semantic web) | Niche | ADIRO-specific |
| Role for ADIRO | **Publish/discover the annotated dataset** | **Aligned to, in the core** | Compared, not reused | **The in-graph provenance model** |

The single most important row is the first: **Croissant answers a question `aec_provenance` never asks, and vice
versa.** Trying to record per-title-block-field confidence in Croissant would be forcing corpus-level metadata
to do assertion-level work; trying to make `aec_provenance` describe a dataset's files and splits would be the
reverse mistake.

## 5. Where each fits ADIRO

- **`aec_provenance` (PROV-O-aligned) stays the in-graph provenance model.** Unchanged by this evaluation. It
  is the right tool for the per-assertion confidence/agent/activity that UC-01 (and later UC-03) need, and
  Croissant offers no equivalent.
- **Croissant fits at the dataset-publication layer**, not in the ontology. When an ADIRO-annotated corpus of
  drawings is published (for internal discovery/retrieval, or as a public evaluation dataset for the SPARQL
  competency-question work), a Croissant manifest is how it becomes findable and loadable by standard tooling.
  This is an *application of* ADIRO, not a change *to* it.
- **DAnO stays a documented comparison**, not reused (see the [DAnO comparison](dano-comparison.md)).

## 6. Implementation ideas for ADIRO

Concrete, in rough priority order. None of these change the assertion model; they add a dataset-facing surface
and borrow one useful convention.

1. **A provenance-bearing `BoundingBox` in a new `aec_geometry` module — borrowing Croissant's `format`
   convention — for [#90](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/90).** Croissant standardises
   *how a box is written* — `cr:BoundingBox` with a `format` token such as `CENTER_XYWH`, `XYWH` or `XYXY`. That
   convention is worth borrowing so an ADIRO box can be mapped to CV tooling's formats by an exporter (ADIRO
   stores a page-point xyxy *string*; Croissant expects a four-number array with a format declaration); but
   Croissant carries only the shape, and a title-block box needs two things Croissant does not model:
   - a **coordinate frame** — which PDF/page/units/origin the coordinates are relative to; and
   - its **own provenance** — a box is itself an inferred claim (a detector localised it, with a confidence) or a
     human annotation, and that is *distinct* from how confident we are of the field's *value*.

   So ADIRO promotes the box to a **class**: `aec_geometry:BoundingBox`, a subclass of GeoSPARQL's `geo:Geometry`
   (so UC-01 and UC-03 boxes reduce to the same spatial type), carrying its coordinates in an `XYXY` convention
   aligned to Croissant's token, an `inCoordinateFrame` link to a `CoordinateFrame` (the PDF-page context), and —
   by being an inferred entity — its own `hasInferenceMeta` / `hasConfidence` from `aec_provenance` (who/what/when
   produced it, model-vs-human, and with what score). This unifies with the UC-03 geometry design (`geo:Geometry`
   + `CoordinateFrame`, primary space `page_display_pt`) so the module is shared, and it fixes the confidence-on-
   geometry problem UC-03 flagged (see item 2). Detail in [#90](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/90).
2. **Emit a Croissant manifest for a published ADIRO dataset.** Model the extracted graph as a `cr:RecordSet`
   whose `cr:Field`s are semantically typed to ADIRO field-kinds/properties via `dataType` /
   `equivalentProperty` (the hook from §1). The Croissant file describes *the dataset*; the semantic types point
   *into ADIRO*. This is the clean bridge and needs no ontology change — it is a serialisation concern for the
   publication step.
3. **Use the RAI extension to document the extraction pipeline at corpus level.** How the ML pipeline collected
   and produced the ABox (data-collection, annotation protocol) is exactly what RAI is for, and it complements
   — does not duplicate — the `InferenceMeta` model. `InferenceMeta` describes the inference *activity* that
   produced a result (and may be shared by several results — a result's own confidence is carried separately, per
   result); RAI says how *the corpus* was built.
4. **Reuse the dataset-level vocabulary we already partly use.** ADIRO module headers already carry
   `dcterms:` (title, licence, creator, publisher). A published-dataset Croissant manifest can carry the same
   schema.org/Dublin-Core fields (`license`, `version`, `citeAs`, `datePublished`), keeping the metadata story
   consistent from ontology to dataset.

**What not to do:**

- **Do not replace `aec_provenance` with Croissant.** Wrong granularity — Croissant has no per-assertion
  confidence, agent or activity for an individual field value.
- **Do not put Croissant terms in the ADIRO TBox.** Croissant describes datasets, not the ontology; the two
  meet only at publication time, through semantic typing that points into ADIRO.

## 7. Recommendation

Croissant is **complementary and adopted at the dataset layer**, PROV-O stays **aligned-to in the core**, DAnO
stays a **documented comparison**. The one place Croissant changes near-term ADIRO work is geometry: its
bounding-box `format` convention should shape [#90](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/90)
so ADIRO's boxes — shared by UC-01 and UC-03 — are standards-aligned rather than bespoke.

## Open questions

- Should the ADIRO `BoundingBox` `format` values be *exactly* Croissant's tokens, or a superset (adding a
  reference-frame token Croissant lacks)?
- Where does the Croissant manifest for a published dataset live — generated by the inference/publication
  pipeline, or checked in alongside a public evaluation dataset?
- Does the RAI lifecycle documentation belong with the dataset, or cross-referenced from a design page here?

## Sources

- Croissant specification — <https://docs.mlcommons.org/croissant/docs/croissant-spec.html>
- Croissant paper (NeurIPS 2024 D&B) — <https://arxiv.org/abs/2403.19546>
- MLCommons Croissant working group — <https://mlcommons.org/working-groups/data/croissant/>
- W3C PROV-O — <https://www.w3.org/TR/prov-o/>
- ADIRO [DAnO comparison](dano-comparison.md) and [External ontology imports](external-ontology-imports.md)
