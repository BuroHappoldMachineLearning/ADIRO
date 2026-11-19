#!/usr/bin/env python3
"""
Split a term's ``rdfs:comment`` into a ``skos:definition`` and the commentary that remains (#273).

A term's definition is a ``skos:definition`` and ``rdfs:comment`` is kept for commentary. Which part of an existing comment
is the definition is an editorial choice, so it is made by hand, in a JSON file that maps a term's local name to the text of
its definition; this script only carries it out, so that nothing is retyped and nothing is lost:

* the definition text must be the **start** of the term's comment, word for word;
* what follows it (if anything) stays in ``rdfs:comment`` as the commentary; a comment that is only a definition moves whole
  and the term keeps no ``rdfs:comment``;
* the rest of the file is untouched (the layout, the line endings, every other triple), and the script re-reads the result
  and refuses to write it unless exactly the comment triples of the mapped terms changed.

Usage:
    uv run python scripts/split_definitions.py src/adiro_geometry.ttl map.json          # rewrite the file
    uv run python scripts/split_definitions.py src/adiro_geometry.ttl map.json --check  # report only
    uv run python scripts/split_definitions.py src/adiro_geometry.ttl --list            # terms with no skos:definition

``map.json`` is ``{"BoundingBox": "A rectangular region on a drawing page ...", ...}``. A term of another namespace (a typing
stub such as a GeoSPARQL class) is not ADIRO's to define and is refused.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from rdflib import Graph, URIRef
from rdflib.namespace import OWL, RDF, RDFS, SKOS

SKOS_PREFIX = "@prefix skos: <http://www.w3.org/2004/02/skos/core#> ."
_STRING = r'"(?:[^"\\]|\\.)*"(?:@[A-Za-z][A-Za-z0-9-]*|\^\^[^\s;,.]+)?'
_TERM_TYPES = (OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty, OWL.NamedIndividual)


class SplitError(Exception):
    """The mapping cannot be applied to the file, said in a sentence."""


def encode(text: str) -> str:
    """A Turtle string literal for the text, with the escapes the modules already use."""
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def module_namespace(graph: Graph) -> str:
    ontology = next((str(s) for s in graph.subjects(RDF.type, OWL.Ontology)), None)
    if not ontology:
        raise SplitError("the file declares no owl:Ontology")
    return ontology + "#"


def terms_without_definition(graph: Graph) -> list[str]:
    """Local names of the module's own terms that have an rdfs:comment and no skos:definition."""
    namespace = module_namespace(graph)
    found = set()
    for term_type in _TERM_TYPES:
        for term in graph.subjects(RDF.type, term_type):
            if (isinstance(term, URIRef) and str(term).startswith(namespace) and (term, RDFS.comment, None) in graph
                    and (term, SKOS.definition, None) not in graph):
                found.add(str(term)[len(namespace):])
    return sorted(found)


def _block(text: str, name: str) -> tuple[int, int]:
    """The start and end offsets of the term's block: from its subject at the start of a line to the next blank line."""
    start = re.search(rf"(?m)^:{re.escape(name)}[ \t\r\n]", text)
    if not start:
        raise SplitError(f"{name}: no block starting with ':{name}' (only a term written with the default prefix is handled)")
    end = re.search(r"\n[ \t\r]*\n", text[start.start():])
    return start.start(), start.start() + end.start() if end else len(text)


