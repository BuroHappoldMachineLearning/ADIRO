#!/usr/bin/env python3
"""
Compose the sticky "Ontology reasoning & QC" PR comment (ontology-reasoning.yml, #130).

Reads what scripts/run_reasoning.sh and scripts/validate_ontology.py left in the output directory
(`.tools/reasoning-out/`: reason.rc, reason.out, report.tsv, validate.md) and prints the comment as Markdown.
It used to be a block of shell inside the workflow, which could not be tested.

The ROBOT report is shown by rule (a count per level and rule), not as a dump of raw rows: the INFO rows are
noise by design (a root class has no superclass), so they are only counted, and the ERROR and WARN rows, which
need a person, are listed with readable names. The full report is kept as a run artifact.

Usage:  qc_comment.py [--out-dir DIR]     (RUN_URL in the environment adds the artifact link)
"""
import argparse
import csv
import html
import io
import os
import sys
from collections import Counter
from pathlib import Path

ADIRO = "https://w3id.org/adiro/"
LEVELS = ("ERROR", "WARN", "INFO")
LIST_LIMIT = 25


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


def _cell(text):
    """Safe inside a Markdown table cell: angle brackets, pipes and newlines."""
    return html.escape(" ".join(str(text).split()), quote=False).replace("|", "&#124;")


def counts(rows):
    """{level: n} for every level, so the headline never has to guess a missing one."""
    found = Counter(r["level"] for r in rows)
    return {level: found.get(level, 0) for level in LEVELS}


def by_rule(rows):
    """[(level, rule, n)] ordered by level (ERROR first), then rule."""
    found = Counter((r["level"], r["rule"]) for r in rows)
    order = {level: i for i, level in enumerate(LEVELS)}
    return sorted(((lv, rule, n) for (lv, rule), n in found.items()), key=lambda t: (order.get(t[0], len(LEVELS)), t[1]))


def robot_section(report_tsv, run_url=None):
    lines = ["### ROBOT report (logical / structural QC)", ""]
    if report_tsv is None:
        return lines + ["The ROBOT report did not run; see the reasoner status above.", ""]
    rows = parse_report(report_tsv)
    total = counts(rows)
    lines += [f"**{total['ERROR']} error(s), {total['WARN']} warning(s), {total['INFO']} info.**", ""]
    if not rows:
        return lines + ["✅ No findings.", ""]
    lines += ["| Level | Rule | Count |", "|---|---|--:|"]
    lines += [f"| {level} | `{_cell(rule)}` | {n} |" for level, rule, n in by_rule(rows)]
    lines.append("")
    actionable = [r for r in rows if r["level"] in ("ERROR", "WARN")]
    if actionable:
        shown = actionable[:LIST_LIMIT]
        lines += [f"<details><summary>ERROR and WARN rows ({len(actionable)})</summary>", "",
                  "| Level | Rule | Subject | Property | Value |", "|---|---|---|---|---|"]
        lines += [f"| {r['level']} | `{_cell(r['rule'])}` | {_cell(short_subject(r['subject']))} | {_cell(r['property'])} | {_cell(r['value'])} |"
                  for r in shown]
        if len(actionable) > len(shown):
            lines += ["", f"… and {len(actionable) - len(shown)} more."]
        lines += ["", "</details>", ""]
    if counts(rows)["INFO"]:
        lines += ["INFO findings are only counted here.", ""]
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
    lines = [
        "## 🧠 Ontology reasoning &amp; QC",
        "",
        "Whole-suite OWL 2 DL reasoning (**HermiT**) and the ROBOT `report` over all modules at *latest* (imports resolved "
        "offline via `src/catalog-v001.xml`), then the repository's own checks. The **reasoner is a blocking gate**; the "
        "rest is advisory. Run the same script locally with `bash scripts/run_reasoning.sh` (see AGENTS.md).",
        "",
        "### Consistency / satisfiability",
        status,
        "",
    ]
    if str(rc).strip() != "0" and reason_out:
        tail = "\n".join(reason_out.splitlines()[-60:])
        lines += ["<details><summary>Reasoner output</summary>", "", "```", tail, "```", "", "</details>", ""]
    lines += robot_section(report_tsv, run_url)
    if validate_md:
        lines += [validate_md.strip(), ""]
    lines.append("<sub>The reasoner blocks (consistency, unsatisfiable classes, OWL 2 DL, including a root change that breaks "
                 "its dependents); the ROBOT report stays advisory.</sub>")
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
