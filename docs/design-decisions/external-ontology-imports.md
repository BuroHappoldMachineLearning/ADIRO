# External ontology imports

How ADIRO brings in terms from external vocabularies (GeoSPARQL, PROV-O, DAnO, …) — and, just as often, how it
deliberately *doesn't*.

!!! info "Where the decision lives"
    The reasoning, evidence and references behind this page are in
    **[Discussion #74](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/74)**
    (ported from the internal KB note RES-A-12, now frozen). Implementation is tracked in
    [RES-68](https://bhmlrnd.youtrack.cloud/issue/RES-68). This page is the short, normative version.

## The rule

Pick the **lightest option that meets the need**, in this order:

| # | Option | Use when | Cost |
|---|---|---|---|
| 1 | **Local stub + alignment** — declare the external term locally (`rdf:type` + `rdfs:label` + `rdfs:isDefinedBy <source>`) and align to it. No `owl:imports`, no extraction. | We want the external IRI for *interoperability signalling*, and our own axioms carry all the logic we need. | Inherits **none** of the source's entailments. The stub is a name, not a definition. |
| 2 | **SLME extraction** — `robot extract --method STAR` from the **version-pinned core file**. | We genuinely want to *reason with* the source's axioms. | Larger module; must be pinned, justified and reasoner-checked. |
| 3 | **MIREOT** — `robot extract --method MIREOT`, asserting an ADIRO-local superclass. | We deliberately want to **re-home** an external term under ADIRO's own taxonomy. | Preserves no entailments; the local placement is a manual commitment. |
| 4 | ~~`owl:imports` of a whole external ontology~~ | **Never.** | Drags the entire source (and its imports) under our blocking DL gate. |

Options 2 and 3 additionally require, per
[Versioning § Imports](../contribute/versioning/index.md):

- **version-pin the source**, and
- **document + justify the pin** — an `rdfs:comment` on the import axiom *plus* a note in the module's changelog.

## Why "pin the core file, not a merged graph"

SLME is deterministic for a fixed input. What changes the result is **which graph you hand the extractor**.

Many vocabularies ship a small core file plus a separate *alignments* file mapping their terms up into upper
ontologies (BFO, PROV, CCO, schema.org, …). GeoSPARQL is exactly this shape: its core
(`http://www.opengis.net/ont/geosparql`, v1.1.1) has **no `owl:imports`** and contains **none** of those
alignment axioms. Extract from the pinned core and the upper-ontology closure simply cannot appear; merge the
alignments file first and it can.

## SLME methods — which one includes what

Easy to get backwards, so stated explicitly (per the [ROBOT `extract` docs](http://robot.obolibrary.org/extract)):

| Method | Contains | Typical size |
|---|---|---|
| **`BOT`** (⊥) | seed **+ all their super-classes** — a view from the bottom of the hierarchy *upwards* | medium |
| **`TOP`** (⊤) | seed **+ all their sub-classes** — a view from the top *downwards* | large |
| **`STAR`** (⊥⊤*) | seed + the inter-relations between them — **not necessarily sub- or super-classes** | very small |

**`STAR` is ADIRO's default.** If the concern is "don't drag an upper ontology in behind a geometry term", then
`STAR` is the mitigation and `BOT` is the risk — not the other way round.

Two consequences of ⊥⊤*-locality worth knowing when predicting what `STAR` will pull:

- An upward `rdfs:subClassOf` / `rdfs:subPropertyOf` alignment is **⊤-local** and is **dropped** by `STAR`.
- An `owl:equivalentClass` / `owl:equivalentProperty` alignment is **neither** ⊥- nor ⊤-local and **is kept**.

## What MIREOT can and cannot do

MIREOT's third URI asserts a **local superclass**. It does **not** rewrite an external term's `rdfs:domain` or
`rdfs:range`.

So if an external property's domain is too narrow for us — for example `dano:depicts` is asserted with
`rdfs:domain dano:DisplayElement`, narrower than ADIRO's `metadata:DrawingElement` — that is **not** a MIREOT
case. It is a *mint our own term and relate it* case: declare an ADIRO property and link it with
`rdfs:subPropertyOf` or `skos:closeMatch` (option 1 above).

## The safeguard that applies to every option

Every ontology PR is reasoned over the **merged suite at latest**:
`.github/workflows/ontology-reasoning.yml` runs **HermiT** (blocking — fails on inconsistency, unsatisfiable
classes, or non-DL) plus ROBOT `report` (advisory), via `scripts/run_reasoning.sh`, resolving imports offline
through `src/catalog-v001.xml`. Run the identical check locally with:

```bash
bash scripts/run_reasoning.sh          # warn mode
ENFORCE=1 bash scripts/run_reasoning.sh # fail on inconsistency / unsatisfiable classes
```

This is the concrete defence against the failure mode documented for the Experimental Factor Ontology, where
selectively-referenced imports left the merged result inconsistent with large numbers of unsatisfiable classes.

## Worked example — PROV-O in `aec_provenance`

`aec_provenance` needs PROV-O only as an *alignment target*: its own axioms carry the logic. So it takes
**option 1** — minimal local typing stubs plus `rdfs:isDefinedBy`, with no `owl:imports`:

```turtle
prov:Agent rdf:type owl:Class ;
    rdfs:label "Agent" ;
    rdfs:isDefinedBy <http://www.w3.org/ns/prov#> .
```

The module stays self-contained, the reasoning CI resolves everything offline, and consumers still get the
PROV-O IRI.

## Status of current candidates

| Vocabulary | Status |
|---|---|
| **PROV-O** | Option 1 (local stub + alignment) in `aec_provenance`. |
| **GeoSPARQL** | Chosen vocabulary; adoption still deferred — see [#36](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/36). If adopted, extract `STAR` from the pinned core. |
| **DAnO** | Import-vs-align undecided — see [#77](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/77). Prior review recommends aligning, not importing. |
| **ifcOWL / BEO** | Surveyed only — see [Discussion #70](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/70). |
