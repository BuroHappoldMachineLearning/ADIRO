# Changelog — adiro_facade_discipline

Per-module SemVer. See [../docs/contribute/versioning/](../docs/contribute/versioning/).
Format: [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Changed
- **The module is licensed CC BY 4.0** ([#276](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/276)), not GPL-3.0: `dcterms:license` names <https://creativecommons.org/licenses/by/4.0/>. Reuse needs attribution only, so another ontology can import or extend its terms under its own licence. Every earlier release, which states GPL-3.0, is also licensed CC BY 4.0 ([#333](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/333)). `LICENSING.md` says what in the repository is under which licence. No IRI, axiom or term changes.
- **The header carries the metadata vocabulary catalogues read** ([#284](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/284)): `vann:preferredNamespacePrefix` and `vann:preferredNamespaceUri`, `dcterms:issued` (the first release under this name) and `dcterms:modified` (the latest release, which the release cut now keeps up to date). `dcterms:description` is the module's introduction, the same text as its `rdfs:comment`; it was an older, shorter text that said something else. No IRI, axiom or term changes.
- **The module's introduction names the modules it builds on** ([#324](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/324)): it named the symbology module, which it does not import. It now says it builds on the drawing-metadata and discipline-core modules. No IRI, axiom or term changes.

## [5.0.0] — 2026-11-26

### Changed
- **BREAKING: renamed from `adiro_facade_domain`** ([#281](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/281)). The module, its ontology IRI and the IRI of every term it defines now use `adiro_facade_discipline` (`https://w3id.org/adiro/adiro_facade_discipline`) instead of `adiro_facade_domain`, and the title says "ADIRO Facade Discipline Ontology". Nothing else changes: the terms, their definitions and their axioms are those of the old module's final release, whose version this release follows with a MAJOR bump. Its import and its prefix follow `adiro_discipline_core`. Every release of the old module stays published at its own IRI and is named here with `owl:priorVersion`; its history is in [its changelog](adiro_facade_domain.md), and the old module is deprecated for its final release (adiro_facade_domain 4.0.1) and stays in `src/` for one release cycle. The example images are published under the new module's path. `migration/aec_to_adiro.ttl` maps each old term IRI, from `aec_*` and from the earlier `adiro_*` module, to the new one, and `scripts/migrate_aec_to_adiro.py` rewrites a graph or a list of links. Downstream consumers may need adjustments: the annotation tooling reads the class IRIs, so every class and property of the module has a new IRI.
