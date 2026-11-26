# Adding a module

A module is one Turtle file directly in `src/` (the validator and the documentation read `src/*.ttl`, not subfolders). The
documentation build finds it and generates its pages, but a new module also needs the steps below. Each one names what fails, or
what goes wrong, without it.

Renaming a module is a different change, with its own steps: see "Renaming a module" in [Versioning](versioning/index.md).

## 1. Write `src/<module>.ttl`

- **The header**, which `scripts/validate_ontology.py` checks for agreement:
    - the ontology IRI `https://w3id.org/adiro/<module>`;
    - `owl:versionIRI <https://w3id.org/adiro/<module>/<version>>` and `owl:versionInfo "<version>"`, the same version in both. A
      module never released before is first released at the version it declares, so declare the one it should start at.
- **`dcterms:title`** ("ADIRO … Ontology") and an **`rdfs:comment`** on the `owl:Ontology`. That comment is the introduction of
  the module's page: a short paragraph on the module's role, not a list of its terms.
- **The prefix of the module's names** is "ad" and its role (`adprov:`, `admeta:`, …). Declare only the prefixes the module uses.
- **`owl:imports`** only the modules whose terms it uses.
- **Every term** has one `rdfs:label` in English and a `skos:definition`. Its `rdfs:comment`, if any, is commentary (see
  `AGENTS.md`, "Every ADIRO term needs a `skos:definition`").

Validate it at once: `uv run python scripts/validate_ontology.py src/<module>.ttl`.

## 2. Pin its imports in `config/module_imports.json`

Add an entry for the module, with each module it imports and the reason (`{}` when it imports none).
`tests/test_module_imports.py` fails while the pin and the real `owl:imports` differ.

## 3. Add it to `src/catalog-v001.xml`

Add a line `<uri name="https://w3id.org/adiro/<module>" uri="<module>.ttl"/>`, so the reasoner (`scripts/run_reasoning.sh`)
resolves an import of the module offline, as it does for the others.

## 4. Start `changelogs/<module>.md`

Copy the header of another module's changelog, and put a first entry under `## [Unreleased]` that says what the module is.
The validator warns on a pull request that changes `src/<module>.ttl` without its changelog, and the Release PR turns the
`[Unreleased]` section into the release notes.

## 5. Add a release badge to `README.md`

Copy another module's badge line in the release table and change the module name and the version. `tests/test_readme_badges.py`
fails without it, or when its link does not name the declared version.

## 6. Place it in the module order of `scripts/generate_docs.py`

Add the module to `dependency_order` in `sort_by_dependency`, after the modules it imports. The order drives the navigation of
the ontology pages, the index and the dependency diagrams. A module that is not listed is placed last.

## 7. Describe it in the specification

- The [modularization page](../specification/design-decisions/modularization/index.md): a row in its table and its imports in
  the diagram. `tests/test_modularization_page.py` fails until the page lists every module in `src/` with its namespace and imports.
- The module hierarchy of each use case that uses the module (§7 of UC-01 and UC-03), with a version bump of that page.
- The module list in `AGENTS.md` ("Purpose" and "Versioning").

## 8. Regenerate and check

```bash
uv run python scripts/generate_docs.py   # the module's pages, the index and the navigation
uv run pytest tests -q
uv run mkdocs build --strict
```

Optionally, add `src/<module>.display.json` for the module's layout in the interactive view; a module without one gets the
default layout.

Then open the pull request as `AGENTS.md` ("Contributor workflow") describes. Leave the release to the Release PR.
