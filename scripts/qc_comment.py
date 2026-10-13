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
    "and OWL 2 DL, including a root change that breaks its dependents."
)


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


def minor_checks(report_tsv, run_url=None):
    lines = ["### Minor checks", "",
             "Executed via ROBOT for logical and structural QC; the ROBOT report stays advisory.", ""]
    if report_tsv is None:
        return lines + ["The ROBOT report did not run; see the reasoner status above.", ""]
    rows = parse_report(report_tsv)
    if not rows:
        return lines + ["✅ No findings.", ""]
    lines += ["| Level | Rule | Count | Findings |", "|---|---|--:|:--|"]
    for level, rule, rule_rows in by_rule(rows):
        preview = "<details><summary>Show</summary>" + "<br>".join(preview_lines(rule, rule_rows)) + "</details>"
        lines.append(f"| {level} | `{_cell(rule)}` | {len(rule_rows)} | {preview} |")
    lines.append("")
    if run_url:
        lines += [f"The full report is the `reasoning-out` artifact of this [workflow run]({run_url}).", ""]
    return lines


def render(rc, reason_out, report_tsv, validate_md, run_url=None):
    """The comment body. `rc` is the reasoner's exit code ('0' is consistent); the other inputs may be None."""
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
    lines += minor_checks(report_tsv, run_url)
    lines += ["<details><summary>About these checks</summary>", "", ABOUT, "", "</details>"]
    return "\n".join(lines) + "\n"


def _read(path):
    return path.read_text(encoding="utf-8") if path.is_file() else None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=".tools/reasoning-out")
    args = ap.parse_args(argv)
    out = Path(args.out_dir)
    rc = _read(out / "reason.rc")
    text = render(rc if rc is not None else "1", _read(out / "reason.out"), _read(out / "report.tsv"),
                  _read(out / "validate.md"), os.environ.get("RUN_URL"))
    sys.stdout.buffer.write(text.encode("utf-8"))


if __name__ == "__main__":
    main()
