#!/usr/bin/env python3
"""
Compatibility-diff classifier (RES-67, Phase 2a - warn mode).

For each ADIRO module, compare the working ``src/<module>.ttl`` against that
module's last released snapshot ``versions/<module>/<max-semver>/<module>.ttl``,
classify the changes by compatibility severity (per
``docs/contribute/versioning/compatibility-diff-algorithm-spec.md``), derive the REQUIRED
SemVer bump, and compare it to the DECLARED bump (``owl:versionInfo``).

Phase 2a scope (syntactic, warn): category deltas + severity + required-vs-declared
bump. Deferred to Phase 2b: entailment-based detection (RES-78), rename/move
similarity (RES-79), compatibility-graph autofix (RES-80), enforce mode (RES-81).

Warn mode: this is advisory. The script exits 0 unless ``--enforce`` is given
(Phase 2b), in which case an insufficient/missing bump exits 1.
"""

import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

from rdflib import BNode, Graph, Literal, URIRef
from rdflib.namespace import OWL, RDF, RDFS, XSD

sys.path.insert(0, str(Path(__file__).resolve().parent))
import module_renames as mr  # noqa: E402

SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")

# --- severity (spec Step 5) ---------------------------------------------------
NON_BREAKING = "non-breaking"
POTENTIALLY = "potentially-breaking"
BREAKING = "breaking"
SEVERITY_RANK = {NON_BREAKING: 1, POTENTIALLY: 2, BREAKING: 3}

DELTA_SEVERITY = {
    "TERM_ADDED": NON_BREAKING,
    "ANNOTATION_CHANGED": NON_BREAKING,
    "ONTOLOGY_HEADER_CHANGED": NON_BREAKING,  # annotations on the owl:Ontology header (e.g. owl:priorVersion)
    "IMPORTS_CHANGED": NON_BREAKING,  # an owl:imports added or removed; term axioms are what MAJOR/MINOR measure
    "RESTRICTION_LOOSENED": NON_BREAKING,
    "RESTRICTION_REMOVED": NON_BREAKING,  # a removed constraint is a loosening
    "DOMAIN_CHANGED": POTENTIALLY,
    "LABELLING_CHANGED": POTENTIALLY,  # a boolean flag of the metadata module that drives the annotation tooling
    "RANGE_CHANGED": POTENTIALLY,
    "SUPERCLASS_CHANGED": POTENTIALLY,
    "RESTRICTION_ADDED": POTENTIALLY,
    "RESTRICTION_TIGHTENED": POTENTIALLY,
    "TERM_REMOVED": BREAKING,
    "TYPE_CHANGED": BREAKING,
    "SUPERPROPERTY_CHANGED": BREAKING,
    # A rename (config/module_renames.json, #171) changes every term IRI of the module: one MAJOR change. The terms
    # are compared with the old IRIs mapped to the new ones, so only what changed besides the name is listed with it.
    "MODULE_RENAMED": BREAKING,
    # A module that a renamed one replaced leaves src/: its releases stay published, so nothing changes for a consumer.
    "MODULE_RETIRED": NON_BREAKING,
}

# --- SemVer bump levels -------------------------------------------------------
BUMP_NONE, BUMP_PATCH, BUMP_MINOR, BUMP_MAJOR = "none", "patch", "minor", "major"
BUMP_RANK = {BUMP_NONE: 0, BUMP_PATCH: 1, BUMP_MINOR: 2, BUMP_MAJOR: 3}

# Deltas that are a semantic (non-annotation) change and so warrant at least MINOR.
_MINOR_DELTAS = {"TERM_ADDED", "RESTRICTION_LOOSENED", "RESTRICTION_REMOVED"}

# Boolean flags that the metadata module defines (isComputerVisionLabel, isComputerVisionOptionalLabel, ...) are read by the downstream annotation
# tooling to build its label set, so changing one on an existing term can break a consumer although no axiom changed.
_FLAG_NS = "https://w3id.org/adiro/aec_drawing_metadata#"

_PROP_KINDS = {"object-property", "datatype-property", "annotation-property"}

