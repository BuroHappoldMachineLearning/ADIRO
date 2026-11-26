# Licensing

ADIRO is published under two licences, one for its ontologies and the resources around them, one for its code
([#276](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/276)).

| What | Where | Licence |
|---|---|---|
| The ontology modules | `src/*.ttl`, and their copies in `docs/` | [CC BY 4.0](LICENSES/CC-BY-4.0.txt) |
| The documentation and the specification (use cases, competency questions, design notes) | `docs/` (except its code, below), `README.md`, `AGENTS.md`, `CLAUDE.md` | [CC BY 4.0](LICENSES/CC-BY-4.0.txt) |
| The changelogs and the citation metadata | `changelogs/`, `CHANGELOG.md`, `CITATION.cff` | [CC BY 4.0](LICENSES/CC-BY-4.0.txt) |
| The data checks (SHACL shapes and queries) | `data-validation/` | [CC BY 4.0](LICENSES/CC-BY-4.0.txt) |
| The migration mapping | `migration/` | [CC BY 4.0](LICENSES/CC-BY-4.0.txt) |
| The example images | `assets/` | [CC BY 4.0](LICENSES/CC-BY-4.0.txt) |
| The display configurations | `src/*.display.json` | [CC BY 4.0](LICENSES/CC-BY-4.0.txt) |
| The code: scripts, the `ttl2md` package, tests, workflows, the site's scripts and styles | `scripts/`, `ttl2md/`, `tests/`, `.github/`, `docs/javascripts/`, `docs/stylesheets/` | [GPL-3.0](LICENSE) |
| The build and tool configuration | `config/`, `mkdocs.yml`, `pyproject.toml`, `uv.lock`, `.claude/`, `.cursor/` | [GPL-3.0](LICENSE) |

**Anything not listed is GPL-3.0** ([`LICENSE`](LICENSE)).

**Released versions keep the licence they were released under.** A snapshot under `versions/` is the file as released, and
its `dcterms:license` says its licence: the releases before this change are GPL-3.0, the releases after it CC BY 4.0.

**Generated pages include third-party code.** The pyLODE pages (`docs/*.html`) carry pyLODE's own styling and scripts, which
are under pyLODE's licence (BSD 3-Clause); the content generated from an ontology is the ontology's.

**Attribution** (CC BY 4.0): name ADIRO and link the resource, for example its `w3id.org/adiro` IRI or the repository's
DOI, as [`CITATION.cff`](CITATION.cff) gives it.

**What ADIRO does not license.** A licence covers only what ADIRO owns. Source drawings are not redistributed (an ADIRO
graph refers to a drawing by a link and a hash), so no drawing is licensed here; its rights stay with its holder. Standards
that ADIRO cites (ISO, EN and others) keep their own terms: ADIRO cites clause numbers and paraphrases, and does not
reproduce their text. An example image is added only if it can be published under CC BY 4.0
([Example images](docs/contribute/example-images.md)).
