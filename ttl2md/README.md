# ttl2md

Convert OWL/RDFS ontologies (Turtle, RDF/XML, JSON-LD, N-Triples, …) into clean,
diff-friendly **Markdown** documentation — ideal for static-site generators such
as MkDocs / Material for MkDocs, where the output pages are themed, searchable
and get an in-page table of contents for free.

> **Status:** developed inside the [ADIRO](https://github.com/BuroHappoldMachineLearning/ADIRO)
> project and vendored here as a self-contained package. It is intended to be
> extracted into its own repository / PyPI distribution later; the only runtime
> dependency is [`rdflib`](https://rdflib.dev/).

## Why

Tools like [pyLODE](https://github.com/RDFLib/pyLODE) v3 only emit standalone
HTML. When you publish an ontology inside a Markdown documentation site you often
want *native* Markdown pages instead — so they inherit the site theme, are
indexed by the site's search, and can be cross-linked like any other page.
`ttl2md` fills that gap with a small, dependency-light, well-tested converter.

## Install

```bash
pip install ttl2md          # once published
# or, from a checkout:
pip install -e .
```

## CLI

```bash
ttl2md my_ontology.ttl -o my_ontology.md
ttl2md my_ontology.ttl --title "My Ontology" --asset-prefix ../
python -m ttl2md my_ontology.ttl        # prints Markdown to stdout
```

## Python API

```python
from ttl2md import convert_file, convert_graph, MarkdownConverter

# One-shot from a file:
markdown = convert_file("my_ontology.ttl", asset_prefix="../")

# From an already-parsed rdflib graph:
from rdflib import Graph
g = Graph().parse("my_ontology.ttl", format="turtle")
markdown = convert_graph(g, title="My Ontology")

# Full control / reuse:
conv = MarkdownConverter(asset_prefix="../")
doc = conv.extract(g)     # structured OntologyDoc (dataclasses)
markdown = conv.render(doc)
```

## What it renders

- Ontology metadata: title, IRI, `owl:versionInfo`, `owl:imports`.
- **Classes** — description, `rdfs:subClassOf` (named super-classes as intra-page
  links), OWL **restrictions** with cardinalities (`min`/`max`/`exactly`,
  qualified and unqualified), `owl:equivalentClass`, `owl:oneOf` enumerations.
- **Object / Datatype / Annotation properties** — description, domain, range,
  sub-property-of, inverse-of, and property characteristics (functional,
  transitive, symmetric, …).
- **Named individuals** — with their class memberships.
- **Class expressions** — unions (`A or B`), intersections (`A and B`),
  enumerations (`{a, b}`) and complements (`not A`), rendered recursively.
- **Example images** — any annotation property whose local name is
  `exampleImage` (case-insensitive) is rendered as an inline image preview,
  reproducing the HTML post-processing previously applied to pyLODE output.
  Configurable via `example_image_predicates`.

Headings carry explicit `{#localName}` anchors (via the `attr_list` Markdown
extension) so intra-ontology references resolve regardless of heading
slugification. Output is deterministically ordered, so it is safe to commit.

### Image paths

Relative image references (string literals like `img/x.png`) can be rewritten
with `asset_prefix` so they resolve from a page in a sub-directory. Absolute
references — including relative IRIs that RDF resolves against an `@base` into an
absolute URL — are left untouched.

## Development

```bash
pip install -e ".[test]"
pytest
```

## License

MIT