# Header predicates that are not annotations: the version is bumped by the release cut, rdf:type is the declaration,
# and owl:imports is compared separately (IMPORTS_CHANGED).
_HEADER_IGNORED = {OWL.versionIRI, OWL.versionInfo, OWL.imports, RDF.type}
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
            # the example images of a term (#145): documentation for consumers, so a change is annotation-only (PATCH)
            "images": frozenset(str(o) for p, o in graph.predicate_objects(term) if str(p).rsplit("#", 1)[-1] == "exampleImage"),
            "flags": frozenset(
                (str(p), str(o))
                for p, o in graph.predicate_objects(term)
                if str(p).startswith(_FLAG_NS) and isinstance(o, Literal) and o.datatype == XSD.boolean
            ),
        }
        symbols[str(term)] = desc
    # The owl:Ontology header: annotations on it (a reworded description, owl:priorVersion, ...) are invisible to the
    # per-term comparison above, so they are compared as one pseudo-symbol.
    for ont in graph.subjects(RDF.type, OWL.Ontology):
        if isinstance(ont, URIRef):
            symbols[str(ont)] = {
                "kind": "ontology",
                "header": frozenset(
                    (str(p), str(o))
                    for p, o in graph.predicate_objects(ont)
                    if p not in _HEADER_IGNORED and not isinstance(o, BNode)
                ),
                "imports": frozenset(str(o) for o in graph.objects(ont, OWL.imports)),
            }
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
        if old_syms[iri]["kind"] != "ontology":
            deltas.append(("TERM_REMOVED", iri))
    for iri in sorted(new_syms.keys() - old_syms.keys()):
        if new_syms[iri]["kind"] != "ontology":
            deltas.append(("TERM_ADDED", iri))
    for iri in sorted(old_syms.keys() & new_syms.keys()):
        o, n = old_syms[iri], new_syms[iri]
        if o["kind"] == "ontology" and n["kind"] == "ontology":
            if o["header"] != n["header"]:
                deltas.append(("ONTOLOGY_HEADER_CHANGED", iri))
            if o["imports"] != n["imports"]:
                deltas.append(("IMPORTS_CHANGED", iri))
            continue
        if o["kind"] != n["kind"]:
            deltas.append(("TYPE_CHANGED", iri))
            continue
        if o["kind"] == "annotation-property" and (o["domain"] != n["domain"] or o["range"] != n["range"]
                                                   or o["supers"] != n["supers"]):
            # An annotation property's domain, range and super-properties carry no logical meaning (no reasoner draws
            # anything from them), so changing one is documentation for consumers: an annotation change, not a breaking
            # one (#145; #157 for the link of exampleImage to foaf:depiction).
            deltas.append(("ANNOTATION_CHANGED", iri))
        if o["kind"] in _PROP_KINDS:
            if o["kind"] != "annotation-property" and o["domain"] != n["domain"]:
                deltas.append(("DOMAIN_CHANGED", iri))
            if o["kind"] != "annotation-property" and o["range"] != n["range"]:
                deltas.append(("RANGE_CHANGED", iri))
            if o["kind"] != "annotation-property" and o["supers"] != n["supers"]:
                deltas.append(("SUPERPROPERTY_CHANGED", iri))
        elif o["kind"] == "class":
            if o["supers"] != n["supers"]:
                deltas.append(("SUPERCLASS_CHANGED", iri))
            for dt in _diff_restrictions(o["restrictions"], n["restrictions"]):
                deltas.append((dt, iri))
        if o["flags"] != n["flags"]:
            deltas.append(("LABELLING_CHANGED", iri))
        if ((o["labels"], o["comments"], o["images"]) != (n["labels"], n["comments"], n["images"])
                and ("ANNOTATION_CHANGED", iri) not in deltas):  # one delta per term, whatever annotation changed
            deltas.append(("ANNOTATION_CHANGED", iri))
    return deltas