def split_text(text: str, graph: Graph, mapping: dict[str, str]) -> str:
    """The Turtle text with each mapped term's comment split; ``graph`` is the parse of ``text``."""
    namespace = module_namespace(graph)
    for name, definition in mapping.items():
        iri = URIRef(namespace + name)
        if (iri, RDF.type, None) not in graph:
            raise SplitError(f"{name}: not a term of this module ({iri})")
        if (iri, SKOS.definition, None) in graph:
            raise SplitError(f"{name}: has a skos:definition already")
        comments = list(graph.objects(iri, RDFS.comment))
        if len(comments) != 1:
            raise SplitError(f"{name}: has {len(comments)} rdfs:comment values, expected exactly one")
        original = str(comments[0])
        if not original.startswith(definition):
            raise SplitError(f"{name}: the definition is not the start of the comment, word for word:\n  comment: {original[:90]}...")
        if not definition.strip():
            raise SplitError(f"{name}: the definition is empty")
        start, end = _block(text, name)
        block = text[start:end]
        found = re.search(rf"(?m)^([ \t]+)(rdfs:comment[ \t]+({_STRING}))", block)
        if not found:
            raise SplitError(f"{name}: could not find its rdfs:comment literal in the file")
        literal = next(Graph().parse(data=f"<a:a> <a:b> {found.group(3)} .", format="turtle").objects())
        if str(literal) != original:
            raise SplitError(f"{name}: the comment found in the file is not the term's comment")
        indent = found.group(1)
        rest = original[len(definition):].strip()
        new = f'skos:definition {encode(definition.strip())}@en'
        if rest:
            tag = f"@{literal.language}" if literal.language else ""
            new += f" ;\n{indent}rdfs:comment {encode(rest)}{tag}"
        text = text[:start + found.start(2)] + new + text[start + found.end(2):]
    return text


def with_skos_prefix(text: str) -> str:
    if re.search(r"(?m)^@prefix skos:", text):
        return text
    prefixes = list(re.finditer(r"(?m)^@prefix [^\n]*\n", text))
    if not prefixes:
        raise SplitError("the file has no @prefix lines to add skos: after")
    last = prefixes[-1]
    return text[:last.end()] + SKOS_PREFIX + "\n" + text[last.end():]


def check(before: Graph, after: Graph, mapping: dict[str, str]) -> None:
    """Exactly the comment triples of the mapped terms changed, and each comment is its definition plus its remainder."""
    namespace = module_namespace(before)
    removed, added = set(before) - set(after), set(after) - set(before)
    for s, p, o in removed:
        if not (p == RDFS.comment and str(s)[len(namespace):] in mapping):
            raise SplitError(f"unexpected triple removed: {s} {p} {o}")
    for s, p, o in added:
        if p not in (RDFS.comment, SKOS.definition) or str(s)[len(namespace):] not in mapping:
            raise SplitError(f"unexpected triple added: {s} {p} {o}")
    for name in mapping:
        iri = URIRef(namespace + name)
        original = str(next(o for s, p, o in removed if s == iri))
        definition = str(after.value(iri, SKOS.definition))
        rest = after.value(iri, RDFS.comment)
        if " ".join((definition + " " + (str(rest) if rest is not None else "")).split()) != " ".join(original.split()):
            raise SplitError(f"{name}: definition + comment does not give back the original comment")


def split_file(path: Path, mapping: dict[str, str], write: bool = True) -> list[str]:
    """Split the mapped terms of a module file; returns the names done. Nothing is written if any check fails."""
    raw = path.read_bytes().decode("utf-8")
    crlf = "\r\n" in raw
    text = raw.replace("\r\n", "\n")
    before = Graph().parse(data=text, format="turtle")
    new_text = with_skos_prefix(split_text(text, before, mapping))
    after = Graph().parse(data=new_text, format="turtle")
    check(before, after, mapping)
    if write:
        path.write_bytes((new_text.replace("\n", "\r\n") if crlf else new_text).encode("utf-8"))
    return sorted(mapping)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("ttl", type=Path)
    parser.add_argument("mapping", type=Path, nargs="?")
    parser.add_argument("--check", action="store_true", help="verify the mapping and report, without writing")
    parser.add_argument("--list", action="store_true", help="list the terms that have a comment and no skos:definition")
    args = parser.parse_args(argv)
    try:
        if args.list:
            graph = Graph().parse(str(args.ttl), format="turtle")
            for name in terms_without_definition(graph):
                print(name)
            return 0
        if not args.mapping:
            parser.error("a mapping file is needed unless --list is given")
        mapping = json.loads(args.mapping.read_text(encoding="utf-8"))
        done = split_file(args.ttl, mapping, write=not args.check)
    except (SplitError, OSError, ValueError) as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        return 1
    print(f"{'Checked' if args.check else 'Split'} {len(done)} term(s): {', '.join(done)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
