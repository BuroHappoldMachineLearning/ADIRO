#!/usr/bin/env python3
"""
The module rename map (#171): which module replaces which, read by the release and documentation tooling.

``config/module_renames.json`` lists each rename as ``{"from": <old module>, "to": <new module>, "reason": ...}``.
A rename keeps one version history across the two names: the new module's first release is the old module's
last release plus a MAJOR bump, and its earlier versions are the old module's releases, which keep their own
names, IRIs, tags, snapshots and pages. So the tooling follows a module's *lineage* (the module, then the module
it replaced, and so on):

- the compatibility check (compat_diff.py) takes the predecessor's last release as the baseline when the module
  has none of its own, and compares it with the old IRIs mapped to the new ones, so a rename is one
  ``MODULE_RENAMED`` change (a MAJOR) and not a wall of removed and added terms;
- the release cut (prepare_release.py) and the checks of ``owl:priorVersion`` (validate_ontology.py,
  check_prior_versions.py) accept and require the predecessor's releases in the chain;
- the release notes, the version dropdown of the documentation pages and the badges show the one history.

A module may be renamed only once at a time (one ``from`` per ``to`` and one ``to`` per ``from``), and the map
has no cycle. stdlib + rdflib (for ``rewrite_graph`` only).
"""
import json
import re
from pathlib import Path

RENAMES_FILE = Path("config") / "module_renames.json"
BASE = "https://w3id.org/adiro/"
NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
VERSION_RE = re.compile(r"^/\d+\.\d+\.\d+(?:$|/)")  # a version IRI of a release, or a file under it
TEXT_VERSION_RE = re.compile(r"/\d+\.\d+\.\d+(?![\w.])")  # the same, found in running text


def load(root):
    """``{new module: old module}`` from config/module_renames.json; {} if the file is absent.

    Raises ValueError for a malformed map: a bad name, a module renamed twice, two modules renamed to one, or a cycle.
    """
    path = Path(root) / RENAMES_FILE
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8") or "{}")
    entries = data.get("renames", [])
    problems, renames, sources = [], {}, set()
    for entry in entries:
        old, new = entry.get("from", ""), entry.get("to", "")
        if not (NAME_RE.match(old) and NAME_RE.match(new)) or old == new:
            problems.append(f"{entry!r}: 'from' and 'to' must be two different module names")
            continue
        if new in renames:
            problems.append(f"{new!r} is the new name of two modules")
        if old in sources:
            problems.append(f"{old!r} is renamed twice")
        renames[new] = old
        sources.add(old)
    for start in renames:  # a cycle would make a lineage endless
        seen, module = {start}, renames.get(start)
        while module is not None:
            if module in seen:
                problems.append(f"the renames of {start!r} form a cycle")
                break
            seen.add(module)
            module = renames.get(module)
    if problems:
        raise ValueError(f"{RENAMES_FILE}: " + "; ".join(sorted(set(problems))))
    return renames


def predecessor(renames, module):
    """The module that `module` replaced, or None."""
    return renames.get(module)


def successor(renames, module):
    """The module that replaced `module`, or None."""
    return next((new for new, old in renames.items() if old == module), None)


def lineage(renames, module):
    """``[module, the module it replaced, the one before, ...]``: one version history, newest name first."""
    out = [module]
    while (module := renames.get(module)) is not None:
        out.append(module)
    return out


def names(renames, module):
    """Every name of `module`'s history, whichever end it is given by: the lineage, then the modules that replaced it."""
    out = lineage(renames, module)
    while (later := successor(renames, out[0])) is not None and later not in out:
        out.insert(0, later)
    return out


def superseded(renames, modules):
    """The modules among `modules` whose successor is among them too: a renamed module's predecessor kept for its last cycle."""
    present = set(modules)
    return {m for m in present if successor(renames, m) in present}


def iri_map(renames):
    """``{old ontology IRI: new ontology IRI}`` for every rename in the map."""
    return {f"{BASE}{old}": f"{BASE}{new}" for new, old in renames.items()}


def rename_iri(iri, renames):
    """`iri` with a renamed module's ontology IRI or term namespace mapped to the new module's.

    The ontology IRI (``…/adiro/<old>``), its terms (``…/adiro/<old>#Term``) and the files published under it (its
    example images, ``…/adiro/<old>/exampleImage/…``) are mapped, through every later rename. A version IRI
    (``…/adiro/<old>/<x.y.z>``, and what is under it) and any other address are left alone: an earlier release keeps
    its own IRI, and ``owl:priorVersion`` names it as it is.
    """
    mapping = iri_map(renames)
    for _ in range(len(mapping) + 1):  # follow a chain of renames
        for old, new in mapping.items():
            rest = iri[len(old):] if iri.startswith(old) else None
            if rest is not None and (rest == "" or rest.startswith("#")
                                     or (rest.startswith("/") and not VERSION_RE.match(rest))):
                iri = new + rest
                break
        else:
            return iri
    return iri


def rewrite_text(text, renames):
    """`text` with every address of a renamed module mapped (see rename_iri), wherever it appears: an IRI in Turtle, a link
    in a list, a value in JSON. A version IRI of an old release, and anything under it, keeps naming that release."""
    if not renames:
        return text
    old = "|".join(re.escape(n) for n in sorted(renames.values(), key=len, reverse=True))
    # a module name ends at a delimiter: `…/aec_geometry` is a module, `…/aec_geometry_x` is not
    pattern = re.compile(r"%s(%s)(?![\w-])" % (re.escape(BASE), old))

    def swap(match):
        if TEXT_VERSION_RE.match(match.string, match.end()):  # `…/aec_x/1.0.0`: the old release, kept
            return match.group(0)
        return rename_iri(match.group(0), renames)

    return pattern.sub(swap, text)


def rewrite_graph(graph, renames):
    """A copy of `graph` with every renamed module's IRIs mapped to the new names (see rename_iri)."""
    from rdflib import Graph, URIRef

    out = Graph()
    for prefix, namespace in graph.namespaces():
        out.bind(prefix, URIRef(rename_iri(str(namespace).rstrip("#"), renames) + ("#" if str(namespace).endswith("#") else "")),
                 override=True, replace=True)

    def term(node):
        return URIRef(rename_iri(str(node), renames)) if isinstance(node, URIRef) else node

    for s, p, o in graph:
        out.add((term(s), term(p), term(o)))
    return out