# --- what changed and where (#181) --------------------------------------------
# The annotations whose change ANNOTATION_CHANGED reports, and the regex that finds each one's predicate in the Turtle text.
_ANNOTATION_PREDICATE = {
    "rdfs:label": r"rdfs:label\b",
    "rdfs:comment": r"rdfs:comment\b",
    "exampleImage": r"(?:[\w-]*:|<[^>]*#)exampleImage\b",
    "rdfs:domain": r"rdfs:domain\b",
    "rdfs:range": r"rdfs:range\b",
    "rdfs:subPropertyOf": r"rdfs:subPropertyOf\b",
}
_REPO_RE = r"[\w-][\w.-]*/[\w-][\w.-]*"  # owner/name: no part may start with a dot (".." is not a repository)
_PREFIX_RE = re.compile(r"^\s*@prefix\s+([\w.-]*):\s*<([^>]*)>\s*\.", re.M | re.I)


def annotation_details(old_syms, new_syms):
    """IRI -> the annotations whose value changed, for the terms an ANNOTATION_CHANGED delta reports."""
    out = {}
    for iri in sorted(old_syms.keys() & new_syms.keys()):
        o, n = old_syms[iri], new_syms[iri]
        if o["kind"] != n["kind"] or o["kind"] == "ontology":
            continue
        pairs = [("labels", "rdfs:label"), ("comments", "rdfs:comment"), ("images", "exampleImage")]
        if o["kind"] == "annotation-property":
            pairs += [("domain", "rdfs:domain"), ("range", "rdfs:range"), ("supers", "rdfs:subPropertyOf")]
        names = [name for key, name in pairs if o[key] != n[key]]
        if names:
            out[iri] = names
    return out


def locate_lines(text, iri, names=()):
    """Where a term sits in Turtle text: (first line of the term, {annotation name: its line}), 1-based.

    The term is the subject at the start of a line (as a prefixed name or as <iri>); its block runs over the
    indented lines that follow. (None, {}) when it is not found. Reads the text only: it never fails a report.
    """
    lines = text.splitlines()
    tokens = ["<%s>" % iri]
    for prefix, ns in _PREFIX_RE.findall(text):
        if ns and iri.startswith(ns) and re.fullmatch(r"[\w.-]*", iri[len(ns):]):
            tokens.append("%s:%s" % (prefix, iri[len(ns):]))
    subject = re.compile(r"^(?:%s)(?=\s)" % "|".join(re.escape(t) for t in tokens))
    start = next((i for i, line in enumerate(lines) if subject.match(line)), None)
    if start is None:
        return None, {}
    end = start + 1
    while end < len(lines) and (not lines[end].strip() or lines[end][0].isspace()):
        end += 1
    found = {}
    for name in names:
        rx = re.compile(_ANNOTATION_PREDICATE[name])
        for i in range(start, end):
            if rx.search(lines[i]):
                found[name] = i + 1
                break
    return start + 1, found


def links_from_env(repo_root, base_dir=None):
    """The context for line links, or None.

    COMPAT_LINK_REPO (owner/name of the head) and COMPAT_LINK_SHA (a full commit) give the file links. With
    COMPAT_LINK_PR (the pull request number) and COMPAT_LINK_BASE_REPO (owner/name of the repository the pull request
    is in; the head's when absent) each change also links to its line in the PR diff (#183). ``base_dir`` holds the
    base branch's files, for the line of a removed term.
    """
    repo, sha = os.environ.get("COMPAT_LINK_REPO", ""), os.environ.get("COMPAT_LINK_SHA", "")
    if not (re.fullmatch(_REPO_RE, repo) and re.fullmatch(r"[0-9a-f]{40}", sha)):
        return None
    pr = os.environ.get("COMPAT_LINK_PR", "")
    base_repo = os.environ.get("COMPAT_LINK_BASE_REPO", "") or repo
    if not (re.fullmatch(r"[1-9][0-9]{0,8}", pr) and re.fullmatch(_REPO_RE, base_repo)):
        pr, base_repo = "", repo

    def read(module):
        # The text at the linked commit, so a line number is the one the link opens; the working tree is the fallback.
        try:
            done = subprocess.run(["git", "show", f"{sha}:src/{module}.ttl"], cwd=repo_root, capture_output=True, check=True)
            return done.stdout.decode("utf-8")
        except Exception:
            return (Path(repo_root) / "src" / f"{module}.ttl").read_text(encoding="utf-8")

    def read_base(module):
        return (Path(base_dir) / f"{module}.ttl").read_text(encoding="utf-8")

    return {"repo": repo, "sha": sha, "read": read, "pr": pr, "base_repo": base_repo,
            "read_base": read_base if base_dir else None}


