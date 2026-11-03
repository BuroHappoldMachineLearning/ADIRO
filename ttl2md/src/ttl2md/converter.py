"""Core TTL/OWL -> Markdown conversion.

The converter parses an RDF ontology with :mod:`rdflib` and renders a single
Markdown document describing the ontology and its terms (classes, object
properties, datatype properties, annotation properties and named individuals).

Design goals
------------
* **Self-contained** -- the only runtime dependency is ``rdflib``. This package
  is intended to be extractable into its own repository / PyPI distribution
  without touching the consuming project.
* **Deterministic** -- terms are emitted in a stable, sorted order so the
  generated Markdown is diff-friendly and safe to commit.
* **Faithful to the source** -- restrictions, cardinalities, class expressions
  (unions, intersections, enumerations) and custom annotations are rendered
  rather than dropped.
* **Documentation-tool friendly** -- headings carry explicit ``{#localName}``
  anchors (via the ``attr_list`` Markdown extension) so intra-ontology
  references resolve regardless of the heading slugification used by the site
  generator.

The one behaviour deliberately mirrored from the previous pyLODE-based pipeline
is the rendering of *example image* annotations: any annotation property whose
local name is ``exampleImage`` (case-insensitive) is treated as an inline image
preview, reproducing the HTML post-processing that used to be applied to the
pyLODE output.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from rdflib import BNode, Graph, Literal, URIRef
from rdflib.namespace import OWL, RDF, RDFS, SKOS, XSD
from rdflib.namespace import split_uri

from .crosslinks import link_names, prefixed_name, targets_for

__all__ = [
    "MarkdownConverter",
    "convert_graph",
    "convert_file",
    "DEFAULT_EXAMPLE_IMAGE_LOCAL_NAME",
]

DEFAULT_EXAMPLE_IMAGE_LOCAL_NAME = "exampleimage"

# Matches an absolute URI scheme (http:, https:, data:, file:, …) so we never
# rewrite the path of an already-absolute image reference.
_ABSOLUTE_REF = re.compile(r"^[a-z][a-z0-9+.\-]*:", re.IGNORECASE)


def local_name(iri: str) -> str:
    """Return a best-effort local name for an IRI (the bit after ``#`` or ``/``)."""
    try:
        _, name = split_uri(URIRef(str(iri)))
        if name:
            return name
    except Exception:
        pass
    # Fall back to the last path/fragment segment, ignoring any trailing
    # separator (e.g. a namespace IRI ending in ``#``).
    text = str(iri).rstrip("#/")
    for sep in ("#", "/"):
        if sep in text:
            tail = text.rsplit(sep, 1)[-1]
            if tail:
                return tail
    return text


@dataclass
class Term:
    """A documented ontology term (class, property or individual)."""

    iri: str
    local: str
    label: str
    comment: str | None = None
    # Ordered (field-label, markdown-value) pairs, e.g. ("Sub class of", "[A](#A)").
    # A value may itself be a list, in which case it is rendered as a sub-list.
    metadata: list[tuple[str, list[str]]] = field(default_factory=list)
    # Non-standard annotation values, e.g. ("Labellable root", "true").
    annotations: list[tuple[str, str]] = field(default_factory=list)
    # Resolved image sources for exampleImage annotations, in declared order.
    images: list[str] = field(default_factory=list)


@dataclass
class OntologyDoc:
    """Structured, render-ready view of an ontology."""

    title: str
    iri: str | None = None
    comment: str | None = None
    version_info: str | None = None
    version_iri: str | None = None
    imports: list[str] = field(default_factory=list)
    classes: list[Term] = field(default_factory=list)
    object_properties: list[Term] = field(default_factory=list)
    datatype_properties: list[Term] = field(default_factory=list)
    annotation_properties: list[Term] = field(default_factory=list)
    individuals: list[Term] = field(default_factory=list)
    # SKOS concepts, grouped by the scheme they are in: (scheme, its concepts), and (None, the concepts in no scheme).
    concept_groups: list[tuple[Term | None, list[Term]]] = field(default_factory=list)


class MarkdownConverter:
    """Convert an :class:`rdflib.Graph` into a Markdown document.

    Parameters
    ----------
    asset_prefix:
        Prepended to relative (non-absolute) image references. Use this when the
        generated page lives in a sub-directory relative to the images, e.g.
        ``"../"`` for a page one level below the image folder.
    example_image_predicates:
        Explicit set of annotation-property IRIs to treat as example images. If
        ``None`` (default), any predicate whose local name equals
        ``exampleImage`` (case-insensitive) is used, matching the historical
        pyLODE post-processing.
    external_links:
        IRI -> URL of terms documented on other pages. The names of terms written
        in a definition link to the term's entry on this page, or to its page in
        this mapping (see :mod:`ttl2md.crosslinks` for the rules).
    """

    # Cardinality predicates grouped by the phrasing they map to.
    _EXACT_CARD = (OWL.qualifiedCardinality, OWL.cardinality)
    _MIN_CARD = (OWL.minQualifiedCardinality, OWL.minCardinality)
    _MAX_CARD = (OWL.maxQualifiedCardinality, OWL.maxCardinality)

    def __init__(
        self,
        *,
        asset_prefix: str = "",
        example_image_predicates: set[str] | None = None,
        external_links: dict[str, str] | None = None,
    ) -> None:
        self.asset_prefix = asset_prefix
        self.external_links = dict(external_links or {})
        self._explicit_example_predicates = (
            {str(p) for p in example_image_predicates}
            if example_image_predicates is not None
            else None
        )

    # -- public API -------------------------------------------------------

    def convert(self, graph: Graph, *, title: str | None = None) -> str:
        """Extract and render ``graph`` as Markdown."""
        doc = self.extract(graph, title=title)
        return self.render(doc)

    # -- extraction -------------------------------------------------------

    def extract(self, graph: Graph, *, title: str | None = None) -> OntologyDoc:
        self._graph = graph
        self._example_predicates = self._resolve_example_predicates(graph)
        # IRIs of terms defined in this document -> used to decide whether a
        # reference becomes an intra-page anchor link or an external code span.
        self._local_iris: set[str] = set()
        self._labels: dict[str, str] = {}

        ontology = self._find_ontology(graph)

        classes = self._collect(graph, (OWL.Class, RDFS.Class))
        object_props = self._collect(graph, (OWL.ObjectProperty,))
        datatype_props = self._collect(graph, (OWL.DatatypeProperty,))
        annotation_props = self._collect(graph, (OWL.AnnotationProperty,))
        # A SKOS concept or concept scheme is documented in the Concepts section, with its names, definition and
        # scheme, whether or not it is also declared an owl:NamedIndividual.
        concepts = self._collect(graph, (SKOS.Concept,))
        schemes = [s for s in self._collect(graph, (SKOS.ConceptScheme,)) if s not in concepts]
        individuals = [s for s in self._collect(graph, (OWL.NamedIndividual,)) if s not in concepts and s not in schemes]

        # Register every named term first so cross-references resolve.
        for subj in (*classes, *object_props, *datatype_props, *annotation_props, *individuals, *concepts, *schemes):
            iri = str(subj)
            self._local_iris.add(iri)
            self._labels[iri] = self._label_of(subj)

        # The names of terms written in a definition become links (ttl2md.crosslinks).
        self._link_targets = targets_for(
            graph,
            str(ontology) if ontology is not None else None,
            {iri: f"#{local_name(iri)}" for iri in self._local_iris},
            self.external_links,
        )

        doc = OntologyDoc(
            title=title or (self._label_of(ontology) if ontology else "Ontology"),
        )
        if ontology is not None:
            doc.iri = str(ontology)
            doc.comment = self._first_text(ontology, (RDFS.comment, SKOS.definition))
            doc.version_info = self._first_text(ontology, (OWL.versionInfo,))
            vi = graph.value(ontology, OWL.versionIRI)
            doc.version_iri = str(vi) if vi is not None else None
            doc.imports = sorted(str(o) for o in graph.objects(ontology, OWL.imports))

        doc.classes = [self._class_term(s) for s in classes]
        doc.object_properties = [self._property_term(s) for s in object_props]
        doc.datatype_properties = [self._property_term(s) for s in datatype_props]
        doc.annotation_properties = [self._property_term(s) for s in annotation_props]
        doc.individuals = [self._individual_term(s) for s in individuals]
        doc.concept_groups = self._concept_groups(schemes, concepts)

        for bucket in (
            doc.classes,
            doc.object_properties,
            doc.datatype_properties,
            doc.annotation_properties,
            doc.individuals,
        ):
            bucket.sort(key=lambda t: (t.label.lower(), t.local))

        return doc

    def _resolve_example_predicates(self, graph: Graph) -> set[str]:
        if self._explicit_example_predicates is not None:
            return self._explicit_example_predicates
        found = set()
        for p in set(graph.predicates()):
            if local_name(str(p)).lower() == DEFAULT_EXAMPLE_IMAGE_LOCAL_NAME:
                found.add(str(p))
        return found

    def _find_ontology(self, graph: Graph) -> URIRef | None:
        onts = [s for s in graph.subjects(RDF.type, OWL.Ontology) if isinstance(s, URIRef)]
        return sorted(onts, key=str)[0] if onts else None

    def _collect(self, graph: Graph, types: tuple) -> list[URIRef]:
        subjects: set[URIRef] = set()
        for t in types:
            for s in graph.subjects(RDF.type, t):
                if isinstance(s, URIRef):
                    subjects.add(s)
        return sorted(subjects, key=str)

    def _label_of(self, node) -> str:
        if node is None:
            return "Ontology"
        lbl = self._first_text(node, (RDFS.label, SKOS.prefLabel))
        return lbl if lbl else local_name(str(node))

    def _first_text(self, subject, predicates: tuple) -> str | None:
        for pred in predicates:
            values = sorted(
                (str(o) for o in self._graph.objects(subject, pred) if isinstance(o, Literal)),
            )
            if values:
                return values[0]
        return None

    def _class_term(self, subj: URIRef) -> Term:
        term = self._base_term(subj)
        named_supers: list[str] = []
        restrictions: list[str] = []
        for sup in self._graph.objects(subj, RDFS.subClassOf):
            if isinstance(sup, URIRef):
                named_supers.append(self._ref(sup))
            elif isinstance(sup, BNode):
                restrictions.append(self._class_expression(sup))
        if named_supers:
            term.metadata.append(("Sub class of", sorted(named_supers)))
        if restrictions:
            term.metadata.append(("Restrictions", sorted(restrictions)))

        equivalents = [
            self._class_expression(o) for o in self._graph.objects(subj, OWL.equivalentClass)
        ]
        if equivalents:
            term.metadata.append(("Equivalent to", sorted(equivalents)))

        one_of = self._graph.value(subj, OWL.oneOf)
        if one_of is not None:
            members = [self._ref(m) for m in self._rdf_list(one_of)]
            if members:
                term.metadata.append(("One of", members))
        return term

    def _property_term(self, subj: URIRef) -> Term:
        term = self._base_term(subj)
        for pred, label in (
            (RDFS.subPropertyOf, "Sub property of"),
            (RDFS.domain, "Domain"),
            (RDFS.range, "Range"),
            (OWL.inverseOf, "Inverse of"),
        ):
            values = [self._class_expression(o) for o in self._graph.objects(subj, pred)]
            if values:
                term.metadata.append((label, sorted(values)))
        char = self._property_characteristics(subj)
        if char:
            term.metadata.append(("Characteristics", char))
        return term

    def _individual_term(self, subj: URIRef) -> Term:
        term = self._base_term(subj)
        types = [
            self._ref(t)
            for t in self._graph.objects(subj, RDF.type)
            if isinstance(t, URIRef) and t != OWL.NamedIndividual
        ]
        if types:
            term.metadata.append(("Type", sorted(types)))
        return term

    # What a concept's entry shows in its own fields; any other statement about it is listed by its predicate.
    _CONCEPT_FIELDS = (
        RDF.type, RDFS.label, RDFS.comment, RDFS.isDefinedBy, SKOS.definition, SKOS.prefLabel, SKOS.altLabel,
        SKOS.example, SKOS.inScheme, SKOS.scopeNote, SKOS.note,
    )

    def _concept_groups(self, schemes: list[URIRef], concepts: list[URIRef]) -> list[tuple[Term | None, list[Term]]]:
        """Each scheme with its concepts, then the concepts in no scheme of this document, sorted by label."""
        def by_label(t: Term):
            return (t.label.lower(), t.local)

        members: dict[str, list[Term]] = {str(s): [] for s in schemes}
        loose: list[Term] = []
        for subj in concepts:
            term = self._concept_term(subj)
            in_schemes = sorted(str(s) for s in self._graph.objects(subj, SKOS.inScheme) if str(s) in members)
            (members[in_schemes[0]] if in_schemes else loose).append(term)  # under its first scheme only
        groups: list[tuple[Term | None, list[Term]]] = [
            (term, sorted(members[term.iri], key=by_label)) for term in sorted(map(self._scheme_term, schemes), key=by_label)
        ]
        if loose:
            groups.append((None, sorted(loose, key=by_label)))
        return groups

    def _scheme_term(self, subj: URIRef) -> Term:
        term = self._base_term(subj)
        self._add_notes(subj, term)
        return term

    def _concept_term(self, subj: URIRef) -> Term:
        """A concept's entry: its definition (skos:definition, else rdfs:comment), names, examples and scheme."""
        term = self._base_term(subj)
        definition = self._first_text(subj, (SKOS.definition,))
        if definition:
            comment = self._first_text(subj, (RDFS.comment,))
            term.comment = self._linked(subj, definition)
            if comment:
                term.metadata.append(("Comment", [self._linked(subj, comment)]))
        types = [self._ref(t) for t in self._graph.objects(subj, RDF.type)
                 if isinstance(t, URIRef) and t not in (SKOS.Concept, OWL.NamedIndividual)]
        if types:
            term.metadata.append(("Type", sorted(types)))
        schemes = [self._ref(s) for s in self._graph.objects(subj, SKOS.inScheme) if isinstance(s, URIRef)]
        if schemes:
            term.metadata.append(("In scheme", sorted(schemes)))
        for pred, label in ((SKOS.prefLabel, "Preferred labels"), (SKOS.altLabel, "Alternative labels"), (SKOS.example, "Examples")):
            values = self._literals(subj, pred)
            if values:
                term.metadata.append((label, [", ".join(values)]))
        self._add_notes(subj, term)
        for pred in sorted({p for p in self._graph.predicates(subj, None)}, key=str):
            if pred in self._CONCEPT_FIELDS or str(pred) in self._example_predicates:
                continue
            values = [self._ref(o) if isinstance(o, URIRef) else self._literal(o)
                      for o in self._graph.objects(subj, pred) if not isinstance(o, BNode)]
            if values:
                term.metadata.append((self._labels.get(str(pred)) or local_name(str(pred)), sorted(values)))
        term.annotations = []  # already listed above
        return term

    def _add_notes(self, subj: URIRef, term: Term) -> None:
        for pred, label in ((SKOS.scopeNote, "Scope note"), (SKOS.note, "Note")):
            for value in sorted(str(o) for o in self._graph.objects(subj, pred) if isinstance(o, Literal)):
                term.metadata.append((label, [self._linked(subj, value)]))

    def _literals(self, subj: URIRef, pred: URIRef) -> list[str]:
        """Each literal value, quoted, with its language: "Client" (en). English first, then by language and text."""
        values = [o for o in self._graph.objects(subj, pred) if isinstance(o, Literal)]
        values.sort(key=lambda o: (o.language not in (None, "en"), o.language or "", str(o)))
        return [self._literal(o) for o in values]

    @staticmethod
    def _literal(value: Literal) -> str:
        return f'"{value}"' + (f" ({value.language})" if value.language else "")

    def _property_characteristics(self, subj: URIRef) -> list[str]:
        mapping = {
            OWL.FunctionalProperty: "Functional",
            OWL.InverseFunctionalProperty: "Inverse functional",
            OWL.TransitiveProperty: "Transitive",
            OWL.SymmetricProperty: "Symmetric",
            OWL.AsymmetricProperty: "Asymmetric",
            OWL.ReflexiveProperty: "Reflexive",
            OWL.IrreflexiveProperty: "Irreflexive",
        }
        found = [name for t, name in mapping.items() if (subj, RDF.type, t) in self._graph]
        return sorted(found)

    def _base_term(self, subj: URIRef) -> Term:
        iri = str(subj)
        term = Term(
            iri=iri,
            local=local_name(iri),
            label=self._labels.get(iri, self._label_of(subj)),
            comment=self._linked(subj, self._first_text(subj, (RDFS.comment, SKOS.definition, RDFS.isDefinedBy))),
        )
        self._collect_annotations(subj, term)
        return term

    def _linked(self, subj: URIRef, text: str | None) -> str | None:
        """A definition with the names of other terms linked to their documentation."""
        if not text:
            return text
        own = {local_name(str(subj)), prefixed_name(self._graph, str(subj))}
        return link_names(text, self._link_targets, skip=own)

    def _collect_annotations(self, subj: URIRef, term: Term) -> None:
        images: list[str] = []
        seen_images: set[str] = set()
        for pred in self._example_predicates:
            for obj in self._graph.objects(subj, URIRef(pred)):
                src = self._resolve_asset(str(obj))
                if src not in seen_images:
                    seen_images.add(src)
                    images.append(src)
        term.images = images

        # Surface any other custom annotation-property values (e.g. labellableRoot)
        # that are not already rendered as label/comment/example-image.
        skip = {
            RDFS.label,
            RDFS.comment,
            SKOS.prefLabel,
            SKOS.definition,
            RDFS.isDefinedBy,
        }
        skip.update(URIRef(p) for p in self._example_predicates)
        annotation_props = set(self._graph.subjects(RDF.type, OWL.AnnotationProperty))
        for pred in sorted({p for p in self._graph.predicates(subj, None)}, key=str):
            if pred in skip or pred not in annotation_props:
                continue
            for obj in self._graph.objects(subj, pred):
                if isinstance(obj, Literal):
                    term.annotations.append((self._plabel(pred), str(obj)))

    def _plabel(self, pred: URIRef) -> str:
        return self._label_of(pred)

    # -- class-expression rendering --------------------------------------

    def _class_expression(self, node) -> str:
        """Render a class expression / node as a Markdown fragment."""
        if isinstance(node, Literal):
            return f"`{node}`"
        if isinstance(node, URIRef):
            return self._ref(node)
        if isinstance(node, BNode):
            if (node, RDF.type, OWL.Restriction) in self._graph:
                return self._restriction(node)
            for pred, joiner in (
                (OWL.unionOf, " or "),
                (OWL.intersectionOf, " and "),
            ):
                coll = self._graph.value(node, pred)
                if coll is not None:
                    parts = [self._class_expression(m) for m in self._rdf_list(coll)]
                    return "(" + joiner.join(parts) + ")"
            one_of = self._graph.value(node, OWL.oneOf)
            if one_of is not None:
                parts = [self._class_expression(m) for m in self._rdf_list(one_of)]
                return "{" + ", ".join(parts) + "}"
            comp = self._graph.value(node, OWL.complementOf)
            if comp is not None:
                return "not " + self._class_expression(comp)
            return "_anonymous class_"
        return f"`{node}`"

    def _restriction(self, node: BNode) -> str:
        prop = self._graph.value(node, OWL.onProperty)
        prop_md = self._ref(prop) if prop is not None else "_property_"

        for pred, word in (
            (OWL.someValuesFrom, "some"),
            (OWL.allValuesFrom, "only"),
            (OWL.hasValue, "value"),
        ):
            filler = self._graph.value(node, pred)
            if filler is not None:
                return f"{prop_md} {word} {self._class_expression(filler)}"

        filler = self._graph.value(node, OWL.onClass) or self._graph.value(
            node, OWL.onDataRange
        )
        filler_md = f" {self._class_expression(filler)}" if filler is not None else ""

        parts: list[str] = []
        exact = self._first_card(node, self._EXACT_CARD)
        if exact is not None:
            parts.append(f"exactly {exact}")
        else:
            mn = self._first_card(node, self._MIN_CARD)
            mx = self._first_card(node, self._MAX_CARD)
            if mn is not None:
                parts.append(f"min {mn}")
            if mx is not None:
                parts.append(f"max {mx}")
        card = " ".join(parts) if parts else "constrained"
        return f"{prop_md} {card}{filler_md}"

    def _first_card(self, node: BNode, preds: tuple) -> str | None:
        for pred in preds:
            val = self._graph.value(node, pred)
            if val is not None:
                return str(val)
        return None

    def _rdf_list(self, head) -> list:
        items = []
        try:
            items = list(self._graph.items(head))
        except Exception:
            # Fall back to manual traversal for malformed lists.
            node = head
            while node and node != RDF.nil:
                first = self._graph.value(node, RDF.first)
                if first is not None:
                    items.append(first)
                node = self._graph.value(node, RDF.rest)
        return items

    def _ref(self, node: URIRef) -> str:
        """Render a reference to a named term as a link (if local) or code span."""
        iri = str(node)
        if iri in self._local_iris:
            return f"[{self._labels.get(iri, local_name(iri))}](#{local_name(iri)})"
        if iri in self.external_links:  # documented on another page
            return f"[`{self._curie(node)}`]({self.external_links[iri]})"
        return f"`{self._curie(node)}`"

    def _curie(self, node: URIRef) -> str:
        try:
            curie = self._graph.namespace_manager.normalizeUri(node)
        except Exception:
            curie = None
        if not curie or curie.startswith("<"):
            return local_name(str(node))
        return curie

    def _resolve_asset(self, src: str) -> str:
        if not self.asset_prefix:
            return src
        if _ABSOLUTE_REF.match(src) or src.startswith("/") or src.startswith("#"):
            return src
        return self.asset_prefix + src

    # -- rendering --------------------------------------------------------

    def render(self, doc: OntologyDoc) -> str:
        out: list[str] = [f"# {doc.title}", ""]
        if doc.comment:
            out += [doc.comment.strip(), ""]

        meta: list[str] = []
        if doc.iri:
            meta.append(f"- **IRI:** `{doc.iri}`")
        if doc.version_iri:
            # The versioned IRI names the release and contains its version; the bare version is the fallback
            # for an ontology that declares no owl:versionIRI.
            meta.append(f"- **Versioned IRI:** `{doc.version_iri}`")
        elif doc.version_info:
            meta.append(f"- **Version:** {doc.version_info}")
        if doc.imports:
            imports_md = ", ".join(f"`{self._curie(URIRef(i))}`" for i in doc.imports)
            meta.append(f"- **Imports:** {imports_md}")
        if meta:
            out += meta + [""]

        self._render_section(out, "Classes", doc.classes)
        self._render_section(out, "Object Properties", doc.object_properties)
        self._render_section(out, "Datatype Properties", doc.datatype_properties)
        self._render_section(out, "Annotation Properties", doc.annotation_properties)
        self._render_section(out, "Named Individuals", doc.individuals)
        self._render_concepts(out, doc.concept_groups)

        return "\n".join(out).rstrip() + "\n"

    def _render_section(self, out: list[str], heading: str, terms: list[Term]) -> None:
        if not terms:
            return
        out += [f"## {heading}", ""]
        for term in terms:
            self._render_term(out, term)

    def _render_concepts(self, out: list[str], groups: list[tuple[Term | None, list[Term]]]) -> None:
        """The Concepts section: each scheme with its concepts below it, then the concepts in no scheme."""
        if not groups:
            return
        out += ["## Concepts", ""]
        for scheme, concepts in groups:
            if scheme is None:
                out += ["### Concepts in no scheme", ""]
            else:
                self._render_term(out, scheme)
            for concept in concepts:
                self._render_term(out, concept, level=4)

    def _render_term(self, out: list[str], term: Term, level: int = 3) -> None:
        out += [f"{'#' * level} {term.label} {{#{term.local}}}", ""]
        if term.comment:
            out += [term.comment.strip(), ""]
        out.append(f"- **IRI:** `{term.iri}`")
        for label, value in term.metadata:
            values = value if isinstance(value, list) else [value]
            values = [v for v in values if v]
            if not values:
                continue
            if len(values) == 1:
                out.append(f"- **{label}:** {values[0]}")
            else:
                out.append(f"- **{label}:**")
                out += [f"    - {v}" for v in values]
        for label, value in term.annotations:
            out.append(f"- **{label}:** {value}")
        out.append("")
        if term.images:
            out += ["*Example images:*", ""]
            for src in term.images:
                out += [f"![{term.label} — example]({src})", ""]


def convert_graph(graph: Graph, *, title: str | None = None, **kwargs) -> str:
    """Convenience wrapper: render an already-parsed graph to Markdown."""
    return MarkdownConverter(**kwargs).convert(graph, title=title)


def convert_file(
    source: str | Path,
    *,
    title: str | None = None,
    rdf_format: str | None = None,
    **kwargs,
) -> str:
    """Parse an ontology file and render it to Markdown.

    ``rdf_format`` is passed to :meth:`rdflib.Graph.parse`; when omitted rdflib
    guesses from the file extension.
    """
    graph = Graph()
    graph.parse(str(source), format=rdf_format)
    return convert_graph(graph, title=title, **kwargs)
