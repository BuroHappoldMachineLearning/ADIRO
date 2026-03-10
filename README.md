# AEC Drawing Ontologies

Set of ontologies representing information in AEC drawings

https://burohappoldmachinelearning.github.io/ADIRO/

## Documentation

HTML documentation for all ontology files is automatically generated using [pyLODE](https://github.com/RDFLib/pyLODE).

### Automated Generation

Documentation is automatically generated and deployed to GitHub Pages whenever:
- Changes are pushed to the `main` or `master` branch
- The workflow is manually triggered from the GitHub Actions tab

The documentation is available at the repository's GitHub Pages URL (typically `https://<username>.github.io/<repository-name>/`).

### Manual Generation

To generate documentation locally:

```bash
# Install dependencies
uv sync

# Generate documentation for all TTL files in the root directory
uv run python scripts/generate_docs.py
```

The generated files will be placed in the `docs/` directory. Each `.ttl` file in the repository root will have a corresponding `.html` file generated, and any `*.display.json` files in the repository root will also be copied to `docs/` for public access via GitHub Pages.

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
