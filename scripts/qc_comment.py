#!/usr/bin/env python3
"""
Compose the sticky "Ontology reasoning & QC" PR comment (ontology-reasoning.yml, #130).

Reads what scripts/run_reasoning.sh and scripts/validate_ontology.py left in the output directory
(`.tools/reasoning-out/`: reason.rc, reason.out, report.tsv, validate.md) and prints the comment as Markdown.
It used to be a block of shell inside the workflow, which could not be tested.

The comment, top to bottom: the reasoner's verdict, the **Important checks** (the repository's own, from
validate_ontology.py), the **Minor checks** (ROBOT's logical / structural QC), and a collapsed "About" note.

The ROBOT findings are one table row per rule with a count and an expandable preview. The rows of one rule are
usually near-duplicates (twenty-five root classes with no superclass, say), so the preview groups them, by module
for the ones that carry only a subject, instead of listing every row.

Usage:  qc_comment.py [--out-dir DIR]     (RUN_URL in the environment adds the artifact link)
"""
import argparse
import csv
import html
import io
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

ADIRO = "https://w3id.org/adiro/"
LEVELS = ("ERROR", "WARN", "INFO")
NAMES_PER_GROUP = 8   # names listed per module before "+N more"
ROWS_PER_RULE = 10    # rows listed for a rule whose findings carry a value, before "+N more"

# What a ROBOT rule means, in a line, shown at the top of its preview. Only rules ADIRO is likely to hit.
RULE_HELP = {
    "missing_superclass": "A class with no asserted superclass: it sits at the top of its hierarchy. Expected for a root class.",
    "duplicate_label": "Two terms share the same rdfs:label. A docs-quality convention, not an RDF requirement.",
    "multiple_labels": "A term has more than one rdfs:label; other-language names belong in skos:altLabel.",
    "missing_label": "A term has no rdfs:label.",
    "label_whitespace": "A label has leading or trailing whitespace.",
}

ABOUT = (
    "Whole-suite OWL 2 DL reasoning (**HermiT**) and the ROBOT `report` over all modules at *latest* (imports resolved "
    "offline via `src/catalog-v001.xml`), then the repository's own checks. The **reasoner is a blocking gate**; the "
    "rest is advisory. Run the same script locally with `bash scripts/run_reasoning.sh` (see AGENTS.md).\n\n"
    "Important checks: executed via `scripts/validate_ontology.py`. The reasoner blocks: consistency, unsatisfiable classes "
    "and OWL 2 DL, including a root change that breaks its dependents.\n\n"
    "Minor checks: ROBOT's levels (ERROR, WARN, INFO) are its own; here every one is advisory, and only the reasoner blocks."
)

# The rules whose findings can only record a deprecation: a stub (owl:deprecated, dcterms:isReplacedBy) keeps its released
# axioms and label and is equivalent to the term that replaces it (#281, #290). Those findings are left out (#299).
CYCLE_RULES = ("deprecated_class_reference", "deprecated_property_reference", "equivalent_pair", "duplicate_label")
PROPERTIES = {"rdfs:subClassOf": "http://www.w3.org/2000/01/rdf-schema#subClassOf",
              "owl:equivalentClass": "http://www.w3.org/2002/07/owl#equivalentClass",
              "owl:disjointWith": "http://www.w3.org/2002/07/owl#disjointWith"}
DEPRECATED = "http://www.w3.org/2002/07/owl#deprecated"
REPLACED_BY = "http://purl.org/dc/terms/isReplacedBy"
LABEL = "http://www.w3.org/2000/01/rdf-schema#label"


def load_suite(src="src"):
    """Every module in `src` as one graph, to tell a deprecation from a defect; None when it cannot be read."""
    try:
        from rdflib import Graph
        suite = Graph()
        files = sorted(Path(src).glob("*.ttl"))
        for path in files:
            suite.parse(str(path), format="turtle")
        return suite if files else None
    except Exception:  # noqa: BLE001 - without the ontology every finding is shown, which is the safe side
        return None


