#!/usr/bin/env python3
"""
Compatibility-diff classifier (RES-67, Phase 2a - warn mode).

For each ADIRO module, compare the working ``src/<module>.ttl`` against that
module's last released snapshot ``versions/<module>/<max-semver>/<module>.ttl``,
classify the changes by compatibility severity (per
``docs/governance/compatibility-diff-algorithm-spec.md``), derive the REQUIRED
SemVer bump, and compare it to the DECLARED bump (``owl:versionInfo``).

Phase 2a scope (syntactic, warn): category deltas + severity + required-vs-declared
bump. Deferred to Phase 2b: entailment-based detection (RES-78), rename/move
similarity (RES-79), compatibility-graph autofix (RES-80), enforce mode (RES-81).

Warn mode: this is advisory. The script exits 0 unless ``--enforce`` is given
(Phase 2b), in which case an insufficient/missing bump exits 1.
"""

import re
import sys
from pathlib import Path

from rdflib import BNode, Graph, URIRef
from rdflib.namespace import OWL, RDF, RDFS

SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")

# --- severity (spec Step 5) ---------------------------------------------------
NON_BREAKING = "non-breaking"
POTENTIALLY = "potentially-breaking"
BREAKING = "breaking"
SEVERITY_RANK = {NON_BREAKING: 1, POTENTIALLY: 2, BREAKING: 3}

DELTA_SEVERITY = {
    "TERM_ADDED": NON_BREAKING,
    "ANNOTATION_CHANGED": NON_BREAKING,
    "RESTRICTION_LOOSENED": NON_BREAKING,
    "RESTRICTION_REMOVED": NON_BREAKING,  # a removed constraint is a loosening
    "DOMAIN_CHANGED": POTENTIALLY,
    "RANGE_CHANGED": POTENTIALLY,
    "SUPERCLASS_CHANGED": POTENTIALLY,
    "RESTRICTION_ADDED": POTENTIALLY,
    "RESTRICTION_TIGHTENED": POTENTIALLY,
    "TERM_REMOVED": BREAKING,
    "TYPE_CHANGED": BREAKING,
    "SUPERPROPERTY_CHANGED": BREAKING,
}

# --- SemVer bump levels -------------------------------------------------------
BUMP_NONE, BUMP_PATCH, BUMP_MINOR, BUMP_MAJOR = "none", "patch", "minor", "major"
BUMP_RANK = {BUMP_NONE: 0, BUMP_PATCH: 1, BUMP_MINOR: 2, BUMP_MAJOR: 3}

# Deltas that are a semantic (non-annotation) change and so warrant at least MINOR.
_MINOR_DELTAS = {"TERM_ADDED", "RESTRICTION_LOOSENED", "RESTRICTION_REMOVED"}

_PROP_KINDS = {"object-property", "datatype-property", "annotation-property"}
_CARD = {
    OWL.cardinality: ("exact", 1),
    OWL.qualifiedCardinality: ("exact", 1),
    OWL.minCardinality: ("min", 1),
    OWL.minQualifiedCardinality: ("min", 1),
    OWL.maxCardinality: ("max", 1),
    OWL.maxQualifiedCardinality: ("max", 1),
}


def kind_of(graph, term):
    types = set(graph.objects(term, RDF.type))
    if OWL.Class in types:
        return "class"
    if OWL.ObjectProperty in types:
        return "object-property"
    if OWL.DatatypeProperty in types:
        return "datatype-property"
    if OWL.AnnotationProperty in types:
        return "annotation-property"
    if OWL.NamedIndividual in types:
        return "individual"
    return None


def _restrictions(graph, cls):
    """Normalized restriction descriptors on a class (bnode-independent)."""
    out = set()
    for r in graph.objects(cls, RDFS.subClassOf):
        if not isinstance(r, BNode) or (r, RDF.type, OWL.Restriction) not in graph:
            continue
        on_prop = graph.value(r, OWL.onProperty)
        on_cls = graph.value(r, OWL.onClass) or graph.value(r, OWL.onDataRange)
        for pred, obj in graph.predicate_objects(r):
            if pred in _CARD:
                family = _CARD[pred][0]
                out.add((str(on_prop), family, str(on_cls), "card", str(obj)))
            elif pred in (OWL.someValuesFrom, OWL.allValuesFrom, OWL.hasValue):
                out.add((str(on_prop), str(pred), None, "val", str(obj)))
    return out


