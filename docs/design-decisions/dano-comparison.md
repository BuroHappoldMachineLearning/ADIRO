# DAnO: where ADIRO overlaps it, and what ADIRO reuses

A comparison of the ADIRO suite with the **Drawing Analysis Ontology** (DAnO), and the decision it settles:
ADIRO **does not import or extract from DAnO**, and links to it through an optional compatibility layer at
annotation level only.

!!! info "Where the decision lives"
    Decision: [#77](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/77), implemented in
    [#76](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/76). The rule it applies is
    [External ontology imports](external-ontology-imports.md). The term survey that preceded it is
    [Discussion #70](https://github.com/BuroHappoldMachineLearning/ADIRO/discussions/70).

## Summary

DAnO is a well-shaped vocabulary that overlaps ADIRO on **one module out of five**. Outside that module the two
do different jobs; inside it they are genuine alternatives, and there DAnO is currently the richer of the two.

ADIRO treats DAnO as **evidence rather than as a dependency**. It corroborated two ADIRO design decisions,
exposed one real gap, and none of that required importing a single axiom. Where the two overlap, the crosswalk
is annotation-level and lives in an optional module that nothing in the ADIRO core imports.

This page is deliberately explicit about where DAnO is ahead, because the module where that is true
(`aec_common_symbols`) is the one due for work next, under UC-03 and UC-07.

## 1. What DAnO is

**Drawing Analysis Ontology** - [`https://w3id.org/dano`](https://w3id.org/dano), prefix `dano:`, CC BY 4.0,
from RUB Informatik im Bauwesen. Its own scope statement: *"concepts of technical drawings from the perspective
of computer vision-based drawing analysis"*. 16 classes, 13 object properties, 7 datatype properties, **no
`owl:imports`**, and no `owl:disjointWith` or `owl:equivalentClass` axioms.

```
DrawingElement -+- DisplayElement      "an element representing a real-world component"
                +- DescriptionElement  "an abstract element describing properties of display
                                        elements" (dimension lines, text)

DrawingElement --hasConfidence--> xsd:decimal
DrawingElement --hasMeta--> DrawingElementMeta -+- inferredAt   (xsd:date)
                                                +- inferredBy   (xsd:string)
                                                +- inferredFrom (xsd:string)
                                                +- inferredWith (xsd:string)
```

## 2. The overlap map

ADIRO is a **suite**, and the relationship with DAnO differs in each module. Stating this per module rather
than in the aggregate is the only way to get it right.

| ADIRO module | DAnO counterpart | Relationship |
|---|---|---|
| `aec_provenance` | `DrawingElementMeta`, `inferredAt/By/From/With`, `hasConfidence` | **Overlapping.** ADIRO supersedes - see §3 |
| `aec_drawing_metadata` - sheets, layouts, revisions, projects, parties, title block | `TextField`, `TextElement` only | **Largely complementary.** DAnO models no document structure, no parties, no revisions |
| `aec_common_symbols` - `Dimension`, `Grid`, `ReferenceSymbol` | `Dimension`, `DimensionChain`, `DimensionLine`, `AxisLine`, `Terminator`, `SectionSymbol`, `Symbol`, `EquipmentSymbol` | **Directly competing, same layer.** DAnO is currently richer - see §4 |
| `aec_domain_common`, `aec_facade_domain` | none | **No overlap.** DAnO has no discipline or domain modelling |

An earlier framing described the two as occupying different layers - DAnO for what was seen, ADIRO for what it
means. That holds for the title-block vocabulary it was written about, and it does **not** generalise to the
suite: `aec_common_symbols` sits squarely in DAnO's layer and models the same objects.

The contents of the compatibility layer are the best measurement of the overlap. It carries **seven** mappings,
all of them provenance plus `depicts`. Nothing maps to sheets, layouts, revisions or parties, because DAnO has
no counterpart. Nothing maps to symbols, because that question is open rather than settled.

## 3. Where ADIRO goes further: provenance

This is the substantive modelling difference, and it is requirement-driven rather than a preference for a
heavier model.

DAnO attaches provenance to the **element**: one `DrawingElement`, one `DrawingElementMeta`, one confidence.
ADIRO reifies the **assertion**: a `FieldAssertion` is a claim that some source states some value for some
field kind, carrying its own `assertedBy`, `hasInferenceMeta` and `hasConfidence`.

That choice is what makes three ORSD competency questions answerable:

| Competency question | Why assertion-level is needed |
|---|---|
| **CQ 4.4** - *which extraction-service results have been aggregated, and from which service did each originate?* | Two services can assert different values for the same field. As separate `FieldAssertion`s each keeps its own provenance and confidence; as one element with one meta object, the second write overwrites the first |
| **CQ 2.4** - *which detected errors are auto-resolvable and which require human intervention?* | Needs a validation status and an explicit conflict relation, both per-claim. DAnO has no human-in-the-loop concept |
| **CQ 3.2** - *which predicted individuals match their ground-truth counterparts, and which diverge?* | Divergence is a relation between two claims about the same thing, which presupposes that claims are individuals |

In fairness, **CQ 3.1** (*what label, confidence score and geometry are recorded for a given model-prediction
individual?*) is satisfied by DAnO's model as it stands. The gap is specific, not general.

DAnO's placement of `hasConfidence` on the element while the four `inferred*` properties sit on the meta object
is worth reading as deliberate: inference metadata is usually shared across every element from one extraction
run, whereas confidence is per-result. ADIRO reaches the same conclusion by a different route.

Secondary differences on the same terms, all pointing the same way: DAnO carries actor, tool and source as
`xsd:string`, so two spellings of one model are unrelated strings, while ADIRO points at entities that can be
described, versioned and queried. DAnO's `inferredAt` is `xsd:date`, so two extraction runs on one day are
indistinguishable; ADIRO's is `xsd:dateTime`. ADIRO's provenance is aligned to PROV-O throughout, so
PROV-aware tooling understands it without bespoke mapping.

## 4. Where DAnO goes further: drawing-mark decomposition

`aec_common_symbols` currently declares three classes - `Dimension`, `Grid`, `ReferenceSymbol`. DAnO declares
eight or so in the same territory, and decomposes a dimension into its parts: `dano:Dimension` is a composite
of exactly one `DimensionLine`, two `Terminator`s and one `TextElement`, with `DimensionChain` above it and
`AxisLine` alongside.

On that ground DAnO is the more developed vocabulary, and any claim that ADIRO is simply *more expressive*
would be false there. ADIRO's symbol coverage is thin because the use cases that need it have not been built
yet, not because a decomposition was considered and rejected.

This matters now rather than later: **UC-03** (Reference Symbol Cross-Sheet Linking) is the highest-priority
open use case and touches `SectionSymbol` / `Terminator` / `refersTo` / `isReferredToBy`, and **UC-07** (Wall
Orientation and Measurement) needs exactly the dimension and axis-line territory. See §8.

## 5. What actually distinguishes ADIRO

Not expressivity in the abstract. ADIRO is built for the **machine-learning loop**, and that shows up as
vocabulary DAnO has no counterpart for:

- `labellableRoot`, `isCVATProperty`, `exampleImage`, `extractionHint` - annotations that tell an annotation
  tool and an extraction pipeline what to label and how, carried by the ontology itself.
- `expectedRange`, `mapsToFieldProperty` - the bridge from a reified assertion to a validated, promoted
  statement.
- A field-kind scheme whose *membership is the extraction profile*, with per-language synonyms.
- Document structure, parties, revisions, projects and discipline taxonomies, so an extracted value can be
  placed in a real engineering context.

And one characteristic that is not vocabulary at all but shapes every modelling choice: **ADIRO individuals
are detections, not idealised drawing constructs.** ADIRO targets historical drawings as well as modern ones,
and a scanned historical sheet is routinely cut at the edge, torn, faded or partially legible. What ADIRO
records is what a detector actually found, with confidence and with gaps. DAnO describes drawings as they are
meant to be. That difference has teeth - see §8.

DAnO describes what is on a drawing. ADIRO describes what a drawing *means*, and how a model is trained,
evaluated and held accountable for extracting it. That is a difference in purpose, not a score.

## 6. Maintenance and release discipline

ADIRO commits to per-module SemVer, version-pinned IRIs, changelogs, and a blocking DL reasoning gate on every
pull request. DAnO's repository was created 2025-03-11 and last pushed 2025-07-15, with **no tags or
releases** - though it does have a permanent `w3id.org` IRI, which is more than many peers offer.

The earlier [title-block vocabulary review](titleblock-vocabulary-review.md) called it **"borrowable, not
dependable"**. That remains the right summary, and it is an argument about what to take a hard dependency on,
not about the quality of the modelling.

## 7. The decision, and why the links are annotations

ADIRO mints its own terms and relates them to DAnO with `skos:closeMatch`, in a separate optional module
`aec_dano_alignment`. No `owl:imports`, no extraction, and **no ADIRO core module mentions DAnO at all**.

The cheap-looking alternative is `rdfs:subPropertyOf`, so that DAnO-aware consumers understand us. That move is
unavailable for three separate reasons, worth separating because only the first fails our own CI.

**Type mismatch (fails locally).** `aprov:inferredBy`, `inferredWith` and `inferredFrom` are **object**
properties; DAnO's are **datatype** properties holding strings. OWL 2 DL has no sub-property axiom crossing
that boundary, so the axiom is ill-typed and non-DL, and the blocking reasoning gate rejects it. Declaring the
stub dishonestly as an object property would move the failure downstream onto anyone merging real DAnO.

**Range conflict (fails on merge).** `aprov:inferredAt` has range `xsd:dateTime`; `dano:inferredAt` has range
`xsd:date`. The two datatypes are disjoint, so an inherited range makes **every recorded timestamp**
inconsistent.

**Domain leakage (silent).** `dano:hasConfidence` carries `rdfs:domain dano:DrawingElement`. In OWL a domain is
an *inference rule*, not a constraint: from `x dano:hasConfidence 0.87` a reasoner concludes `x` **is** a
`dano:DrawingElement`. Under a sub-property axiom, every `FieldAssertion` ADIRO produces would be entailed to
be a drawing mark - filing a claim *about* a mark under the class of marks. Nothing errors. The same applies to
`dano:depicts` (`rdfs:domain dano:DisplayElement`) and, through `owl:inverseOf`, to `dano:isDepictedBy`.

### Why this is easy to miss

A local stub carries none of the source's axioms, so the second and third failures pass the ADIRO gate
**silently**. They fire the first time someone loads ADIRO alongside DAnO itself - which is exactly the
audience an external IRI exists to serve. An alignment that works only for consumers who ignore it is not an
alignment.

`skos:closeMatch` is annotation-level: a reasoner concludes nothing from it, no domain, range or type is
inherited, and a human or a crosswalk tool still learns that two terms mean nearly the same thing. The DAnO
IRIs are **not declared anywhere in ADIRO** - they appear only as annotation values.

!!! note "Option 1 is really two moves"
    The published rule folds both under "local stub + alignment", but they differ in which IRI is the subject.
    **Move A - reuse the external IRI as a stub** (`prov:Agent` in `aec_provenance`): the external term stays
    the subject and ADIRO's axioms point at it. **Move B - mint an ADIRO term and relate it** (everything on
    this page): the ADIRO IRI is the subject and the external term appears only as an annotation value. Move B
    is the right one whenever the external term's own axioms are incompatible with ADIRO's.

## 8. Open: `aec_common_symbols`, and what this strategy does and does not constrain

`aec_common_symbols` is the one module where ADIRO and DAnO compete, and it is next in line for work. Nothing
on this page decides it; the decision is tracked in [#79](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/79). What follows is the procedure it
inherits.

**When may a core module reference an external vocabulary directly?** The test is not "external or not" -
`aec_provenance` references PROV-O in the core and should. The test is:

| Condition | PROV-O | DAnO |
|---|---|---|
| Source is stable, versioned and maintained | W3C Recommendation since 2013 | No releases, quiet since 2025-07 |
| Alignment is logically sound | `inferredBy` genuinely *is* a `prov:wasAttributedTo` | Type, range and domain clashes throughout |
| The entailments it carries are wanted | Yes - PROV-awareness is the point | No - the mappings are for humans and crosswalk tools |
| **Verdict** | **Core** | **Optional compatibility layer** |

So the rule the suite now follows: *an external term may be referenced from a core module only when the source
is stable and the alignment is both sound and wanted. Otherwise the reference lives in an optional layer where
it carries no logical force and consumers opt in.*

**What that permits for `aec_common_symbols`:**

- **Minting ADIRO terms that parallel DAnO's decomposition** - `DimensionLine`, `Terminator`, `AxisLine` and
  so on - and mapping them in the compatibility layer. Fully compatible with this strategy, and the likely
  answer, because ADIRO symbol classes are also **labelling targets**: they carry `labellableRoot` and
  `isCVATProperty` annotations for the extraction pipeline. Annotating an external IRI with ADIRO's own
  annotation properties would couple the core to DAnO through the back door.
- **A pinned SLME `STAR` extract**, if a future use case genuinely needs to *reason with* DAnO's axioms. The
  published rule's options 2 and 3 remain open. Such an extract is a **different artefact** from the
  compatibility layer - it holds real external axioms, must be version-pinned and justified, and whatever
  needs it imports it explicitly. Adding one would not contradict this page; it would need its own decision
  under the same test above.

**A further argument for minting, specific to ADIRO's data.** `dano:Dimension` is not just a label, it is a
composite definition with **exact qualified cardinalities**:

```turtle
dano:Dimension ⊑ dano:Composite
  ⊓ =1 contains.DimensionLine
  ⊓ =2 contains.Terminator
  ⊓ =1 contains.TextElement
```

On a clipped, torn or partially legible historical sheet - ADIRO's routine input - a detected dimension may be
missing a terminator, its text, or the line itself. Under OWL's open-world assumption those axioms do **not**
reject such a dimension. They **infer the missing parts into existence**. Ask a reasoner afterwards which
dimensions are incomplete and it answers "none", having already supplied what the detector never saw.

That directly undermines a competency question ADIRO already holds: **CQ 2.1** asks whether an extracted graph
*lacks any mandatory functional sub-components required to form a semantically complete assembly*. Adopting an
exact-cardinality axiom makes missing sub-components unfindable by reasoning. Completeness is a **validation**
question - a SHACL shape over a finished extraction, under closed-world semantics - not an entailment over
detections. Tracked in [#84](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/84), with a worked note in UC-07 §7.5.

The axioms would not fail the reasoning gate. They would quietly give wrong answers, which is worse, and it is
the same failure mode as the domain leakage in §7: an adopted axiom that entails something ADIRO does not mean.

**What it rules out:** declaring DAnO IRIs inside a core module and building axioms on them (move A for DAnO),
because DAnO fails the first two conditions of the test.

**What is not yet known:** whether UC-03 or UC-07 need DAnO's decomposition at all. UC-03 already ships
`csymbol:ReferenceSymbol` and its own linking properties; UC-07 has no ontology work yet. The question to
answer when they are picked up is whether DAnO's published decomposition is better than what ADIRO would
design unaided - and if it is, to adopt the *shape* and mint the terms, which is what ADIRO has already done
twice with DAnO (see §9).

One hygiene point the compatibility layer introduces: a mapping whose ADIRO-side subject is later renamed
becomes a dangling annotation that no reasoner will flag, because annotations carry no logical force. A cheap
staleness check is tracked in [#81](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/81).

## 9. What DAnO contributed anyway

None of this required importing anything, and all of it changed ADIRO:

- **It corroborated the reification choice.** ADIRO was holding open RDF-star versus a meta-object for
  per-value provenance. DAnO had already chosen the meta-object. A peer group meeting the same problem the
  same way is real evidence, and `aprov:InferenceMeta` follows it.
- **It exposed a genuine gap.** ADIRO proposed no extraction timestamp anywhere. `dano:inferredAt` made the
  omission obvious; `aprov:inferredAt` exists because of it.
- **It corroborated two over-modelling suspicions.** DAnO carries source and model as plain strings, which
  supported the independent finding that `SourceFile` and `MLModel` as classes were heavier than the
  requirements justified.

This is the pattern worth keeping: **adopt the shape, mint the terms, map the names.**

## 10. Per-term verdicts

| DAnO term | Verdict | Reason |
|---|---|---|
| `dano:inferredBy` | Superseded by `aprov:inferredBy`; `skos:closeMatch` | Object/datatype type mismatch; ADIRO's resolves an agent |
| `dano:inferredWith` | Superseded by `aprov:inferredWith`; `skos:closeMatch` | As above |
| `dano:inferredFrom` | Superseded by `aprov:inferredFrom`; `skos:closeMatch` | As above; ADIRO's is PROV-aligned |
| `dano:inferredAt` | Superseded by `aprov:inferredAt`; `skos:closeMatch` | `xsd:date` disjoint from ADIRO's `xsd:dateTime` |
| `dano:hasConfidence` | Superseded by `aprov:hasConfidence`; `skos:closeMatch` | Domain leakage; ADIRO's is per-assertion |
| `dano:DrawingElementMeta` | Superseded by `aprov:InferenceMeta`; `skos:closeMatch` | Same pattern, PROV-aligned |
| `dano:depicts` | ADIRO mints `metadata:depicts`; `skos:closeMatch` | Domain `dano:DisplayElement` is wrong for a class that also covers dimensions and grids |
| `dano:isDepictedBy` | Not minted yet | Inverse naming is UC-06's call (`isDepictedOn`) - [#80](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/80) |
| `dano:Dimension`, `DimensionChain`, `DimensionLine`, `AxisLine`, `Terminator`, `SectionSymbol` | **Open**, but reuse of the IRIs is disfavoured | `aec_common_symbols` / UC-03 / UC-07 - see §8, [#79](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/79). `dano:Dimension`'s exact cardinalities would infer undetected parts into existence on clipped drawings - [#84](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/84) |
| `dano:DisplayElement` vs `DescriptionElement` | **Open** | The split may be worth minting as ADIRO's own; ADIRO's `DrawingElement` currently spans both - [#83](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/83) |
| `dano:hasGeometry`, `defaultGeometry` | Deferred | Gated on the GeoSPARQL decision, [#36](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/36) |
| `dano:hasIfcRepresentation` | Not assessed | Possible cheap alternative to IFC alignment axioms |

`metadata:depicts` answers **ORSD CQ 5.2** and closes its open issue OI-1. It asserts no domain or range: UC-03
would place the subject on a reference symbol and UC-06 on a whole drawing, so committing to a narrower domain
would entail those subjects are of a type they are not - the same error this page rejects in DAnO's axioms.
The principle is general, not a criticism of DAnO.

## 11. Precedent: neither ontology imports the other's source

DAnO has no `owl:imports`. It declares the GeoSPARQL terms it needs **locally**, with `rdf:type`, `rdfs:label`,
`rdfs:comment`, `rdfs:isDefinedBy` and a version-pinned `owl:versionIRI` annotation:

```turtle
geo:hasGeometry
  rdf:type owl:ObjectProperty ;
  rdfs:comment "A spatial representation for a given feature." ;
  rdfs:isDefinedBy <http://www.opengis.net/ont/geosparql> ;
  rdfs:label "hasGeometry"@en ;
.
```

That is ADIRO's option 1, move A, arrived at independently by another group - external corroboration of the
import rule, and a reason to read ADIRO's treatment of DAnO as the same courtesy rather than a criticism.

ADIRO goes one step further by putting its crosswalk in a *separate* file, the shape GeoSPARQL itself uses
(core plus `alignments.ttl`). The reason is lifecycle rather than logic: an unreleased third-party vocabulary
should not be able to force a version bump on a core module that downstream consumers pin, and crosswalks to
DiCon, ifcOWL, BOT and GeoSPARQL would otherwise pile up inside two core files. It is worth being precise that
annotation-only mappings would **not** have endangered an SLME extraction if left inline — locality is defined
over logical axioms and `skos:closeMatch` is not one — so this is not the merged-alignment-graph hazard the
import rule warns about. The separation does make it safe to add a *logical* alignment later without
contaminating the core for extractors.

It also retires an argument made earlier in ADIRO's own review, that importing DAnO would *"drag its 16
drawing-element classes"* into the suite. True as far as it goes, but DAnO imports nothing, so bloat was never
the operative risk. The operative risk is type and domain incompatibility, which is sharper and applies even to
the lightest alignment.

## 12. Method and limits

**Verified against primary sources (2026-09-21):** the raw `dano.ttl` fetched from `https://w3id.org/dano`
(HTTP 200, resolving to `rub-informatik-im-bauwesen.github.io/dano/dano.ttl`). Every domain, range and property
type quoted here is read from that file, not from DAnO's generated specification. The absence of
`owl:imports`, `owl:disjointWith` and `owl:equivalentClass` was confirmed by direct search. ADIRO class and
annotation-property counts are read from `src/*.ttl` on the branch implementing this decision.

**Supersedes:** the earlier [title-block vocabulary review](titleblock-vocabulary-review.md) recommended
aligning ADIRO's provenance terms to `dano:` rather than minting parallel ones. That review read DAnO from its
generated specification and explicitly flagged that domains and ranges should be confirmed against the source
before any alignment axiom was written. They now have been, and the recommendation does not survive the check.

**Corrects:** an earlier framing of the two ontologies as occupying different layers. That holds for the
title-block vocabulary it was written about; it does not hold for `aec_common_symbols`.

**Not claimed:** that DAnO's modelling is wrong for DAnO's purpose. Every objection here concerns what ADIRO
can safely depend on, given a blocking DL gate and a different set of competency questions.

**Not disjoint:** DAnO declares no `owl:disjointWith` axioms, so the domain-leakage objections describe wrong
entailments rather than inconsistencies that would fail a reasoner today. That would change if DAnO declared
`DisplayElement` and `DescriptionElement` disjoint, an obvious future addition.
