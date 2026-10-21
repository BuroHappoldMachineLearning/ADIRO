# UC-03 provenance application profile

This profile implements [#96](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/96)
using the existing `adiro_provenance`, PROV-O and `adiro_geometry` foundation. It adds no competing core module.

An immutable PDF artifact is a `prov:Entity`; its content hash is distinct from a `DrawingSheet` identity.
Each actual extraction or resolution execution is a `prov:Activity`. It `prov:used` exact input entities,
and its output entity `prov:wasGeneratedBy` that activity. Each export execution has a new activity identity even when its inputs are identical, with actual start/end
times and pinned exporter-code and configuration hashes. A later assembly uses those output entities;
it does not imply that the earlier inference ran again. Record the generating agent with
`prov:wasAssociatedWith`. Where the historical producer, parameters or timing were not recorded, retain
`not_recorded` in the manifest rather than reconstructing an invented execution.

## Accepted graph and detailed evidence

The accepted graph contains source occurrences, accepted composition and target identities, selected
geometry and declared coordinate frames. Shared batch manifests pin model, configuration, code and input
hashes. Indexed immutable JSONL records keep per-occurrence candidates, member-to-target pairings,
rejections, ambiguity, abstention, corrections and inheritance. An object identifier plus delivery
membership must resolve to its evidence record. An accepted target edge does not prove link emission.

The following public-safe example is illustrative; its hashes are placeholders, not measured artifacts:

```turtle
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix dct: <http://purl.org/dc/terms/> .
@prefix ex: <https://example.org/adiro/profile-demo#> .
ex:pdf-version a prov:Entity ; dct:identifier "sha256:illustrative-input" .
ex:extraction a prov:Activity ; prov:used ex:pdf-version ;
    prov:wasAssociatedWith ex:extractor .
ex:extraction-output a prov:Entity ; prov:wasGeneratedBy ex:extraction .
ex:assembly a prov:Activity ; prov:used ex:extraction-output .
ex:delivery a prov:Entity ; prov:wasGeneratedBy ex:assembly ;
    prov:wasDerivedFrom ex:extraction-output ; dct:hasPart ex:occurrence .
ex:occurrence prov:wasDerivedFrom ex:pdf-version ;
    dct:identifier "evidence.jsonl occurrence_id=example-occurrence" .
```

An assembly uses an output **Entity**, not the earlier Activity as a `prov:used` object. `InferenceMeta`
may be shared across materialised `InferredEntity` products where that reflects their actual producer.
`FieldAssertion` is useful for reified field-value claims; it is not mandatory for every reference edge.

## Identity, revisions and geometry

Scope Sheet/Layout identities to their source document; matching printed numbers in two PDFs must not
merge their identities. Preserve the full upstream occurrence/member/target identifiers in evidence.
A revised annotation artifact gets its own hash and an explicit crosswalk supported by preserved record
identity and PDF hash. Never replace the resolver's pinned Gazetteer implicitly with a later annotation
snapshot. Record changed titles/boxes as revision differences. Unchanged instances retain their earlier
lineage; a local rerun gets a new scoped activity and records which delivery adopts it.

Bounding boxes carry one exact artifact/page frame, `page_display_pt`, `pt`, top-left origin, x right and
y down. Record effective page size, rotation and PDF/native/display transformations in the manifest;
already upright points are not rotated twice. A title region and a drawing-view region are different
geometry roles. A title literal is never an OWL individual with its own BoundingBox. Source Layout
membership requires unambiguous evidence; overlap and nested candidate views remain unresolved.

An unlocalisable reconstructed text block may retain independently accepted Sheet resolution and explicit
source-evidence status. It receives no invented precise text box, source Layout owner or clickable link.
Unresolved targets remain in the evidence ledger. This is an application-profile distinction between
semantic acceptance and navigation eligibility, not a new geometry cardinality axiom.

## Delivery membership and validation

A versioned delivery manifest lists semantic/provenance RDF hashes and uses `dct:hasPart` or an indexed
membership table to locate each occurrence. Historical queries select an immutable delivery explicitly;
this profile does not require a particular named-graph store. Validate duplicate identities, document
scope, source status, member reconstruction, object/datatype property use, accepted-only target edges,
and evidence lookup. Verify actual PDF emission and clicks separately when navigation is delivered.

## Composition and validation rules for UC-03 references

These rules are checked on the data, not asserted as OWL axioms:

- An `InlineLayoutSheetReference` has exactly one `DrawingIdentifierMention` and at least one
  `LayoutIdentifierMention`, attached with `contains`.
- A `ReferenceSymbol` has at most one `DrawingIdentifierMention`.
- A mention has at most one accepted `denotesDrawingSheet` target.

**Why not OWL.** OWL reasons under the open-world assumption and does not assume that different names are
different things. An existential restriction (`contains some DrawingIdentifierMention`) would not report a
missing mention; it would infer an anonymous one with no source text, box or evidence. A `max 1` or functional
axiom would not report a second mention or a second sheet; it would infer that the two are the same individual
and merge them, silently, including two different drawing sheets that share a printed number. A completeness or
cardinality rule on detections is a closed-world check, so it belongs in validation (NFR 2 of the ORSD, #84).

**Status of the checks.** These rules are specified here and are **not yet implemented** as SHACL shapes.
Where shapes live is still open (a file under `src/` would be treated as an ontology module), and is tracked with
the wider validation programme in [#22](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/22) and
[#84](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/84); the shapes for these three rules are
[#168](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/168).

**Pairing of numbers and targets.** The graph holds the accepted target set of an inline reference; which printed
layout number produced which target is kept in the indexed evidence record. A consumer holding only the graph
cannot recover that pairing. The evidence record is intended to be delivered with the delivery manifest
(delivery policy to be confirmed). Making the pairing queryable in the graph would need a binding term and is
out of scope here.

Review/retraction state machines and graph-level modelling of rare human review events remain deferred.
Detailed processing crops, candidate scores and intermediate transforms stay in evidence/manifests.