def build_symbols(graph):
    """IRI -> descriptor for every named class/property/individual in the file."""
    symbols = {}
    for term in set(graph.subjects()):
        if not isinstance(term, URIRef):
            continue
        kind = kind_of(graph, term)
        if kind is None:
            continue
        desc = {
            "kind": kind,
            "labels": frozenset(str(o) for o in graph.objects(term, RDFS.label)),
            "comments": frozenset(str(o) for o in graph.objects(term, RDFS.comment)),
            "supers": frozenset(
                str(o)
                for pred in (RDFS.subClassOf, RDFS.subPropertyOf)
                for o in graph.objects(term, pred)
                if isinstance(o, URIRef)
            ),
            "domain": frozenset(str(o) for o in graph.objects(term, RDFS.domain) if isinstance(o, URIRef)),
            "range": frozenset(str(o) for o in graph.objects(term, RDFS.range) if isinstance(o, URIRef)),
            "restrictions": _restrictions(graph, term) if kind == "class" else frozenset(),
        }
        symbols[str(term)] = desc
    return symbols


def _diff_restrictions(old, new):
    """Yield restriction delta types for one class's old/new restriction sets."""
    added = new - old
    removed = old - new
    # Match cardinality changes on the same (onProperty, family, onClass) to
    # classify tighten/loosen rather than a raw add+remove.
    def card_index(s):
        idx = {}
        for t in s:
            if t[3] == "card":
                idx.setdefault((t[0], t[1], t[2]), t)
        return idx

    a_idx, r_idx = card_index(added), card_index(removed)
    for key in set(a_idx) & set(r_idx):
        _, family, _ = key
        old_v, new_v = int(r_idx[key][4]), int(a_idx[key][4])
        if old_v == new_v:
            continue
        if family == "min":
            yield "RESTRICTION_TIGHTENED" if new_v > old_v else "RESTRICTION_LOOSENED"
        elif family == "max":
            yield "RESTRICTION_TIGHTENED" if new_v < old_v else "RESTRICTION_LOOSENED"
        else:  # exact
            yield "RESTRICTION_TIGHTENED"
        added.discard(a_idx[key])
        removed.discard(r_idx[key])
    for _ in added:
        yield "RESTRICTION_ADDED"
    for _ in removed:
        yield "RESTRICTION_REMOVED"


def compute_deltas(old_syms, new_syms):
    """Return a list of (delta_type, term) records (exact-IRI matching only).

    Set differences/intersections are iterated in sorted(IRI) order so the
    emitted list is deterministic across runs (independent of PYTHONHASHSEED) —
    keeps CI logs diffable and guards against order-sensitive tests going flaky.
    """
    deltas = []
    for iri in sorted(old_syms.keys() - new_syms.keys()):
        deltas.append(("TERM_REMOVED", iri))
    for iri in sorted(new_syms.keys() - old_syms.keys()):
        deltas.append(("TERM_ADDED", iri))
    for iri in sorted(old_syms.keys() & new_syms.keys()):
        o, n = old_syms[iri], new_syms[iri]
        if o["kind"] != n["kind"]:
            deltas.append(("TYPE_CHANGED", iri))
            continue
        if o["kind"] in _PROP_KINDS:
            if o["domain"] != n["domain"]:
                deltas.append(("DOMAIN_CHANGED", iri))
            if o["range"] != n["range"]:
                deltas.append(("RANGE_CHANGED", iri))
            if o["supers"] != n["supers"]:
                deltas.append(("SUPERPROPERTY_CHANGED", iri))
        elif o["kind"] == "class":
            if o["supers"] != n["supers"]:
                deltas.append(("SUPERCLASS_CHANGED", iri))
            for dt in _diff_restrictions(o["restrictions"], n["restrictions"]):
                deltas.append((dt, iri))
        if (o["labels"], o["comments"]) != (n["labels"], n["comments"]):
            deltas.append(("ANNOTATION_CHANGED", iri))
    return deltas


def required_bump(deltas):
    sevs = {DELTA_SEVERITY[d] for d, _ in deltas}
    types = {d for d, _ in deltas}
    if BREAKING in sevs or POTENTIALLY in sevs:
        return BUMP_MAJOR
    if types & _MINOR_DELTAS:
        return BUMP_MINOR
    if "ANNOTATION_CHANGED" in types:
        return BUMP_PATCH
    return BUMP_NONE


