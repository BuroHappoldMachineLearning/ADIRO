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
| 1A | **Reuse the external IRI as a local stub** — declare the external term locally (`rdf:type` + `rdfs:label` + `rdfs:isDefinedBy <source>`) and point our axioms at it. No `owl:imports`, no extraction. | We want the external IRI for *interoperability signalling*, our own axioms carry all the logic we need, and the external term's own axioms are compatible with ours. | Inherits **none** of the source's entailments. The stub is a name, not a definition. |
| 1B | **Mint our own term and relate it** — declare an ADIRO term and link it to the external one, by `rdfs:subPropertyOf` / `rdfs:subClassOf` if the alignment is logically sound, otherwise by an annotation such as `skos:closeMatch`. | The external term's domain, range or property type is incompatible with what we need — so reusing its IRI would import a wrong commitment. | An annotation link carries **no** logical force. That is the point: nothing is inherited, including the parts we did not want. |
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
case. It is an **option 1B** case: mint an ADIRO property and relate it.

!!! warning "And relate it with an *annotation*, not `rdfs:subPropertyOf`"
    When the objection to an external term is its **domain or range**, `rdfs:subPropertyOf` does not escape the
    problem — it re-imposes it. A sub-property inherits its parent's domain and range, so
    `:depicts rdfs:subPropertyOf dano:depicts` would entail that every subject of `:depicts` is a
    `dano:DisplayElement`, which is precisely what minting our own term was meant to avoid. Remember that in OWL
    a domain is an *inference rule*, not a constraint: nothing is rejected, a wrong type is concluded.
    Use `rdfs:subPropertyOf` only when the parent's own axioms are ones we actively want; otherwise use
    `skos:closeMatch`. Worked through in full in the [DAnO comparison](dano-comparison.md).

## Where the reference lives: core module or compatibility layer

Choosing option 1 settles *how* to relate to an external term. A second question is *where the reference may
sit*. An external IRI in a core module couples that module's release to the external vocabulary; an external
IRI in an optional layer does not.

A core module may reference an external vocabulary directly only when **all three** hold:

1. **The source is stable, versioned and maintained.** A permanent IRI is not enough; look for releases.
2. **The alignment is logically sound.** Compatible property types, compatible ranges, and a domain we are
   willing to inherit.
3. **The entailments it carries are ones we want.** An alignment we would rather a reasoner ignored is not a
   core concern.

`aec_provenance` references PROV-O in the core and passes all three: a W3C Recommendation, a genuine
sub-property relationship, and PROV-awareness is exactly the intent.

Otherwise the reference goes in an **optional compatibility layer** — a module carrying annotation-level
mappings only, which **nothing in the core imports** and a consumer loads explicitly. `aec_dano_alignment` is
the worked example: seven `skos:closeMatch` mappings, no logical force, and no DAnO IRI anywhere in the ADIRO
core. This keeps core release cycles independent of an unreleased third-party vocabulary and lets a mapping be
deprecated wholesale without touching a core module.

It also keeps ADIRO consistent with its own advice. The rule above tells others to extract from a **pinned core
file, not a merged alignment graph** — advice that only works when vocabularies ship the two separately, as
GeoSPARQL does. ADIRO ships that way for the same reason.

A compatibility layer is **not** a substitute for options 2 and 3. If a future module genuinely needs to reason
with an external vocabulary's axioms, a pinned SLME extract remains available and is a different artefact,
imported by whatever needs it and justified under the test above.

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
| **PROV-O** | Option 1A (external IRI reused as a local stub) in `aec_provenance`, referenced from the core. |
| **GeoSPARQL** | Chosen vocabulary; adoption still deferred — see [#36](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/36). If adopted, extract `STAR` from the pinned core. |
| **DAnO** | **Decided: no import, no extraction.** ADIRO mints its own terms; the crosswalk is annotation-level in the optional `aec_dano_alignment` module. Coverage of `aec_common_symbols` is still open. See the [DAnO comparison](dano-comparison.md) and [#77](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/77). |
| **ifcOWL / BEO** | Surveyed only — see [Discussion #70](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/70). |
