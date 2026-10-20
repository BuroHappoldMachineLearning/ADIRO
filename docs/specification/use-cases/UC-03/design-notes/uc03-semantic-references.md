# UC-03 semantic references: expressions, occurrences and accepted targets

This page explains the UC-03 semantic extension tracked in
[#95](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/95). It complements the
[UC-03 specification](../UC-03-Reference%20Symbol%20Cross-Sheet%20Linking.md).
The existing `aec_common_symbols:ReferenceSymbol` and its Layout-to-Layout link remain in place. The new terms
describe source text occurrences and complete inline or standalone references that the original symbol-only
model could not distinguish.

## One source occurrence is not its target

| Source individual | Meaning | Accepted target edge |
|---|---|---|
| `metadata:DrawingIdentifierMention` | One occurrence of sheet-number text | `metadata:denotesDrawingSheet` to a `DrawingSheet`, when resolved |
| `metadata:LayoutIdentifierMention` | One occurrence of layout-number text | No direct target edge; it is a component of a complete expression |
| `csymbol:ReferenceSymbol` | One graphical marker | Existing `csymbol:referencesLayout` to an accepted target `Layout` |
| `metadata:InlineLayoutSheetReference` | One complete inline expression | `metadata:inlineReferencesLayout` to each accepted target `Layout` |
| `metadata:StandaloneSheetReference` | One sheet-number occurrence that is itself a complete reference | Inherited `metadata:denotesDrawingSheet` |

`metadata:ReferenceExpression` groups the three complete forms for queries. A standalone reference has both
`DrawingIdentifierMention` and `ReferenceExpression` types through subclassing: **one occurrence, one individual**. It
does not need an outer wrapper, a self-directed `contains` edge or a duplicate box. An embedded sheet
number remains a component of its symbol or inline expression; absence of a known parent does not prove that
it is standalone.

This is the Semantic part of the [three-layer UC-03 model](uc03-three-layer-model.md); page regions and
processing history have separate responsibilities.

`metadata:contains`, with a typed mention as its object, expresses accepted composition, not target
resolution. The existing `metadata:hasLayout` states which Layout belongs to a DrawingSheet; a layout number
alone is not a globally unique Layout identity. The evidenced source Layout of any reference expression, inline or
standalone, is stated with `metadata:contains` from that Layout (a graphical marker through `csymbol:hasReferenceSymbol`,
a sub-property of `contains`), and read from the expression's side with the inverse path `^metadata:contains`, as ADIRO
declares no named inverse properties ([#21](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/21)). Likewise, `metadata:inlineReferencesLayout` is separate from the existing symbol-only
`csymbol:referencesLayout`, so using an inline reference cannot accidentally infer that it is a graphical
symbol. Source membership is left unset when the evidence supports only a page location. *(Amended in
[UC-03 v0.7](../UC-03-Reference%20Symbol%20Cross-Sheet%20Linking.md#10-version-history): `appearsOnLayout` was removed.)*

## Worked examples

| Source | Individuals and relationships | What remains outside the accepted graph |
|---|---|---|
| Two separate printed `S601` references | Two distinct `StandaloneSheetReference` individuals may each `denotesDrawingSheet` the same sheet | Their raw glyphs, text spans and selection histories remain separate evidence records |
| Marker `2/ST-201` | One `ReferenceSymbol`, with a `DrawingIdentifierMention` and `LayoutIdentifierMention`; the symbol `referencesLayout` only after the target Layout is resolved | Reading `2/ST-201` does not by itself prove target identity |
| Inline `1, 3, 5 & 7/S601` | One `InlineLayoutSheetReference`, one shared `DrawingIdentifierMention` for `S601`, and up to four independently evidenced `LayoutIdentifierMention` individuals; each supported target uses `inlineReferencesLayout` | Component-to-target pairing, unresolved members and rejected candidates remain in structured evidence |

For example, after one inline member has been accepted:

```turtle
@prefix md: <https://w3id.org/adiro/aec_drawing_metadata#> .
@prefix ex: <https://example.org/adiro/demo#> .

ex:sheet-S601 a md:DrawingSheet ;
    md:hasLayout ex:layout-1-S601 .

ex:sheet-text-S601 a md:DrawingIdentifierMention ;
    md:denotesDrawingSheet ex:sheet-S601 .

ex:inline-reference-1 a md:InlineLayoutSheetReference ;
    md:contains ex:sheet-text-S601 ;
    md:inlineReferencesLayout ex:layout-1-S601 .

ex:standalone-reference-2 a md:StandaloneSheetReference ;
    md:denotesDrawingSheet ex:sheet-S601 .
```

No `contains` self-link or extra DrawingIdentifierMention individual is added for the standalone reference.
The inline's other printed members receive target edges only if their resolutions are accepted.

The expression `3/A6.02 AND 5/A7.01` is commonly recognised as two independent inline references in the
current UC-03 pipeline. Adjacency or the word “AND” alone does not make it one multi-sheet expression. That
pipeline example is not a global OWL cardinality rule.

Only an accepted resolution creates a target edge. An evidenced occurrence may exist while its target is
unknown. Admission requires source-text evidence and an immutable PDF/page/token identity. Precise text
localisation is a separate navigation requirement: an unlocalisable reconstructed text block may retain
an independently accepted sheet resolution with explicit geometry status and evidence, without a fabricated
BoundingBox or a clickable link. Such an occurrence is not automatically a StandaloneSheetReference.
Rejected or ambiguous target candidates stay in evidence. These are application-profile validation rules,
not OWL geometry cardinality axioms. Geometry roles remain tracked in
[#93](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/93).

## Existing terms and deliberate limits

- `metadata:TextualNote.refersToDrawingId` stores an identifier string on a free-form note. A
  `StandaloneSheetReference` identifies a particular evidenced text occurrence and may have an accepted
  `DrawingSheet` identity. The two can coexist for different query needs; this work does not replace the
  existing note property or infer a target sheet from its string.
- The proposed general `referencesSheet` property is **not added** here. Graphical markers targeting a whole
  sheet are the narrower open case in [#38](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/38).
  `denotesDrawingSheet` already expresses the accepted identity of an evidenced sheet-number occurrence.
- A bare layout identifier that is a complete reference by itself (for example a same-sheet "see detail 3") has no
  reference class yet. A layout counterpart of `StandaloneSheetReference` is deferred with #38 and #20.
- No `ReferenceTargetBinding` class is introduced. Direct accepted target edges answer target-set queries;
  source-member-to-target pairings require stable member records in evidence, rather than an RDF node per
  pairing. A partial resolution asserts only its supported edges.
- `ReferenceSymbol` still has no raw-text datatype property. Whether raw extracted text belongs in that class
  remains under [#20](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/20). Source text and its
  extraction history can be retained in immutable evidence without altering the symbol's resolved identity.
- `NavigationLink` remains an open delivery-model question. A semantic target is not proof that a clickable
  link was written to an output PDF; [#93](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/93)
  covers its geometry and [#96](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/96) covers output
  provenance. No navigation-link class or emission claim is added in this semantic change.

The new terms address the UC-03 occurrence and multi-reference questions in the
[specification](../UC-03-Reference%20Symbol%20Cross-Sheet%20Linking.md#4-competency-questions).
They are schema terms, not a deployed exporter, populated knowledge graph or successful PDF navigation run.

## Source admission follows the final branch

The final accepted extraction branch determines an occurrence's expression type and selected source region.
An earlier detector box does not override a later inline acceptance or non-symbol decision. A branch that
abstains, remains provisional or is rejected retains its observations in evidence; it is not promoted to
an accepted ReferenceSymbol or InlineLayoutSheetReference. Independently accepted DrawingIdentifierMention facts
and Sheet resolution may remain. An accepted source LayoutIdentifierMention is retained even when its target is
missing or ambiguous; only its accepted target edge is withheld. Source composition and target resolution
are separate decisions.
