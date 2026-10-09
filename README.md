# AEC Drawing Ontologies

<!-- Latest-release badges: one per module in src/ (checked by tests/test_readme_badges.py). Each reads
     badges/<module>.json from the docs site (scripts/release_badges.py), which every docs deploy refreshes
     from versions/, so the badges update after a release is published. -->
<table align="center">
  <tr>
    <td><img src="docs/img/adiro_banner.png" alt="ADIRO" width="320"></td>
    <td align="left" valign="middle">
      <b>Latest releases</b><br>
      <a href="https://burohappoldmachinelearning.github.io/ADIRO/ontologies/aec_provenance/"><img src="https://img.shields.io/endpoint?url=https%3A%2F%2Fburohappoldmachinelearning.github.io%2FADIRO%2Fbadges%2Faec_provenance.json" alt="aec_provenance"></a><br>
      <a href="https://burohappoldmachinelearning.github.io/ADIRO/ontologies/aec_geometry/"><img src="https://img.shields.io/endpoint?url=https%3A%2F%2Fburohappoldmachinelearning.github.io%2FADIRO%2Fbadges%2Faec_geometry.json" alt="aec_geometry"></a><br>
      <a href="https://burohappoldmachinelearning.github.io/ADIRO/ontologies/aec_drawing_metadata/"><img src="https://img.shields.io/endpoint?url=https%3A%2F%2Fburohappoldmachinelearning.github.io%2FADIRO%2Fbadges%2Faec_drawing_metadata.json" alt="aec_drawing_metadata"></a><br>
      <a href="https://burohappoldmachinelearning.github.io/ADIRO/ontologies/aec_common_symbols/"><img src="https://img.shields.io/endpoint?url=https%3A%2F%2Fburohappoldmachinelearning.github.io%2FADIRO%2Fbadges%2Faec_common_symbols.json" alt="aec_common_symbols"></a><br>
      <a href="https://burohappoldmachinelearning.github.io/ADIRO/ontologies/aec_domain_common/"><img src="https://img.shields.io/endpoint?url=https%3A%2F%2Fburohappoldmachinelearning.github.io%2FADIRO%2Fbadges%2Faec_domain_common.json" alt="aec_domain_common"></a><br>
      <a href="https://burohappoldmachinelearning.github.io/ADIRO/ontologies/aec_facade_domain/"><img src="https://img.shields.io/endpoint?url=https%3A%2F%2Fburohappoldmachinelearning.github.io%2FADIRO%2Fbadges%2Faec_facade_domain.json" alt="aec_facade_domain"></a><br>
    </td>
  </tr>
</table>

ADIRO (*AEC Drawing Information Representation Ontologies*) is a set of ontologies for AEC (*Architecture, Engineering, and Construction*) drawing representation, designed to support machine learning tasks, in particular information extraction workflows.

The ontologies include concepts for drawing metadata, common symbols, domain-common symbols, and domain-specific symbols. They can be used to represent the information in AEC drawings, to make them machine-readable, and to support the creation of graph databases and knowledge graphs.

## Documentation

Find the docs here: https://burohappoldmachinelearning.github.io/ADIRO/.

The documentation site is built with **[Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)** and deployed to GitHub Pages whenever:
- Changes are pushed to the `main` or `master` branch
- The workflow is manually triggered from the GitHub Actions tab

The site provides a landing page (`docs/index.md`), a **Use Cases** page (`docs/specification/use-cases/README.md`), an **Ontology Requirements (ORSD)** page (`docs/specification/ORSD_v1.2.md`), and a detailed per-ontology reference page for each ontology, generated with **[pyLODE](https://github.com/RDFLib/pyLODE)**.

### Documentation website automation

- `scripts/generate_docs.py` reads every `.ttl` in `src/`, generates a pyLODE HTML reference page for each into `docs/`, copies the `.ttl` and `*.display.json` sources into `docs/`, and (re)generates the MkDocs landing page `docs/index.md` (including the auto-discovered list of ontologies).
- `mkdocs.yml` configures the Material site. It uses `docs/` as its source directory, so the generated pyLODE HTML pages, the `.ttl` sources, and the `.display.json` files are copied verbatim into the built site alongside the Markdown pages.
- The site is built into `site/` (git-ignored) and deployed to GitHub Pages.

### Preview the site locally

To view the documentation site on your machine with live reload:

```bash
# 1. Install dependencies (once)
uv sync

# 2. Generate the pyLODE ontology pages + the MkDocs landing page (docs/index.md)
uv run python scripts/generate_docs.py

# 3. Start the live-reloading preview server
uv run mkdocs serve
```

Then open **http://127.0.0.1:8000/ADIRO/** in your browser. The server rebuilds automatically whenever you edit a file under `docs/` or `mkdocs.yml`.

> Tip: to serve on a different address/port, use e.g. `uv run mkdocs serve -a localhost:8001`.

### Building the static site

To produce the deployable static site (what CI publishes to GitHub Pages):

<details>

```bash
uv run python scripts/generate_docs.py   # regenerate ontology pages + index.md
uv run mkdocs build                       # outputs the static site into site/
```

Each `.ttl` file in `src/` gets a corresponding `.html` reference page in `docs/`, and any `*.display.json` files are copied to `docs/` for public access via GitHub Pages. The final static site is produced in `site/` (git-ignored).

</details>

## Contributing

Contributions are welcome — please propose additions or changes as a
**[GitHub issue](https://github.com/BuroHappoldMachineLearning/ADIRO/issues)**.

See the **[Contribute](https://burohappoldmachinelearning.github.io/ADIRO/contribute/)** section of the documentation site for details:

- **[Adding New Ontologies](https://burohappoldmachinelearning.github.io/ADIRO/contribute/adding-ontologies/)** — how to add a new `.ttl` and have it documented automatically.
- **[Versioning](https://burohappoldmachinelearning.github.io/ADIRO/contribute/versioning/)** — versioned/unversioned IRIs, version backups, and how to cut a new version.
- **[Design Decisions](https://burohappoldmachinelearning.github.io/ADIRO/design-decisions/)** — rationale behind OWL restrictions, annotation properties, and relationship modelling.