def required_bump(deltas):
    sevs = {DELTA_SEVERITY[d] for d, _ in deltas}
    types = {d for d, _ in deltas}
    if BREAKING in sevs or POTENTIALLY in sevs:
        return BUMP_MAJOR
    if types & _MINOR_DELTAS:
        return BUMP_MINOR
    if types & {"ANNOTATION_CHANGED", "ONTOLOGY_HEADER_CHANGED", "IMPORTS_CHANGED"}:
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


def apply_bump(version, bump):
    """Return the version that results from applying ``bump`` to ``version``.

    e.g. apply_bump("2.0.0", "major") -> "3.0.0"; minor -> "2.1.0"; patch ->
    "2.0.1"; none -> unchanged. Returns None for a non-SemVer input.
    """
    m = SEMVER_RE.match(version or "")
    if not m:
        return None
    x, y, z = (int(v) for v in m.groups())
    if bump == BUMP_MAJOR:
        return f"{x + 1}.0.0"
    if bump == BUMP_MINOR:
        return f"{x}.{y + 1}.0"
    if bump == BUMP_PATCH:
        return f"{x}.{y}.{z + 1}"
    return f"{x}.{y}.{z}"


def latest_snapshot(repo_root, module):
    base = Path(repo_root) / "versions" / module
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


def baseline(repo_root, module, renames=None):
    """(module, snapshot) of the release to compare `module` with, or (None, None).

    The module's own last release; for a renamed module that has none yet, the last release of the module it replaced
    (config/module_renames.json, #171), so the new name continues the old one's numbering.
    """
    renames = mr.load(repo_root) if renames is None else renames
    for name in mr.lineage(renames, module):
        snapshot = latest_snapshot(repo_root, name)
        if snapshot is not None:
            return name, snapshot
    return None, None


def analyze_module(repo_root, module):
    repo_root = Path(repo_root)
    renames = mr.load(repo_root)
    new_file = repo_root / "src" / f"{module}.ttl"
    base_module, old_file = baseline(repo_root, module, renames)
    if old_file is None:
        return {"module": module, "status": "no-baseline"}

    old_g, new_g = Graph(), Graph()
    old_g.parse(str(old_file), format="turtle")
    renamed = base_module != module
    if renamed:  # compare under the new names, so the rename is one change and the rest is what really changed
        old_g = mr.rewrite_graph(old_g, renames)
    removed = not new_file.is_file()  # the module was deleted or renamed: every released term is gone
    if not removed:
        new_g.parse(str(new_file), format="turtle")
    replaced_by = mr.successor(renames, module) if removed else None
    retired = bool(replaced_by) and (repo_root / "src" / f"{replaced_by}.ttl").is_file()

    if retired:  # its successor carries the history on; the old releases stay published
        deltas = [("MODULE_RETIRED", mr.BASE + module)]
    else:
        deltas = compute_deltas(build_symbols(old_g), build_symbols(new_g))
        if renamed and not removed:
            deltas.insert(0, ("MODULE_RENAMED", mr.BASE + module))
    req = required_bump(deltas)
    old_v, new_v = version_of(old_g), version_of(new_g)
    decl = None if removed else declared_bump(old_v, new_v)

    if retired:
        verdict = "MODULE_RETIRED"
    elif removed:
        verdict = "MODULE_REMOVED"
    elif decl == "decreased":
        verdict = "VERSION_DECREASED"
    elif req == BUMP_NONE:
        verdict = "OK"
    elif decl is None:
        verdict = "UNKNOWN_VERSION"
    elif decl == BUMP_NONE:
        # Accumulation phase: owl:versionInfo intentionally not bumped yet (repo
        # policy - bump only at the release cut). This is expected, not a fault;
        # we forecast the next version rather than warn. INSUFFICIENT_BUMP is
        # reserved for a release-cut PR that *did* bump, but not far enough.
        verdict = "RELEASE_PENDING"
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
        # Minimum next release version implied by the changes = last released
        # version + the required bump. This is the "prospective new version".
        "prospective_version": apply_bump(old_v, req),
        "verdict": verdict,
        "deltas": deltas,
        # the module whose release is the baseline: the module itself, or the one it replaced (#171)
        "baseline_module": base_module,
        "renamed_from": base_module if renamed else None,
        "replaced_by": replaced_by if retired else None,
    }


