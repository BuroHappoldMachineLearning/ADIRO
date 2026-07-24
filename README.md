# AEC Drawing Ontologies

Set of ontologies representing information in AEC drawings

https://burohappoldmachinelearning.github.io/ADIRO/

## Use Cases

The ontology is developed against a set of use cases following the **LOT (Linked Open Terms)** methodology (`Use Case → Information Needs → Functional Requirements → Competency Questions → OWL Terms`).

See [docs/uc-orsd/README.md](docs/uc-orsd/README.md) for the full use case catalogue, prioritization matrix, and current ORSD status across all use cases (UC-01 through UC-07).

## Documentation

Find the docs here: https://burohappoldmachinelearning.github.io/ADIRO/.

The documentation site is built with **[Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)** and deployed to GitHub Pages whenever:
- Changes are pushed to the `main` or `master` branch
- The workflow is manually triggered from the GitHub Actions tab

The site provides a landing page (`docs/index.md`), a **Use Cases** page (`docs/uc-orsd/README.md`), an **Ontology Requirements (ORSD)** page (`docs/ORSD_v1.md`), and a detailed per-ontology reference page for each ontology, generated with **[pyLODE](https://github.com/RDFLib/pyLODE)**.

### How it fits together

- `scripts/generate_docs.py` reads every `.ttl` in `src/`, generates a pyLODE HTML reference page for each into `docs/`, copies the `.ttl` and `*.display.json` sources into `docs/`, and (re)generates the MkDocs landing page `docs/index.md` (including the auto-discovered list of ontologies).
- `mkdocs.yml` configures the Material site. It uses `docs/` as its source directory, so the generated pyLODE HTML pages, the `.ttl` sources, and the `.display.json` files are copied verbatim into the built site alongside the Markdown pages.
- The site is built into `site/` (git-ignored) and deployed to GitHub Pages.

### Building the docs locally

<details>

```bash
# Install dependencies
uv sync

# 1. Generate the pyLODE ontology pages + the MkDocs landing page (index.md)
uv run python scripts/generate_docs.py

# 2a. Preview the site locally with live reload
uv run mkdocs serve

# 2b. ...or build the static site into site/
uv run mkdocs build
```

Each `.ttl` file in `src/` gets a corresponding `.html` reference page in `docs/`, and any `*.display.json` files are copied to `docs/` for public access via GitHub Pages. The final static site is produced in `site/`.

</details>

### Adding New Ontologies

Simply add a new `.ttl` file to the `src` folder, or in a subfolder to `src`.  
The next time the documentation workflow runs (automatically on push or manually), it will discover and document the new ontology file automatically.

## Versioning

The ontologies use OWL 2 versioning best practices with unversioned and versioned IRIs:

- **Unversioned ontology IRI**: `https://burohappoldmachinelearning.github.io/ADIRO/aec-core` (always resolves to current version)
- **Versioned ontology IRI**: `https://burohappoldmachinelearning.github.io/ADIRO/aec-core/1.0.0` (specific version)
- **Namespace prefix**: `https://burohappoldmachinelearning.github.io/ADIRO/aec-core#` (unversioned, always current)

Each ontology declares both an unversioned IRI and a versioned IRI using `owl:versionIRI` and `owl:versionInfo`. The filenames do not include version numbers (e.g., `aec_core.ttl` rather than `aec_core_v01.ttl`).

### Version Backups

When a new version is released (via a tagged release in GitHub), the current version of all ontology files is automatically backed up to the `versions/` folder. The backup process is triggered automatically by GitHub Actions when a release tag is created or published.

The backup structure is:

```
versions/
  1.0.0/
    aec_core.ttl
    aec_drawing_metadata.ttl
    aec_common_symbols.ttl
    aec_domain_common.ttl
    aec_facade_domain.ttl
  1.1.0/
    ...
```

This backup process preserves the complete state of all ontology files at each release point, allowing for:

- Historical reference and comparison
- Rollback capabilities if needed
- Clear versioning documentation

### Creating a New Version

To create a new version:

1. Make your changes to the ontology files in `src/`
2. Update the version number in the ontology IRI (e.g., `1.0.0` → `1.1.0`) and update `owl:versionIRI` and `owl:versionInfo` in all ontology files
3. Commit and push your changes to `main` or `master`
4. The `deploy-docs` workflow will automatically:
   - Validate all ontology files
   - Generate documentation
   - Deploy to GitHub Pages
5. Create a new release in GitHub with a tag matching the version (e.g., `v1.1.0` or `1.1.0`)
6. The `backup-version` workflow will automatically:
   - Extract the version from the release tag
   - Copy all `.ttl` files from `src/` to `versions/<version>/`
   - Commit and push the backup to the repository


## Design decisions

### Why OWL restrictions for contains

`contains` is an **object property**: it relates individuals to individuals. In OWL, class axioms describe constraints on instances. To express "Class A can contain Class B" (0 or more) at the class level, we use an **OWL restriction** with qualified cardinality:

```turtle
:Layout rdfs:subClassOf [ rdf:type owl:Restriction ;
                         owl:onProperty :contains ;
                         owl:minQualifiedCardinality 0 ;
                         owl:onClass :Annotation
                       ] .
```

Min cardinality 0 means "can contain" (optional). Use min ≥ 1 for "must contain".

### Annotation properties

OWL annotation properties attach metadata to classes without affecting logical reasoning. We use custom annotation properties for application-specific behaviour.

**Example: labellableRoot** — A boolean we use to mark which classes can serve as labels in diagrams. When `true`, the class is shown as a solid contour (labellable); when `false`, as a dashed contour (structural/category node). This drives filtering and styling in the visualizer and editor.

Other annotation properties (e.g. `rdfs:label`, `rdfs:comment`) follow standard OWL usage.

### Relationship examples

- **rdfs:subClassOf** — Taxonomy: e.g. `CurtainWallSystem` subClassOf `FacadeSystem`
- **contains** — Containment: e.g. a layout can contain drawing elements (via OWL restrictions)
- **hasFunction**, **hasMaterial** — Domain-specific: e.g. a facade component has a function or material