def version_of(graph):
    ont = next(graph.subjects(RDF.type, OWL.Ontology), None)
    if ont is None:
        return None
    v = graph.value(ont, OWL.versionInfo)
    return str(v).strip() if v is not None else None


def declared_bump(old_v, new_v):
    mo, mn = SEMVER_RE.match(old_v or ""), SEMVER_RE.match(new_v or "")
    if not mo or not mn:
        return None  # non-SemVer; can't compare
    o = tuple(int(x) for x in mo.groups())
    n = tuple(int(x) for x in mn.groups())
    if n < o:
        return "decreased"
    if n[0] > o[0]:
        return BUMP_MAJOR
    if n[1] > o[1]:
        return BUMP_MINOR
    if n[2] > o[2]:
        return BUMP_PATCH
    return BUMP_NONE


def latest_snapshot(repo_root, module):
    base = repo_root / "versions" / module
    if not base.is_dir():
        return None
    versions = []
    for d in base.iterdir():
        m = SEMVER_RE.match(d.name)
        if d.is_dir() and m and (d / f"{module}.ttl").is_file():
            versions.append((tuple(int(x) for x in m.groups()), d / f"{module}.ttl"))
    if not versions:
        return None
    return max(versions, key=lambda t: t[0])[1]


def analyze_module(repo_root, module):
    new_file = repo_root / "src" / f"{module}.ttl"
    old_file = latest_snapshot(repo_root, module)
    if old_file is None:
        return {"module": module, "status": "no-baseline"}

    old_g, new_g = Graph(), Graph()
    old_g.parse(str(old_file), format="turtle")
    new_g.parse(str(new_file), format="turtle")

    deltas = compute_deltas(build_symbols(old_g), build_symbols(new_g))
    req = required_bump(deltas)
    old_v, new_v = version_of(old_g), version_of(new_g)
    decl = declared_bump(old_v, new_v)

    if decl == "decreased":
        verdict = "VERSION_DECREASED"
    elif req == BUMP_NONE:
        verdict = "OK"
    elif decl is None:
        verdict = "UNKNOWN_VERSION"
    elif BUMP_RANK.get(decl, 0) >= BUMP_RANK[req]:
        verdict = "OK"
    else:
        verdict = "INSUFFICIENT_BUMP"

    return {
        "module": module,
        "status": "analyzed",
        "old_version": old_v,
        "new_version": new_v,
        "required_bump": req,
        "declared_bump": decl,
        "verdict": verdict,
        "deltas": deltas,
    }


def print_report(result):
    m = result["module"]
    if result["status"] == "no-baseline":
        print(f"  [SKIP] {m}: no released snapshot under versions/{m}/ to diff against")
        return
    deltas = result["deltas"]
    by_sev = {}
    for d, iri in deltas:
        by_sev.setdefault(DELTA_SEVERITY[d], []).append((d, iri))
    print(
        f"  {m}: {result['old_version']} -> {result['new_version']} | "
        f"required bump: {result['required_bump'].upper()} | "
        f"declared: {(result['declared_bump'] or 'n/a')} | {result['verdict']}"
    )
    for sev in (BREAKING, POTENTIALLY, NON_BREAKING):
        for d, iri in by_sev.get(sev, []):
            local = iri.rsplit("/", 1)[-1].rsplit("#", 1)[-1]
            print(f"      - [{sev}] {d}: {local}")


def main():
    repo_root = Path(__file__).parent.parent
    enforce = "--enforce" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    modules = args or sorted(p.stem for p in (repo_root / "src").glob("*.ttl"))

    print("Compatibility diff (warn mode) - src/ vs last released snapshot:")
    problems = 0
    for module in modules:
        result = analyze_module(repo_root, module)
        print_report(result)
        if result.get("verdict") in ("INSUFFICIENT_BUMP", "VERSION_DECREASED"):
            problems += 1

    if problems:
        msg = (
            f"{problems} module(s) need attention: the declared version bump is "
            f"smaller than the change requires."
        )
        if enforce:
            print(f"\n[ERROR] {msg}", file=sys.stderr)
            sys.exit(1)
        print(f"\n[WARN] {msg} (advisory - warn mode)")
    else:
        print("\n[OK] All modules' declared version bumps are consistent with their changes.")


if __name__ == "__main__":
    main()