def analyze_pr_change(repo_root, base_dir, module):
    """Deltas introduced by THIS PR: base-branch `src/<module>.ttl` vs working `src/<module>.ttl`.

    Returns {module, deltas, required_bump}, or None if the module is in neither place. A module
    absent from base_dir (new in this PR) diffs as all-added; one absent from `src/` (deleted or
    renamed) diffs as all-removed. The rename map (#171) refines both: a new module that replaces one in the
    base diffs against it under the new names, plus one MODULE_RENAMED change, and a module that leaves `src/`
    while its successor is there is one MODULE_RETIRED change.
    """
    repo_root = Path(repo_root)
    renames = mr.load(repo_root)
    new_file = repo_root / "src" / f"{module}.ttl"
    old_file = Path(base_dir) / f"{module}.ttl"
    if not new_file.is_file() and not old_file.is_file():
        return None
    replaced_by = mr.successor(renames, module)
    if old_file.is_file() and not new_file.is_file() and replaced_by and (repo_root / "src" / f"{replaced_by}.ttl").is_file():
        deltas = [("MODULE_RETIRED", mr.BASE + module)]
        return {"module": module, "deltas": deltas, "required_bump": required_bump(deltas), "details": {}}
    renamed_from = None
    old_name = mr.predecessor(renames, module)
    if not old_file.is_file() and old_name and (Path(base_dir) / f"{old_name}.ttl").is_file():
        renamed_from, old_file = old_name, Path(base_dir) / f"{old_name}.ttl"
    new_syms = {}
    if new_file.is_file():
        new_g = Graph()
        new_g.parse(str(new_file), format="turtle")
        new_syms = build_symbols(new_g)
    old_syms = {}
    if old_file.is_file():
        old_g = Graph()
        old_g.parse(str(old_file), format="turtle")
        if renamed_from:
            old_g = mr.rewrite_graph(old_g, renames)
        old_syms = build_symbols(old_g)
    # a module present in the base but not in the PR is deleted/renamed: every term diffs as removed
    deltas = compute_deltas(old_syms, new_syms)
    if renamed_from:
        deltas.insert(0, ("MODULE_RENAMED", mr.BASE + module))
    return {"module": module, "deltas": deltas, "required_bump": required_bump(deltas),
            "details": annotation_details(old_syms, new_syms), "renamed_from": renamed_from}


def print_report(result):
    m = result["module"]
    if result["status"] == "no-baseline":
        print(f"  [SKIP] {m}: no released snapshot under versions/{m}/ to diff against")
        return
    deltas = result["deltas"]
    by_sev = {}
    for d, iri in deltas:
        by_sev.setdefault(DELTA_SEVERITY[d], []).append((d, iri))
    renamed = f" (renamed from {result['renamed_from']})" if result.get("renamed_from") else ""
    print(
        f"  {m}{renamed}: {result['old_version']} -> {result['new_version']} | "
        f"required bump: {result['required_bump'].upper()} | "
        f"declared: {(result['declared_bump'] or 'n/a')} | {result['verdict']}"
    )
    for sev in (BREAKING, POTENTIALLY, NON_BREAKING):
        for d, iri in by_sev.get(sev, []):
            local = iri.rsplit("/", 1)[-1].rsplit("#", 1)[-1]
            print(f"      - [{sev}] {d}: {local}")


