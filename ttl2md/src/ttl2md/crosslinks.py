"""Link the names of terms written in a definition to the terms' documentation.

A definition (``rdfs:comment``) is plain text that often names other terms: "each recorded as a FieldAssertion". This
module finds those names and turns each into a link, for any output format (the caller says how a link is written), so
a Markdown page and an HTML page link the same names in the same way.

A *target* is a name as it may be written (a term's local name, or its prefixed name such as ``prov:startedAtTime``)
mapped to the URL of the term's documentation; :func:`targets_for` builds them from a graph. :func:`link_names` then
rewrites a text. The rules, chosen so that ordinary words are not linked by mistake:

* A name is matched as a whole word, case-sensitively, optionally followed by a plural ``s``.
* A name with a capital letter inside it (``FieldAssertion``, ``hasStepKind``) or a prefix (``prov:Activity``) is
  always linked.
* A name that is a single capitalised word (``Layout``, ``Failed``) is linked unless it starts a sentence or stands
  next to another capitalised word (part of a phrase such as "Ground Floor Plan").
* A name that is a single all-lowercase word (``unit``, ``contains``) is never linked.
* Each target is linked once per text, at its first linkable mention, and the names in ``skip`` (the term being
  defined) are never linked.
* Nothing inside a URL, a code span, an HTML tag or an existing link (Markdown or HTML) is changed.
"""

from __future__ import annotations

import re
from typing import Callable, Iterable, Mapping

from rdflib import Graph, URIRef

__all__ = ["link_names", "targets_for", "markdown_link", "html_link", "prefixed_name"]

# Spans that are never rewritten: an HTML link with its text, any other HTML tag, a Markdown link, a code span, a URL.
_PROTECTED = re.compile(
    r"<a\b[^>]*>.*?</a>|<[^>]+>|\[[^\]]*\]\([^)]*\)|`[^`]*`|\b[a-z][a-z0-9+.\-]*://[^\s<>\"')]+",
    re.IGNORECASE | re.DOTALL,
)
_SINGLE_WORD = re.compile(r"[A-Za-z][a-z0-9]*")
_SENTENCE_START = re.compile(r"(?:^|[.!?])\s*$")  # the text before a match ends a sentence (or is empty)
_CAPITALISED_BEFORE = re.compile(r"[A-Z][\w\-]*\s$")  # "Ground Floor| Plan"
_CAPITALISED_AFTER = re.compile(r"s?\s[A-Z]")  # "Detail| Markers"


def markdown_link(name: str, url: str) -> str:
    return f"[{name}]({url})"


def html_link(name: str, url: str) -> str:
    return f'<a href="{url}">{name}</a>'


def prefixed_name(graph: Graph, iri: str) -> str | None:
    """The term's prefixed name with one of ``graph``'s prefixes (``prov:Activity``), or None (no prefix, or the empty one)."""
    try:
        curie = graph.namespace_manager.normalizeUri(URIRef(iri))
    except Exception:
        return None
    if not curie or curie.startswith("<") or curie.startswith(":") or ":" not in curie:
        return None
    return curie


def _local(iri: str) -> str:
    return re.split(r"[#/]", iri.rstrip("#/"))[-1]


def targets_for(
    graph: Graph,
    own_namespace: str | None,
    on_page: Mapping[str, str],
    elsewhere: Mapping[str, str] = {},
) -> dict[str, str]:
    """The names to link, each mapped to its URL.

    ``on_page`` maps the IRI of each term documented on the page to its URL (an anchor); ``elsewhere`` maps the IRI of
    each term documented on another page to its URL. A term is linked by its local name when its IRI is in
    ``own_namespace`` (the page's ontology) or is documented elsewhere, and by its prefixed name always: a stub of an
    external vocabulary declared on the page (``prov:Activity``) is linked only when written with its prefix, so the
    ordinary word "Activity" is not. A term documented elsewhere links there even when the page declares a stub of it.
    A local name that two different targets share is not linked by that name.
    """
    urls: dict[str, str] = dict(on_page)
    urls.update(elsewhere)  # the term's own documentation wins over a stub on this page
    by_name: dict[str, set[str]] = {}
    for iri, url in urls.items():
        names = []
        own = bool(own_namespace) and iri.startswith(own_namespace) and iri[len(own_namespace):][:1] in ("#", "/")
        if own or iri in elsewhere:
            names.append(_local(iri))
        curie = prefixed_name(graph, iri)
        if curie:
            names.append(curie)
        for name in names:
            by_name.setdefault(name, set()).add(url)
    return {name: next(iter(found)) for name, found in by_name.items() if len(found) == 1}


def _linkable(name: str, text: str, start: int, end: int) -> bool:
    if ":" in name or not _SINGLE_WORD.fullmatch(name):
        return True  # a prefixed name, or one with a capital inside it
    if name[0].islower():
        return False  # an ordinary lowercase word
    before, after = text[:start], text[end:]
    return not (_SENTENCE_START.search(before) or _CAPITALISED_BEFORE.search(before) or _CAPITALISED_AFTER.match(after))


def link_names(
    text: str,
    targets: Mapping[str, str],
    render: Callable[[str, str], str] = markdown_link,
    skip: Iterable[str] = (),
) -> str:
    """``text`` with the first linkable mention of each target written as ``render(name, url)``."""
    skip = set(skip)
    names = [n for n in targets if n not in skip]
    if not text or not names:
        return text
    pattern = re.compile(
        r"(?<![\w:/#.\-])(" + "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True)) + r")(?=s?(?![\w\-]))"
    )
    protected = [m.span() for m in _PROTECTED.finditer(text)]
    out: list[str] = []
    done: set[str] = set()
    last = 0
    for match in pattern.finditer(text):
        name, (start, end) = match.group(1), match.span(1)
        if name in done or any(a < end and start < b for a, b in protected):
            continue
        if not _linkable(name, text, start, end):
            continue
        out += [text[last:start], render(name, targets[name])]
        last = end
        done.add(name)
    out.append(text[last:])
    return "".join(out)