def leave_out_deprecation_cycle(rows, suite):
    """
    The rows that report a defect, and a Counter by rule of the rows left out because they only record a deprecation.

    - `deprecated_class_reference`: a stub's own axiom (a superclass, its equivalence to its replacement), or another
      deprecated term that refers to it. A live class or a restriction that refers to a deprecated class is a defect
      and stays: ROBOT shows both directions as the same row, so the asserted triple decides which one it is.
      A stub's own restriction (its value is a blank node, not an IRI) is left out too.
    - `deprecated_property_reference`: a stub's own restriction on a deprecated property. A row whose subject is a
      blank node cannot be told from a live class's restriction, so it stays.
    - `equivalent_pair`: a stub and the term that replaces it.
    - `duplicate_label`: a term whose every namesake is its replacement or the stub it replaces.
    """
    if suite is None:
        return rows, Counter()
    from rdflib import URIRef

    def deprecated(term):
        return any(str(v).lower() == "true" for v in suite.objects(term, URIRef(DEPRECATED)))

    def replacement_pair(a, b):
        return any(deprecated(x) and (x, URIRef(REPLACED_BY), y) in suite for x, y in ((a, b), (b, a)))

    def cycle(row):
        if not row["subject"].startswith("http"):
            return False  # "blank node": a restriction that refers to a deprecated class is a defect
        rule, subject, value = row["rule"], URIRef(row["subject"]), row["value"]
        if rule == "deprecated_property_reference":
            # a stub's own restriction on a deprecated property; an IRI value could be either direction, so it stays
            return deprecated(subject) and not value.startswith("http")
        if rule == "deprecated_class_reference":
            prop = PROPERTIES.get(row["property"])
            if prop is None or not deprecated(subject):
                return False
            if not value.startswith("http"):
                return True  # the stub's own anonymous superclass (a restriction), which ROBOT names by a generated id
            other = URIRef(value)
            if (subject, URIRef(prop), other) in suite:
                return True  # the stub's own axiom
            return (other, URIRef(prop), subject) in suite and deprecated(other)
        if rule == "equivalent_pair":
            return replacement_pair(subject, URIRef(value))
        if rule == "duplicate_label":
            namesakes = {s for s in suite.subjects(URIRef(LABEL), None)
                         if s != subject and any(str(o) == value for o in suite.objects(s, URIRef(LABEL)))}
            return bool(namesakes) and all(replacement_pair(subject, s) for s in namesakes)
        return False

    kept, left_out = [], Counter()
    for row in rows:
        if row["rule"] in CYCLE_RULES and cycle(row):
            left_out[row["rule"]] += 1
        else:
            kept.append(row)
    return kept, left_out


def parse_report(text):
    """Rows of ROBOT's report.tsv (Level, Rule Name, Subject, Property, Value) as dicts."""
    rows = []
    for rec in csv.DictReader(io.StringIO(text), delimiter="\t", quoting=csv.QUOTE_NONE):
        level = (rec.get("Level") or "").strip()
        if level:
            rows.append({
                "level": level,
                "rule": (rec.get("Rule Name") or "").strip(),
                "subject": (rec.get("Subject") or "").strip(),
                "property": (rec.get("Property") or "").strip(),
                "value": (rec.get("Value") or "").strip(),
            })
    return rows


def short_subject(subject):
    """An ADIRO IRI as `module:Term`; anything else (already a CURIE, or an external IRI) as it is."""
    if subject.startswith(ADIRO):
        return subject[len(ADIRO):].replace("#", ":", 1)
    return subject


def split_subject(subject):
    """(group, term): the module or vocabulary a subject belongs to, and its local name."""
    short = short_subject(subject)
    if short.startswith(("http://", "https://")):
        base, sep, term = short.partition("#")
        if sep:
            return base.rstrip("/").rsplit("/", 1)[-1] or "other", term
        return "other", short
    if ":" in short:
        group, _, term = short.partition(":")
        return group, term
    return "other", short


def _cell(text):
    """Safe inside a Markdown table cell: angle brackets, pipes and newlines."""
    return html.escape(" ".join(str(text).split()), quote=False).replace("|", "&#124;")


def by_rule(rows):
    """[(level, rule, [rows])] ordered by level (ERROR first), then rule."""
    groups = defaultdict(list)
    for row in rows:
        groups[(row["level"], row["rule"])].append(row)
    order = {level: i for i, level in enumerate(LEVELS)}
    return [(lv, rule, groups[(lv, rule)]) for lv, rule in sorted(groups, key=lambda k: (order.get(k[0], len(LEVELS)), k[1]))]