_BUMP_LABEL = {BUMP_MAJOR: "MAJOR", BUMP_MINOR: "MINOR", BUMP_PATCH: "PATCH", BUMP_NONE: "none"}
def to_markdown(results, pr_results=None, links=None):
    """Render a GitHub-flavored Markdown report (for a PR comment).

    ``results`` — cumulative analysis (working ``src/`` vs each module's last
    released snapshot); drives the "Next version if released" forecast.
    ``pr_results`` — optional per-module deltas *introduced by this PR* (``src/``
    vs the base branch, from ``analyze_pr_change``); when given, a "Changes in
    this PR" section is shown first. When ``None`` (e.g. a local run without
    ``--base-dir``) that section is omitted.
    ``links`` — optional (see ``links_from_env``): each listed change then links to its line in the PR diff (#183)
    and in ``src/<module>.ttl`` at the head commit (#181).
    """
    out = ["## 🔢 Ontology version impact", ""]

    # --- Section 1: what THIS PR changes (base branch -> this PR) --------------
    if pr_results is not None:
        pr_changed = [r for r in pr_results if r and r["deltas"]]
        out.append("### Changes in this PR")
        if not pr_changed:
            out.append("This PR makes **no changes** to the ontology `src/` files.")
        else:
            for r in pr_changed:
                out.append(
                    f"- **`{r['module']}`** — {len(r['deltas'])} change(s), "
                    f"**{_BUMP_LABEL[r['required_bump']]}**-level:"
                )
                by_sev = {}
                for d, iri in r["deltas"]:
                    by_sev.setdefault(DELTA_SEVERITY[d], []).append((d, iri))
                details = r.get("details", {})
                text = base_text = None
                if links:
                    try:
                        text = links["read"](r["module"])
                    except Exception:
                        text = None  # no text, no links: the report never fails for it
                    try:
                        base_text = links["read_base"](r["module"]) if links.get("read_base") else None
                    except Exception:
                        base_text = None
                path_hash = hashlib.sha256(f"src/{r['module']}.ttl".encode()).hexdigest()  # GitHub's anchor of a file in a PR diff

                def refs(line, side="R"):
                    """Links to one line: the PR diff (R = new side, L = old side) when the PR is known, and the file at the head."""
                    found = []
                    if links.get("pr"):
                        found.append(f"[diff](https://github.com/{links['base_repo']}/pull/{links['pr']}/changes#diff-{path_hash}{side}{line})")
                    if side == "R":
                        found.append(f"[file](https://github.com/{links['repo']}/blob/{links['sha']}/src/{r['module']}.ttl#L{line})")
                    return " · ".join(found)

                for sev in (BREAKING, POTENTIALLY, NON_BREAKING):
                    for d, iri in by_sev.get(sev, []):
                        local = iri.rsplit("/", 1)[-1].rsplit("#", 1)[-1]
                        names = details.get(iri, []) if d == "ANNOTATION_CHANGED" else []
                        subject, where, side = None, {}, "R"
                        if d == "TERM_REMOVED":  # no line in the PR head: the line is on the old side of the diff
                            if base_text is not None:
                                subject, side = locate_lines(base_text, iri)[0], "L"
                        elif text is not None:
                            subject, where = locate_lines(text, iri, names)
                        if names:
                            parts = []
                            for name in names:
                                line = where.get(name) or subject
                                parts.append(f"`{name}`" + (f" (line {line}: {refs(line)})" if line else ""))
                            out.append(f"  - `[{sev}]` {d} — `{local}`: " + ", ".join(parts))
                        elif subject and refs(subject, side):
                            out.append(f"  - `[{sev}]` {d} — `{local}` (line {subject}: {refs(subject, side)})")
                        else:
                            out.append(f"  - `[{sev}]` {d} — `{local}`")
        out.append("")

    # --- Section 2: cumulative next-version forecast (src vs last released) ----
    analyzed = [r for r in results if r["status"] == "analyzed"]
    changed = [r for r in analyzed if r["required_bump"] != BUMP_NONE]
    skipped = [r for r in results if r["status"] != "analyzed"]

    out.append("### Next version if released")
    if not changed:
        out.append("✅ No unreleased changes — every module stays at its current version.")
    else:
        out.append(
            "The running total of **all unreleased changes since each module's last release** "
            "(not just this PR) — i.e. what the next release would be:"
        )
        out.append("")
        out.append("| Module | Current | → Next version |")
        out.append("|---|:--:|:--:|")
        for r in changed:
            current = f"`{r['renamed_from']}` `{r['old_version']}`" if r.get("renamed_from") else f"`{r['old_version']}`"
            out.append(
                f"| `{r['module']}` | {current} | "
                f"**`{r['prospective_version']}`** ({_BUMP_LABEL[r['required_bump']]}) |"
            )

    renamed = [r for r in changed if r.get("renamed_from")]
    if renamed:
        out.append("")
        out.append(
            "> ℹ️ Renamed (`config/module_renames.json`): "
            + ", ".join(f"`{r['module']}` replaces `{r['renamed_from']}`" for r in renamed)
            + ". A renamed module continues the old one's numbering: its next version is the old module's last release "
            "plus a MAJOR, and its terms are compared with the old IRIs mapped to the new ones."
        )
    retired = [r for r in analyzed if r.get("replaced_by")]
    if retired:
        out.append("")
        out.append("> ℹ️ Retired from `src/` (its releases stay published): "
                   + ", ".join(f"`{r['module']}` (replaced by `{r['replaced_by']}`)" for r in retired) + ".")

    if skipped:
        names = ", ".join(f"`{r['module']}`" for r in skipped)
        out.append("")
        out.append(f"> ℹ️ No released snapshot to diff against yet (skipped): {names}.")

    # Warn only when a release-cut PR actually under-bumped owl:versionInfo (rare).
    problems = [r for r in analyzed if r["verdict"] in ("INSUFFICIENT_BUMP", "VERSION_DECREASED")]
    if problems:
        out.append("")
        out.append("⚠️ **Heads-up — the declared version bump is smaller than the change needs:**")
        for r in problems:
            out.append(
                f"- `{r['module']}`: this PR sets `owl:versionInfo` to a "
                f"**{r['declared_bump'] or 'none'}** bump, but the changes need "
                f"**{_BUMP_LABEL[r['required_bump']]}** (→ `{r['prospective_version']}`)."
            )

    out.append("")
    out.append("<details><summary>ℹ️ How this works</summary>")
    out.append("")
    out.append(
        "**Changes in this PR** diffs the PR against its base branch. **Next version if released** compares "
        "each module's working `src/` against its **last released snapshot** and maps the accumulated change "
        "to the **minimum next [SemVer](https://semver.org/)** (per the "
        "[compatibility-diff spec](https://github.com/BuroHappoldMachineLearning/ADIRO/blob/main/docs/contribute/versioning/compatibility-diff-algorithm-spec.md)). "
        "`owl:versionInfo` is only bumped **at the release cut (after merge)**, so the forecast is cumulative "
        "across every unreleased PR. Advisory only — it never blocks the PR. (warn mode.)"
    )
    out.append("")
    out.append("</details>")
    return "\n".join(out)


