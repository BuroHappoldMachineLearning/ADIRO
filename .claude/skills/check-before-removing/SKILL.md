---
name: check-before-removing
description: >-
  Use before deleting or changing anything in ADIRO because a warning, a check, a bot comment or tidiness says to: an owl:imports
  that is "unused", an unused prefix, a term nobody seems to use, a property, a class, a file, a changelog entry. Find out why it
  is there first, and say in the pull request that you removed it and why.
---

# ADIRO: a warning is a question, not an instruction

The rule is in [`AGENTS.md`](../../../AGENTS.md) ("A warning is a question"); this skill is the Claude Code checklist for it. A
validator, a bot or an advisory check reports what it can see. It cannot see intent, and in an ontology much of the intent lives
outside the file being checked. The case that made this a rule: an `owl:imports` flagged as "unused" was dropped, but the
module used it as a **data pattern** (`geom:hasBoundingBox` has no domain on purpose), so no axiom of the module named a term of
the import, and the dependency documented in the ORSD was lost ([#195](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/195)).

## Before you delete

1. **Say what the warning claims and what it cannot see.** "Unused" usually means "no axiom in this file mentions it"; it does not
   see data patterns, the documentation, other modules, the display configs, the tests or a downstream consumer.
2. **Find why it exists.**
   - `config/module_imports.json` records each module's imports and the reason (for an import).
   - `git log -S'<name>' --oneline -- src docs` finds the commit that added it, and its message and issue say why.
   - Search `docs/specification/` (the ORSD term-placement tables, the design decisions and design notes), `changelogs/` and `tests/`
     for the name, as the `check-existing-work` skill does for issues.
   - Search the issues and Discussions for it.
3. **Decide with that evidence.**
   - Still needed, but the file does not show it: **state the use** (an axiom such as a `min 0` restriction, as for
     `Titleblock` and `geom:hasBoundingBox`), keep the thing, and let the warning go away that way.
   - Not needed: remove it **and** update every place that names it (the pin, the ORSD, the design pages, the changelog, the display
     config, the tests) in the same pull request.
   - Unsure: ask the person who asked for the work; do not guess.
4. **Say it.** Name what you removed and why in the pull request description and in the changelog (a removed term, property or
   import is a breaking change for a consumer). Never let a removal ride along unannounced inside a larger change.

## Rules

- A removal made only because a check complained is not a reason. A reason is a statement that the thing is not needed, with the
  evidence from step 2.
- The same care applies to a rename, to loosening a restriction and to deleting a released changelog line (released sections do not
  change; a deliberate correction is listed in `tests/test_module_imports.py`).
- Public repository: no internal tool names, no internal tracker IDs in what you write.
