#!/usr/bin/env python3
"""
Validate ADIRO data against the data-validation shapes (#168).

The ontology (`src/`) says what exists; the files in `data-validation/` (SHACL, `*.shacl.ttl`) say what a complete,
well-formed DATASET must contain: the closed-world conditions that OWL cannot state (see docs/contribute/data-validation.md).
This script checks one or more RDF files, the individuals an extraction pipeline produced, against them.

    uv run --with pyshacl python scripts/validate_data.py DATA.ttl [DATA2.ttl ...]
    uv run --with pyshacl python scripts/validate_data.py --public-hosts HOSTS.txt DATA.ttl   # a public release

With --public-hosts, the release shapes in `data-validation/release/` run as well: they check that every address a file
records (sourceLocation, sourcePage, storageLocation) is on a host of the allowlist, one host per line in HOSTS.txt (a
host also allows its subdomains; `#` starts a comment). The allowlist is supplied by whoever runs the release; it is
not part of the repository (#229).

Exit code 1 when a result has severity Violation; a Warning or an Info is reported and never fails the run.
The ontology modules are read as background, so that a subclass counts as its superclass (a standalone reference
is a drawing identifier mention).
"""
import sys
from pathlib import Path

from rdflib import BNode, Graph, Literal, Namespace
from rdflib.namespace import RDF

ROOT = Path(__file__).resolve().parent.parent
SH = Namespace("http://www.w3.org/ns/shacl#")
SHAPES_DIR = "data-validation"
SHAPES_GLOB = "*.shacl.ttl"
RELEASE_DIR = "data-validation/release"
RELEASE = Namespace("https://w3id.org/adiro/data-validation/release#")


def shape_files(root=ROOT, release=False):
    files = sorted((Path(root) / SHAPES_DIR).glob(SHAPES_GLOB))
    if release:
        files += sorted((Path(root) / RELEASE_DIR).glob(SHAPES_GLOB))
    return files


def load_shapes(root=ROOT, release=False):
    graph = Graph()
    for path in shape_files(root, release):
        graph.parse(str(path), format="turtle")
    return graph


def read_public_hosts(path):
    """The allowlist of public hosts: one per line, lower-cased; blank lines and `#` comments are skipped."""
    hosts = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        host = line.split("#", 1)[0].strip().lower()
        if host:
            hosts.append(host)
    return hosts


def with_public_hosts(data, hosts):
    """A copy of the data graph with the allowlist added as data, which the release shapes query."""
    graph = Graph()
    for triple in data:
        graph.add(triple)
    for host in hosts:
        node = BNode()
        graph.add((node, RDF.type, RELEASE.PublicHost))
        graph.add((node, RELEASE.host, Literal(host)))
    return graph


def load_ontology(root=ROOT):
    """All ontology modules, merged: the background that gives subclasses to the shapes' classes."""
    graph = Graph()
    for path in sorted((Path(root) / "src").glob("*.ttl")):
        graph.parse(str(path), format="turtle")
    return graph


def validate(data, root=ROOT, public_hosts=None):
    """Check an rdflib Graph; return a list of {severity, focus, path, message, shape} dicts, most severe first.

    public_hosts, a list of hosts, runs the release shapes as well, with that allowlist (None: not a release)."""
    from pyshacl import validate as shacl_validate  # a dependency of this script only

    release = public_hosts is not None
    if release:
        data = with_public_hosts(data, public_hosts)
    _, results, _ = shacl_validate(data, shacl_graph=load_shapes(root, release), ont_graph=load_ontology(root),
                                   inference="none")
    found = []
    for result in results.subjects(RDF.type, SH.ValidationResult):
        severity = results.value(result, SH.resultSeverity)
        found.append({
            "severity": str(severity).rsplit("#", 1)[-1] if severity else "Violation",
            "focus": str(results.value(result, SH.focusNode)),
            "path": str(results.value(result, SH.resultPath) or ""),
            "message": str(results.value(result, SH.resultMessage) or ""),
            "shape": str(results.value(result, SH.sourceShape) or ""),
        })
    rank = {"Violation": 0, "Warning": 1, "Info": 2}
    return sorted(found, key=lambda r: (rank.get(r["severity"], 3), r["focus"], r["message"]))


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    public_hosts = None
    if "--public-hosts" in argv:
        at = argv.index("--public-hosts")
        if at + 1 >= len(argv):
            print("--public-hosts needs a file")
            return 2
        public_hosts = read_public_hosts(argv[at + 1])
        del argv[at:at + 2]
    files = [a for a in argv if not a.startswith("-")]
    if not files:
        print(__doc__.strip().splitlines()[0])
        print("usage: validate_data.py [--public-hosts HOSTS.txt] DATA.ttl [DATA2.ttl ...]")
        return 2
    data = Graph()
    for name in files:
        data.parse(name)
    results = validate(data, public_hosts=public_hosts)
    for r in results:
        print(f"[{r['severity']}] {r['focus']}: {r['message']}")
    violations = sum(1 for r in results if r["severity"] == "Violation")
    print(f"{len(results)} result(s), {violations} violation(s) ({len(shape_files(release=public_hosts is not None))} shape file(s)).")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