def main():
    repo_root = Path(__file__).parent.parent
    argv = sys.argv[1:]
    enforce = "--enforce" in argv
    as_markdown = "--markdown" in argv
    base_dir = None
    if "--base-dir" in argv:
        i = argv.index("--base-dir")
        base_dir = argv[i + 1] if i + 1 < len(argv) else None
    # Positional args = modules; exclude flags and the --base-dir value.
    modules = [a for a in argv if not a.startswith("-") and a != base_dir]
    if not modules:
        found = {p.stem for p in (repo_root / "src").glob("*.ttl")}
        if base_dir is not None:  # also modules the PR deleted: they exist in the base only
            found |= {p.stem for p in Path(base_dir).glob("*.ttl")}
        modules = sorted(found)

    results = [analyze_module(repo_root, module) for module in modules]

    if as_markdown:
        pr_results = None
        if base_dir is not None:
            pr_results = [analyze_pr_change(repo_root, base_dir, m) for m in modules]
        # UTF-8 to stdout regardless of the host console codepage (Windows cp1252).
        sys.stdout.buffer.write((to_markdown(results, pr_results, links_from_env(repo_root, base_dir)) + "\n").encode("utf-8"))
        return

    print("Compatibility diff (warn mode) - src/ vs last released snapshot:")
    problems = 0
    for result in results:
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
