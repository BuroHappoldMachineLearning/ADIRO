# Adding New Ontologies

Simply add a new `.ttl` file to the `src` folder, or in a subfolder to `src`.

The next time the documentation workflow runs (automatically on push or manually), it will discover and document the new ontology file automatically — generating both the interactive pyLODE HTML page and a native Markdown reference page (via [`ttl2md`](https://github.com/BuroHappoldMachineLearning/ADIRO/tree/main/ttl2md)) under the **Ontologies** section.

!!! note "One manual step: the navigation entry"
    The site navigation (`nav:` in `mkdocs.yml`) is curated, so after adding a new ontology add a line for its generated page under the `Ontologies:` section, e.g.:

    ```yaml
    - Ontologies:
        - ontologies/index.md
        - My New Ontology: ontologies/my_new_ontology.md
    ```
