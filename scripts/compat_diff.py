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
    }


def analyze_pr_change(repo_root, base_dir, module):
    """Deltas introduced by THIS PR: base-branch `src/<module>.ttl` vs working `src/<module>.ttl`.

    Returns {module, deltas, required_bump}, or None if the module has no working
    file. A module absent from base_dir (new in this PR) diffs as all-added.
    """
    new_file = repo_root / "src" / f"{module}.ttl"
    if not new_file.is_file():
        return None
    new_g = Graph()
    new_g.parse(str(new_file), format="turtle")
    old_syms = {}
    old_file = Path(base_dir) / f"{module}.ttl"
    if old_file.is_file():
        old_g = Graph()
        old_g.parse(str(old_file), format="turtle")
        old_syms = build_symbols(old_g)
    deltas = compute_deltas(old_syms, build_symbols(new_g))
    return {"module": module, "deltas": deltas, "required_bump": required_bump(deltas)}


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


_BUMP_LABEL = {BUMP_MAJOR: "MAJOR", BUMP_MINOR: "MINOR", BUMP_PATCH: "PATCH", BUMP_NONE: "none"}
def to_markdown(results, pr_results=None):
    """Render a GitHub-flavored Markdown report (for a PR comment).

    ``results`` — cumulative analysis (working ``src/`` vs each module's last
    released snapshot); drives the "Next version if released" forecast.
    ``pr_results`` — optional per-module deltas *introduced by this PR* (``src/``
    vs the base branch, from ``analyze_pr_change``); when given, a "Changes in
    this PR" section is shown first. When ``None`` (e.g. a local run without
    ``--base-dir``) that section is omitted.
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
                for sev in (BREAKING, POTENTIALLY, NON_BREAKING):
                    for d, iri in by_sev.get(sev, []):
                        local = iri.rsplit("/", 1)[-1].rsplit("#", 1)[-1]
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
            out.append(
                f"| `{r['module']}` | `{r['old_version']}` | "
                f"**`{r['prospective_version']}`** ({_BUMP_LABEL[r['required_bump']]}) |"
            )

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
        "[compatibility-diff spec](https://github.com/BuroHappoldMachineLearning/ADIRO/blob/main/docs/governance/compatibility-diff-algorithm-spec.md)). "
        "`owl:versionInfo` is only bumped **at the release cut (after merge)**, so the forecast is cumulative "
        "across every unreleased PR. Advisory only — it never blocks the PR. (RES-67 · warn mode.)"
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
    modules = modules or sorted(p.stem for p in (repo_root / "src").glob("*.ttl"))

    results = [analyze_module(repo_root, module) for module in modules]

    if as_markdown:
        pr_results = None
        if base_dir is not None:
            pr_results = [analyze_pr_change(repo_root, base_dir, m) for m in modules]
        # UTF-8 to stdout regardless of the host console codepage (Windows cp1252).
        sys.stdout.buffer.write((to_markdown(results, pr_results) + "\n").encode("utf-8"))
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
