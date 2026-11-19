#!/usr/bin/env python3
"""
The Metadata block of a pyLODE reference page: which IRI and title it shows, the two links it gets, and the check that it
is right (#146).

pyLODE reads every ``owl:Ontology``, ``skos:ConceptScheme`` and ``prof:Profile`` as "the ontology", merges their
properties into the page's Metadata block and keeps the last subject's IRI. A module that declares a concept scheme
(``aec_drawing_metadata`` declares ``TitleblockFieldScheme``) therefore showed the scheme's IRI, both titles in the
heading and a second schema.org block. ``graph_for_pylode`` hands pyLODE the module's graph without that type, which is
enough: pyLODE shows no section of its own for the scheme or its concepts.

The page also gets two rows, added by ``add_links`` to the page itself, not to the Turtle: the TTL source and the
documentation page, both at ``w3id.org/adiro``. A deprecated module also gets a "Deprecated" row (``add_deprecation``,
#171), because pyLODE shows neither ``owl:deprecated`` nor ``dcterms:isReplacedBy`` on the ontology. ``check`` compares a generated page with its Turtle, so a module (or an
archived release) cannot publish the wrong IRI or heading.

A term's definition is a ``skos:definition`` and its commentary an ``rdfs:comment`` (#273). Left alone, pyLODE shows both
(with ``dc:description`` and ``sdo:description``) together in one list under a single *Description* label, so a reader cannot
tell the definition from the commentary. The generated page shows them apart instead: a labelled *Definition* row, then a
labelled *Comment* row. ``graph_for_pylode`` marks each ``skos:definition`` with an invisible sequence (``MARK``), which survives
pyLODE's Markdown, and ``separate_definitions`` uses the mark to build the two rows, then removes it. A term with no
``skos:definition`` keeps pyLODE's *Description* row.
"""
import html as htmllib
import re
from pathlib import Path

from rdflib import Graph, Literal
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SKOS

SITE = "https://w3id.org/adiro"
ROW = (
    "<div>\n"
    "            <dt>\n"
    "              <strong>{label}</strong>\n"
    "            </dt>\n"
    "            <dd>\n"
    '              <a href="{url}">{url}</a>\n'
    "            </dd>\n"
    "          </div>\n"
)
TEXT_ROW = (
    "<div>\n"
    "            <dt>\n"
    "              <strong>{label}</strong>\n"
    "            </dt>\n"
    "            <dd>{text}</dd>\n"
    "          </div>\n"
)
SECTION = re.compile(r'<div class="section" id="metadata">(.*?)(?=<div class="section"|\Z)', re.S)
IRI_ROW = re.compile(r"(<dt>\s*<strong>IRI</strong>\s*</dt>\s*<dd>\s*<code>)(.*?)(</code>\s*</dd>\s*</div>\s*)", re.S)
HEADING = re.compile(r"<h1>(.*?)</h1>", re.S)


MARK = "\u2063\u2064\u2063"  # invisible separator, invisible plus, invisible separator: never in a written definition
_DESCRIPTION_ROW = re.compile(
    r'<tr>\s*<th>\s*<a class="hover_property" href="http://purl\.org/dc/terms/description"[^>]*>Description</a>\s*</th>\s*'
    r"<td>(.*?)</td>\s*</tr>", re.S)
_LIST_ITEM = re.compile(r"<li>(.*?)</li>", re.S)
_ROW = (
    "<tr>\n"
    "              <th>\n"
    '                <a class="hover_property" href="{href}" title="{title}">{label}</a>\n'
    "              </th>\n"
    "              <td>{cell}</td>\n"
    "            </tr>"
)


def graph_for_pylode(ttl_file) -> Graph:
    """The module's graph without the type ``skos:ConceptScheme``, and with each ``skos:definition`` marked (see the module
    docstring)."""
    graph = Graph().parse(str(ttl_file), format="turtle")
    for scheme in list(graph.subjects(RDF.type, SKOS.ConceptScheme)):
        graph.remove((scheme, RDF.type, SKOS.ConceptScheme))
    for subject, value in list(graph.subject_objects(SKOS.definition)):
        if isinstance(value, Literal):
            graph.remove((subject, SKOS.definition, value))
            marked = MARK + str(value)
            graph.add((subject, SKOS.definition, Literal(marked, lang=value.language) if value.language
                       else Literal(marked, datatype=value.datatype)))
    return graph


def _cell(items):
    """A table cell for the texts of one row: the text itself for one, a list for several (as pyLODE writes them)."""
    if len(items) == 1:
        return items[0]
    listed = "".join(f"                  <li>{item}</li>\n" for item in items)
    return "\n                <ul>\n" + listed + "                </ul>\n              "


