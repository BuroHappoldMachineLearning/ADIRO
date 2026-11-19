# Moving from `aec_*` to `adiro_*`

The six ADIRO modules were called `aec_provenance`, `aec_geometry`, `aec_drawing_metadata`, `aec_common_symbols`,
`aec_domain_common` and `aec_facade_domain`. They are now `adiro_provenance`, `adiro_geometry`, `adiro_drawing_metadata`,
`adiro_common_symbols`, `adiro_domain_common` and `adiro_facade_domain`
([#171](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/171)): "AEC" is already the A of ADIRO.

## What changed

Only the names. Each `adiro_*` module holds the terms, definitions and axioms of the final release of its `aec_*`
predecessor, under new IRIs:

| What | Before | After |
|---|---|---|
| Ontology | `https://w3id.org/adiro/aec_geometry` | `https://w3id.org/adiro/adiro_geometry` |
| Term | `https://w3id.org/adiro/aec_geometry#BoundingBox` | `https://w3id.org/adiro/adiro_geometry#BoundingBox` |
| Example image | `https://w3id.org/adiro/aec_drawing_metadata/exampleImage/Titleblock_01.png` | `https://w3id.org/adiro/adiro_drawing_metadata/exampleImage/Titleblock_01.png` |
| Release | `https://w3id.org/adiro/aec_geometry/2.0.0` | unchanged: a release keeps its IRI |

The version numbering continues: the first release of each `adiro_*` module is the final `aec_*` release plus a MAJOR
(`aec_drawing_metadata` 6.0.0 is followed by `adiro_drawing_metadata` 7.0.0).

## What stays

Every `aec_*` release stays published at its own IRI, with its documentation page, its Turtle file and its example
images. The final release of each says `owl:deprecated true` and `dcterms:isReplacedBy` the new module, and each new
module says `dcterms:replaces` the old one and names every old release with `owl:priorVersion`. Data that pins a release
(for example with `dcterms:conformsTo <https://w3id.org/adiro/aec_geometry/2.0.0>`) keeps resolving.

## How to move

- **The mapping.** [`migration/aec_to_adiro.ttl`](https://w3id.org/adiro/migration/aec_to_adiro.ttl) states, for each
  old ontology and term, `<old> dcterms:isReplacedBy <new>`.
- **A graph.** `uv run python scripts/migrate_aec_to_adiro.py rewrite data.ttl` writes `data.adiro.ttl`, with every old
  ontology, term and image IRI replaced and the IRIs of releases left as they are. Turtle, N-Triples, RDF/XML, JSON-LD,
  TriG and N-Quads are read by their extension.
- **Any other text.** `uv run python scripts/migrate_aec_to_adiro.py links export.json` does the same in a list of links,
  a JSON or CSV export or code, and leaves the rest of the text as it is.
- **Tools that read the labelling annotations** (`isComputerVisionLabel`, `isComputerVisionOptionalLabel`, `exampleImage`)
  read them in the `adiro_drawing_metadata` namespace from now on, and the class IRIs they build labels from are the
  `adiro_*` ones.

Data written against an `aec_*` release older than the final one may use terms that the final release moved or
removed; the changelogs of the old modules list those changes, and the rewrite does not cover them.

## Classes renamed since

Two classes of `adiro_drawing_metadata` changed name after the module rename
([#271](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/271)): `InlineLayoutSheetReference` is now
`InlineLayoutDrawingReference`, and `StandaloneSheetReference` is now `StandaloneDrawingReference`. The old IRIs stay,
deprecated and `owl:equivalentClass` to the new ones. The mapping above and the `rewrite` and `links` commands send an old IRI,
whether `aec_drawing_metadata#…` or `adiro_drawing_metadata#…`, straight to the new class. The renames are listed in
`config/term_renames.json`.

## Renamed again: three modules

Three modules changed name a second time ([#281](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/281)): `adiro_common_symbols` is now `adiro_drawing_symbology`, `adiro_domain_common` is now
`adiro_discipline_core` and `adiro_facade_domain` is now `adiro_facade_discipline`. Nothing else about them changes: the terms, definitions and axioms are
those of the final release of the module they replace, under new IRIs, and the numbering continues (the first release of each new module is the old
final release plus a MAJOR). The old modules stay published, deprecated, for one release cycle, and every old release keeps its IRI.

The mapping above, the `rewrite` command and the `links` command send an IRI of the first, the second or any earlier name straight to the module's
current name, so a graph written against `aec_common_symbols` or `adiro_common_symbols` ends at `adiro_drawing_symbology`. The prefixes used in this
repository follow (`csymbol:` is `adsym:`, `dcommon:` is `adcore:`), and a SPARQL query written with the old namespaces needs the new ones.
