# Changelog — adiro_discipline_core

Per-module SemVer. See [../docs/contribute/versioning/](../docs/contribute/versioning/).
Format: [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Changed
- **The module is licensed CC BY 4.0** ([#276](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/276)), not GPL-3.0: `dcterms:license` names <https://creativecommons.org/licenses/by/4.0/>. Reuse needs attribution only, so another ontology can import or extend its terms under its own licence. Earlier releases keep the licence they were released under. `LICENSING.md` says what in the repository is under which licence. No IRI, axiom or term changes.
- **The header carries the metadata vocabulary catalogues read** ([#284](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/284)): `vann:preferredNamespacePrefix` and `vann:preferredNamespaceUri`, `dcterms:issued` (the first release under this name) and `dcterms:modified` (the latest release, which the release cut now keeps up to date). `dcterms:description` is the module's introduction, the same text as its `rdfs:comment`; it was an older, shorter text that said something else. No IRI, axiom or term changes.

### Changed
- **The module's introduction names the module it builds on** ([#324](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/324)): it said the module "sits between the drawing symbology and the discipline-specific modules", but it imports only `adiro_drawing_metadata`. It now says it builds on the drawing-metadata module. No IRI, axiom or term changes.

## [5.0.0] — 2026-11-26

### Changed
- **BREAKING: renamed from `adiro_domain_common`** ([#281](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/281)). The module, its ontology IRI and the IRI of every term it defines now use `adiro_discipline_core` (`https://w3id.org/adiro/adiro_discipline_core`) instead of `adiro_domain_common`, and the title says "ADIRO Discipline Core Ontology". Nothing else changes: the terms, their definitions and their axioms are those of the old module's final release, whose version this release follows with a MAJOR bump. Every release of the old module stays published at its own IRI and is named here with `owl:priorVersion`; its history is in [its changelog](adiro_domain_common.md), and the old module is deprecated for its final release (adiro_domain_common 4.0.1) and stays in `src/` for one release cycle. The example images are published under the new module's path. `migration/aec_to_adiro.ttl` maps each old term IRI, from `aec_*` and from the earlier `adiro_*` module, to the new one, and `scripts/migrate_aec_to_adiro.py` rewrites a graph or a list of links. Downstream consumers may need adjustments: the annotation tooling reads the class IRIs, so every class and property of the module has a new IRI.