def separate_definitions(page):
    """The page with each marked *Description* split into a *Definition* row (the ``skos:definition``) and a *Comment* row
    (the rest), and the marks removed; a *Description* with no mark, and a page already split, are unchanged (#273)."""
    def split(match):
        content = match.group(1)
        if MARK not in content:
            return match.group(0)
        items = [m.strip() for m in _LIST_ITEM.findall(content)] or [content.strip()]
        definitions = [i for i in items if MARK in i]
        comments = [i for i in items if MARK not in i]
        rows = _ROW.format(href="http://www.w3.org/2004/02/skos/core#definition", label="Definition", cell=_cell(definitions),
                           title="A statement or formal explanation of the meaning of a concept. Defined in SKOS")
        if comments:
            rows += "\n            " + _ROW.format(
                href="http://www.w3.org/2000/01/rdf-schema#comment", label="Comment", cell=_cell(comments),
                title="A description of the subject resource. Defined in RDF Schema")
        return rows

    return _DESCRIPTION_ROW.sub(split, page).replace(MARK, "")


def links(module, version=None):
    """(TTL source, documentation) addresses at ``w3id.org/adiro``, for the latest page or for an earlier release."""
    if version:
        return f"{SITE}/{module}/{version}/{module}.ttl", f"{SITE}/ontologies/{module}/{version}/"
    return f"{SITE}/{module}.ttl", f"{SITE}/ontologies/{module}/"


def add_links(page, module, version=None):
    """The page with a TTL source row and a documentation row after the IRI row; unchanged if they are there already."""
    section = SECTION.search(page)
    if not section or "<strong>TTL source</strong>" in section.group(1):
        return page
    ttl, docs = links(module, version)
    rows = ROW.format(label="TTL source", url=ttl) + "          " + ROW.format(label="Documentation", url=docs)
    found = IRI_ROW.search(page, section.start(1))
    if not found:
        return page
    return page[:found.end()] + "          " + rows + page[found.end():]


def replacements(ttl_file):
    """None when the module is not deprecated; else the names of the modules that replace it (``dcterms:isReplacedBy``).

    A deprecated module says ``owl:deprecated true`` on its ``owl:Ontology`` (#171).
    """
    graph = Graph().parse(str(ttl_file), format="turtle")
    for ontology in graph.subjects(RDF.type, OWL.Ontology):
        if any(str(v).lower() == "true" for v in graph.objects(ontology, OWL.deprecated)):
            return sorted(str(o).rstrip("/").rsplit("/", 1)[-1] for o in graph.objects(ontology, DCTERMS.isReplacedBy))
    return None


def add_deprecation(page, ttl_file):
    """The page with a "Deprecated" row after the IRI row when the module is deprecated (pyLODE shows neither
    ``owl:deprecated`` nor ``dcterms:isReplacedBy`` on the ontology); unchanged otherwise or if the row is there already.

    The replacement is named, not linked: it may not be published yet when the deprecated release is.
    """
    names = replacements(ttl_file)
    section = SECTION.search(page)
    if names is None or not section or "<strong>Deprecated</strong>" in section.group(1):
        return page
    found = IRI_ROW.search(page, section.start(1))
    if not found:
        return page
    by = ", ".join(f"<code>{htmllib.escape(n)}</code>" for n in names)
    text = f"Yes. Replaced by {by}, which continues its version numbering." if names else "Yes."
    return page[:found.end()] + "          " + TEXT_ROW.format(label="Deprecated", text=text) + page[found.end():]


def shown(page):
    """(IRI row, heading) of the Metadata block, as text; None for what is not there."""
    section = SECTION.search(page)
    if not section:
        return None, None
    iri = IRI_ROW.search(section.group(1))
    heading = HEADING.search(section.group(1))
    text = lambda s: htmllib.unescape(re.sub(r"<[^>]+>", "", s)).strip()
    return (text(iri.group(2)) if iri else None), (text(heading.group(1)) if heading else None)


def expected(ttl_file):
    """(IRI, title) of the module's single ``owl:Ontology``."""
    graph = Graph().parse(str(ttl_file), format="turtle")
    ontologies = list(graph.subjects(RDF.type, OWL.Ontology))
    if len(ontologies) != 1:
        return None, None
    ontology = ontologies[0]
    title = graph.value(ontology, DCTERMS.title) or graph.value(ontology, RDFS.label)
    return str(ontology), str(title) if title else None


def check(page, ttl_file):
    """Problems of a generated page against its Turtle (an empty list when it is right)."""
    iri, title = expected(ttl_file)
    shown_iri, shown_heading = shown(page)
    problems = []
    if shown_iri is None and shown_heading is None:
        return ["no Metadata block"]
    if shown_iri != iri:
        problems.append(f"the IRI row is {shown_iri!r}, not the ontology's {iri!r}")
    if shown_heading != title:
        problems.append(f"the heading is {shown_heading!r}, not the ontology's title {title!r}")
    if page.count("DefinedTermSet") != 1:
        problems.append(f"{page.count('DefinedTermSet')} schema.org blocks, not one")
    return problems


def module_and_version(ttl_file, output_dir):
    """The module of a Turtle file and, for an earlier release's page (``<module>/<semver>/``), its version."""
    module = Path(ttl_file).stem
    out = Path(output_dir)
    if re.fullmatch(r"\d+\.\d+\.\d+", out.name) and out.parent.name == module:
        return module, out.name
    return module, None