def preview_lines(rule, rows):
    """The lines of one rule's expandable preview: what the rule means, then its findings, near-duplicates grouped."""
    lines = []
    if rule in RULE_HELP:
        lines.append(f"<i>{_cell(RULE_HELP[rule])}</i>")
    if all(not row["value"] for row in rows):
        # Only subjects: list the names grouped by module, so twenty-five similar rows become a handful of lines.
        names = defaultdict(set)
        for row in rows:
            group, term = split_subject(row["subject"])
            names[group].add(term)
        for group in sorted(names):
            terms = sorted(names[group])
            shown = ", ".join(terms[:NAMES_PER_GROUP]) + (f" +{len(terms) - NAMES_PER_GROUP} more" if len(terms) > NAMES_PER_GROUP else "")
            lines.append(f"<b>{_cell(group)}</b> ({len(terms)}): {_cell(shown)}")
    else:
        for row in rows[:ROWS_PER_RULE]:
            lines.append(f"{_cell(short_subject(row['subject']))}: {_cell(row['value'])}")
        if len(rows) > ROWS_PER_RULE:
            lines.append(f"+{len(rows) - ROWS_PER_RULE} more")
    return lines


def minor_checks(report_tsv, run_url=None, rows=None, left_out=0):
    lines = ["### Minor checks", "",
             "Executed via ROBOT for logical and structural QC; the ROBOT report stays advisory.", ""]
    if report_tsv is None:
        return lines + ["The ROBOT report did not run; see the reasoner status above.", ""]
    rows = parse_report(report_tsv) if rows is None else rows
    if not rows:
        note = f" ({left_out} that only record a deprecation are left out; see *About these checks*.)" if left_out else ""
        return lines + [f"✅ No findings.{note}", ""]
    lines += ["| Level | Rule | Count | Findings |", "|---|---|--:|:--|"]
    for level, rule, rule_rows in by_rule(rows):
        preview = "<details><summary>Show</summary>" + "<br>".join(preview_lines(rule, rule_rows)) + "</details>"
        lines.append(f"| {level} | `{_cell(rule)}` | {len(rule_rows)} | {preview} |")
    lines.append("")
    if run_url:
        lines += [f"The full report is the `reasoning-out` artifact of this [workflow run]({run_url}).", ""]
    return lines


def render(rc, reason_out, report_tsv, validate_md, run_url=None, suite=None):
    """The comment body. `rc` is the reasoner's exit code ('0' is consistent); the other inputs may be None.

    `suite` (the modules as one graph) lets the findings that only record a deprecation be left out and counted (#299).
    """
    if str(rc).strip() == "0":
        status = "✅ **Consistent** — no unsatisfiable classes (HermiT, suite at latest)."
    else:
        status = ("⛔ **Reasoner failed** — the merged suite is inconsistent, has an unsatisfiable class, or is not valid "
                  "OWL 2 DL. See the reasoner output below. **This fails the check — fix before merge.**")
    lines = ["## 🧠 Ontology reasoning &amp; QC", "", "### Consistency / satisfiability", status, ""]
    if str(rc).strip() != "0" and reason_out:
        tail = "\n".join(reason_out.splitlines()[-60:])
        lines += ["<details><summary>Reasoner output</summary>", "", "```", tail, "```", "", "</details>", ""]
    if validate_md:
        lines += [validate_md.strip(), ""]
    rows, left_out = (None, Counter()) if report_tsv is None else leave_out_deprecation_cycle(parse_report(report_tsv), suite)
    lines += minor_checks(report_tsv, run_url, rows, sum(left_out.values()))
    about = ABOUT
    if left_out:
        detail = ", ".join(f"`{rule}` {n}" for rule, n in sorted(left_out.items()))
        about += (f"\n\n{sum(left_out.values())} ROBOT findings are left out ({detail}): each only records a deprecation, a "
                  "deprecated term (`owl:deprecated`, `dcterms:isReplacedBy`) keeping its released axioms and label, and "
                  "being equivalent to the term that replaces it. A live term that refers to a deprecated one is still shown.")
    lines += ["<details><summary>About these checks</summary>", "", about, "", "</details>"]
    return "\n".join(lines) + "\n"


def _read(path):
    return path.read_text(encoding="utf-8") if path.is_file() else None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=".tools/reasoning-out")
    ap.add_argument("--src", default="src", help="the modules, to tell a deprecation from a defect (#299)")
    args = ap.parse_args(argv)
    out = Path(args.out_dir)
    rc = _read(out / "reason.rc")
    text = render(rc if rc is not None else "1", _read(out / "reason.out"), _read(out / "report.tsv"),
                  _read(out / "validate.md"), os.environ.get("RUN_URL"), load_suite(args.src))
    sys.stdout.buffer.write(text.encode("utf-8"))


if __name__ == "__main__":
    main()
