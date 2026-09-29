# UC-03: Semantic, Geometry and Provenance

UC-03 represents cross-sheet references through three complementary responsibilities. These are **views of
one ADIRO suite**, not three databases or three new UC-03 ontology modules.

| Responsibility | Question it answers | ADIRO location and current state |
|---|---|---|
| Semantic | Which evidenced source reference exists, how is it composed, and which Sheet or Layout target has been accepted? | Existing `aec_drawing_metadata` and `aec_common_symbols`, extended under [#95](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/95); see [semantic references](uc03-semantic-references.md) |
| Geometry | Where are the source text, whole symbol, and actual output link region, and which artifact/page/coordinate frame interprets their numbers? | Shared `aec_geometry` foundation in [PR #76](https://github.com/BuroHappoldMachineLearning/ADIRO/pull/76); UC-03 roles and transforms tracked in [#93](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/93) |
| Provenance | Which exact input, run, policy, evidence and revision produced or accepted the result? | Shared `aec_provenance` foundation in PR #76; UC-03 batch/evidence profile tracked in [#96](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/96) |

An accepted target relationship belongs to Semantic. A bounding box alone does not resolve a target; a
resolved target alone does not prove that a clickable link was written to an output PDF. A detector's box
confidence differs from confidence in a text value or target interpretation.

The intended data path is:

```text
exact source PDF + page + original text/geometry evidence
  -> candidate extraction and decision history in immutable evidence records
  -> accepted reference occurrences, composition and targets in the semantic graph
  -> selected geometry in a declared coordinate frame
  -> output artifact and actual link-emission evidence, if a link is delivered
```

The graph need not contain one RDF individual for every rejected candidate or every processing crop. Run
manifests and indexed evidence files retain detailed per-occurrence choices, abstentions, corrections and
inheritance. `InferenceMeta`/PROV-O can connect materialised accepted products to their actual generating
activities. This is the proposed UC-03 operating profile under [#96](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/96), not a claim that an exporter or end-to-end navigation pipeline has already populated the graph.

The Semantic extension can be reviewed independently of the remaining UC-03 Geometry and Provenance work.
The shared `BoundingBox`, `CoordinateFrame`, `InferredEntity` and `InferenceMeta` from PR #76 are reused rather
than copied into a parallel UC-03 namespace.
