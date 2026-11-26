#!/usr/bin/env python3
"""
Validate TTL ontology files for correctness.

This script parses ontology files and checks for:
- Circular references in class hierarchies
- Invalid OWL structure
- Missing imports
- Other structural issues
"""

import html
import json
import os
import subprocess
import sys
from pathlib import Path
import re
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL, SKOS, DCTERMS
from rdflib.term import BNode
from collections import defaultdict, deque

import example_images
import module_renames


# Every ADIRO term must carry a human-readable description. ADIRO's definition
# vocabulary is skos:definition, with rdfs:comment kept for commentary (#273) - NOT the
# OBO convention IAO:0000115 that ROBOT's built-in `missing_definition` rule looks for.
# See docs/specification/design-decisions/usage-of-annotation-properties.md for why.
#
# While the modules are split one by one (#273), a term that still defines itself in
# rdfs:comment counts as described, as does one with dcterms:description (the other
# property pyLODE normalises into a rendered description); find_unsplit_terms reports
# the terms whose definition is not yet a skos:definition.
ADIRO_NS = "https://w3id.org/adiro/"
DESCRIPTION_PROPS = (SKOS.definition, RDFS.comment, DCTERMS.description)
TERM_TYPES = (OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty,
              OWL.AnnotationProperty, OWL.NamedIndividual,
              # a field-kind vocabulary is SKOS, and its concepts are terms a
              # reader has to understand just as much as a class is
              SKOS.Concept, SKOS.ConceptScheme)


def find_circular_references(graph):
    """
    Find circular references in class hierarchies.
    
    Returns a list of circular reference paths.
    """
    # Build subclass relationships
    subclass_map = defaultdict(set)
    all_classes = set()
    
    for s, p, o in graph.triples((None, RDFS.subClassOf, None)):
        # Skip blank nodes (BNode objects) - these are typically restrictions
        if isinstance(o, BNode):
            continue
        # Only track direct class-to-class subclass relationships
        # Skip owl:Thing as it's the root
        if o == OWL.Thing:
            all_classes.add(s)
            continue
        subclass_map[s].add(o)
        all_classes.add(s)
        all_classes.add(o)
    
    # Check for cycles using DFS
    cycles = []
    visited = set()
    rec_stack = set()
    
    def dfs(node, path):
        if node in rec_stack:
            # Found a cycle
            cycle_start = path.index(node)
            cycle = path[cycle_start:] + [node]
            cycles.append(cycle)
            return
        
        if node in visited:
            return
        
        visited.add(node)
        rec_stack.add(node)
        
        for subclass in subclass_map.get(node, []):
            if isinstance(subclass, BNode):
                continue
            dfs(subclass, path + [node])
        
        rec_stack.remove(node)
    
    for cls in all_classes:
        if cls not in visited:
            dfs(cls, [])
    
    return cycles


def find_version_inconsistencies(graph) -> list[str]:
    """
    Check per-module version metadata consistency (RES-66).

    For each owl:Ontology declared in the file:
    - it must carry exactly one owl:versionInfo and one owl:versionIRI;
    - the versionIRI must end with the versionInfo
      (e.g. ".../aec_drawing_metadata/2.0.0" <-> "2.0.0");
    - the versionIRI must equal the (unversioned) ontology IRI + "/" + versionInfo.

    Versions are per-module and independent, so this deliberately does NOT
    require different modules to share a version.

    Returns a list of error strings (empty if consistent).
    """
    errors = []

    for ontology in graph.subjects(RDF.type, OWL.Ontology):
        if isinstance(ontology, BNode):
            errors.append(
                "anonymous (blank node) owl:Ontology declaration - the ontology must "
                "have a named IRI carrying owl:versionInfo / owl:versionIRI"
            )
            continue

        version_infos = list(graph.objects(ontology, OWL.versionInfo))
        version_iris = list(graph.objects(ontology, OWL.versionIRI))

        if not version_infos:
            errors.append(f"{ontology}: missing owl:versionInfo")
        elif len(version_infos) > 1:
            errors.append(f"{ontology}: multiple owl:versionInfo values")

        if not version_iris:
            errors.append(f"{ontology}: missing owl:versionIRI")
        elif len(version_iris) > 1:
            errors.append(f"{ontology}: multiple owl:versionIRI values")

        if len(version_infos) != 1 or len(version_iris) != 1:
            continue

        version_info = str(version_infos[0]).strip()
        version_iri = str(version_iris[0]).strip()
        iri_tail = version_iri.rstrip("/").rsplit("/", 1)[-1]

        if iri_tail != version_info:
            errors.append(
                f'{ontology}: owl:versionInfo "{version_info}" does not match the '
                f'owl:versionIRI tail "{iri_tail}" ({version_iri})'
            )

        expected_iri = f"{str(ontology).rstrip('/')}/{version_info}"
        if version_iri != expected_iri:
            errors.append(
                f'{ontology}: owl:versionIRI "{version_iri}" should be the unversioned '
                f'ontology IRI + "/" + version, i.e. "{expected_iri}"'
            )

    return errors


# This repository is public, so it must not name internal tools (#89). The names are assembled from parts so the
# guard's own source does not contain them. A match in a hand-written file is an error.
_INTERNAL_TOOL_NAMES = ("c" + "vat",)
# Identifiers that still carry a name and are due to be renamed (#89); removed from this list when they are.
_PENDING_RENAME = ("is" + "c" + "vat" + "property",)
_PUBLIC_SCAN = ("AGENTS.md", "CLAUDE.md", "README.md", "CHANGELOG.md", "changelogs", "src", "scripts", ".github",
                ".claude", ".cursor", "docs/ai", "docs/contribute", "docs/specification", "data-validation",
                "docs/brainstorming")
_SCAN_SUFFIXES = {".md", ".mdc", ".ttl", ".json", ".xml", ".py", ".sh", ".yml", ".yaml", ".txt", ".toml"}


def find_internal_names(repo_root: Path) -> list[str]:
    """Hand-written files that name an internal tool, as 'path:line' findings (#89)."""
    name_re = re.compile("|".join(_INTERNAL_TOOL_NAMES), re.IGNORECASE)
    allowed_re = re.compile("|".join(re.escape(a) for a in _PENDING_RENAME), re.IGNORECASE)
    findings = []
    for entry in _PUBLIC_SCAN:
        root = repo_root / entry
        files = [root] if root.is_file() else sorted(p for p in root.rglob("*") if p.is_file()) if root.is_dir() else []
        for path in files:
            if path.suffix.lower() not in _SCAN_SUFFIXES or "__pycache__" in path.parts:
                continue
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except (UnicodeDecodeError, OSError):
                continue
            for n, line in enumerate(lines, 1):
                if name_re.search(allowed_re.sub("", line)):
                    findings.append(f"{path.relative_to(repo_root).as_posix()}:{n} names an internal tool; describe the "
                                    "behaviour generically (this repository is public)")
    return findings


def is_own_term(graph, term) -> bool:
    """
    Whether `term` is in the namespace of the module the graph holds. A declaration of another module's term
    (`adsym:x a owl:ObjectProperty`, made so a reader that does not load that module can read an
    `owl:equivalentProperty`) is a name, not a term to define here: its definition is in its own module.
    A graph with no `owl:Ontology` has no namespace to compare with, so every term is its own.
    """
    modules = [str(o) + "#" for o in graph.subjects(RDF.type, OWL.Ontology) if isinstance(o, URIRef)]
    return not modules or any(str(term).startswith(m) for m in modules)


def is_deprecated(graph, node) -> bool:
    """Whether `node` (a term or an `owl:Ontology`) says `owl:deprecated true`."""
    return any(str(v).lower() == "true" for v in graph.objects(node, OWL.deprecated))


def in_deprecated_module(graph, term) -> bool:
    """
    Whether `term` belongs to a module whose `owl:Ontology` is deprecated (#298). Such a module had its final release
    and cannot be released again, so its backlog is one nobody can act on; it is its successor's to clear.
    """
    return any(str(term).startswith(str(o) + "#") for o in graph.subjects(RDF.type, OWL.Ontology)
               if isinstance(o, URIRef) and is_deprecated(graph, o))


def find_unsplit_terms(graph) -> list[str]:
    """
    ADIRO-namespace terms whose definition is still an rdfs:comment: they have an rdfs:comment and no skos:definition (#273).

    A term with neither is reported by find_undescribed_terms; a term with a skos:definition is split, whatever
    commentary it also carries. A deprecated term is skipped, and so is every term of a deprecated module (#298): a
    stub's comment ("Deprecated: use …") points to its replacement and is no definition to split.
    """
    unsplit = []
    for term_type in TERM_TYPES:
        for term in graph.subjects(RDF.type, term_type):
            if not isinstance(term, URIRef) or not str(term).startswith(ADIRO_NS) or not is_own_term(graph, term):
                continue
            if is_deprecated(graph, term) or in_deprecated_module(graph, term):
                continue
            if (term, SKOS.definition, None) in graph or (term, RDFS.comment, None) not in graph:
                continue
            unsplit.append(str(term).split("#")[-1])
    return sorted(set(unsplit))


def find_undescribed_terms(graph) -> list[str]:
    """
    ADIRO-namespace terms with no human-readable description.

    Terms from other namespaces are exempt by design: an external term declared
    as a local stub is a name, not a definition - the definition lives at the
    source, which is what its rdfs:isDefinedBy points at. Describing it here
    would be asserting someone else's definition.

    The terms of a deprecated module are skipped (#298). A deprecated term of a live module is not: a stub with no
    text at all should still say what replaces it.
    """
    undescribed = []
    for term_type in TERM_TYPES:
        for term in graph.subjects(RDF.type, term_type):
            if not isinstance(term, URIRef) or not str(term).startswith(ADIRO_NS) or not is_own_term(graph, term):
                continue
            if in_deprecated_module(graph, term):
                continue
            if any((term, prop, None) in graph for prop in DESCRIPTION_PROPS):
                continue
            label = graph.value(term, RDFS.label)
            name = str(term).split("#")[-1]
            undescribed.append(f"{name} ({label})" if label else name)
    return sorted(set(undescribed))


def missing_changelog_modules(changed_paths, repo_root: Path | None = None) -> list[str]:
    """
    Modules whose `src/<module>.ttl` changed (added, edited or deleted) while
    `changelogs/<module>.md` did not (#105).

    Each module's `[Unreleased]` section is its release notes, written by whoever
    changes the module; nothing else checks that it was written, and the omission
    otherwise surfaces at release time. The release cut passes, because it moves the
    changelog in the same commit as it bumps the TTL.

    A module retired after a rename (deleted from `src/` while the module that replaced it is there, #171) needs no
    entry: it is not released again, and its changelog stays as it was at its final release.
    """
    root = Path(repo_root) if repo_root else Path(__file__).resolve().parent.parent
    changed = set(changed_paths)
    modules = sorted(Path(p).stem for p in changed if re.fullmatch(r"src/[^/]+\.ttl", p))
    gone = module_renames.retired(module_renames.load(root), [p.stem for p in (root / "src").glob("*.ttl")])
    return [m for m in modules if f"changelogs/{m}.md" not in changed and m not in gone]


def changed_paths_vs_base(base_ref: str, repo_root: Path) -> list[str] | None:
    """Paths under src/ and changelogs/ that differ from `base_ref` (merge-base), or None if git cannot say."""
    r = subprocess.run(["git", "diff", "--name-only", "--no-renames", f"{base_ref}...HEAD", "--", "src", "changelogs"],
                       capture_output=True, text=True, cwd=repo_root)
    return r.stdout.split() if r.returncode == 0 else None


# Releases made before the w3id.org/adiro front door declared their version IRI on the physical host. Archived releases
# are never edited, so their declared IRI stays; the w3id IRI of the same version is the one that resolves.
LEGACY_VERSION_IRI_HOST = "https://burohappoldmachinelearning.github.io/ADIRO/"


def _semver(text):
    m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", text or "")
    return tuple(int(x) for x in m.groups()) if m else None


def accepted_version_iris(module: str, version: str) -> set[str]:
    """The owl:versionIRI values an archived release of `module` may declare for the version IRI `.../<module>/<version>`."""
    return {f"https://w3id.org/adiro/{module}/{version}", f"{LEGACY_VERSION_IRI_HOST}{module}/{version}"}


def find_prior_version_problems(graph, ttl_file: Path) -> list[str]:
    """
    owl:priorVersion consistency (#122).

    Every release names ALL of its earlier published versions, because tools read only the latest release and
    do not follow the chain. So, for the owl:Ontology in the file:
    - each owl:priorVersion is `<ontology IRI>/<major.minor.patch>` and earlier than the file's own version;
    - each names a release archived under versions/<module>/<version>/ (only published versions can be named),
      whose owl:versionIRI is that IRI (or its legacy host form, see LEGACY_VERSION_IRI_HOST);
    - every earlier archived release is named.

    A renamed module (config/module_renames.json, #171) continues the history of the module it replaced, so the
    releases of that module count as its own: they may be named, by their own IRIs, and they must be.

    Returns error strings (empty if consistent).
    """
    errors = []
    module = ttl_file.stem
    repo_root = ttl_file.parent.parent
    try:
        names = module_renames.lineage(module_renames.load(repo_root), module)
    except ValueError as err:
        return [str(err)]
    for ont in graph.subjects(RDF.type, OWL.Ontology):
        base = str(ont)
        bases = {name: (base if name == module else f"{module_renames.BASE}{name}") for name in names}
        version = graph.value(ont, OWL.versionInfo)
        own = _semver(str(version)) if version is not None else None
        listed = set()
        for iri in sorted(str(o) for o in graph.objects(ont, OWL.priorVersion)):
            name, tail = next(((n, iri[len(b) + 1:]) for n, b in bases.items() if iri.startswith(b + "/")), (None, ""))
            if _semver(tail) is None:
                also = f", or of {', '.join(names[1:])} which it replaced" if len(names) > 1 else ""
                errors.append(f"owl:priorVersion <{iri}> must be a version IRI of this ontology ({base}/<major>.<minor>.<patch>{also})")
                continue
            listed.add((name, tail))
            if own is not None and _semver(tail) >= own:
                errors.append(f"owl:priorVersion <{iri}> is not earlier than this ontology's version {version}")
            archived = repo_root / "versions" / name / tail / f"{name}.ttl"
            if not archived.is_file():
                errors.append(f"owl:priorVersion <{iri}>: no archived release at versions/{name}/{tail}/ (only published versions can be named)")
                continue
            prior = Graph()
            prior.parse(str(archived), format="turtle")
            declared = {str(o) for o in prior.objects(None, OWL.versionIRI)}
            if not declared & accepted_version_iris(name, tail):
                errors.append(f"versions/{name}/{tail}/{name}.ttl declares owl:versionIRI {sorted(declared)}, not <{iri}>")
        for name, name_base in bases.items():
            archive_root = repo_root / "versions" / name
            if own is None or not archive_root.is_dir():
                continue
            for folder in sorted(archive_root.iterdir()):
                v = _semver(folder.name)
                if folder.is_dir() and v is not None and v < own and (folder / f"{name}.ttl").is_file() and (name, folder.name) not in listed:
                    errors.append(
                        f"release {folder.name}{'' if name == module else ' of ' + name} is archived but not named by "
                        f"owl:priorVersion <{name_base}/{folder.name}>: every release names all earlier versions")
    return errors


FOAF = "http://xmlns.com/foaf/0.1/"


def find_foaf_problems(graph) -> list[str]:
    """Why this module could put FOAF's own definition of depiction next to ADIRO's (#157).

    `exampleImage` is a sub-property of `foaf:depiction`, which ADIRO declares as an annotation property and FOAF defines
    as an object property. OWL 2 DL does not allow one IRI to be both, so a module that imports FOAF, or declares
    `foaf:depiction` as anything but an annotation property, would take the suite out of OWL 2 DL (Protege reports illegal
    punning, a strict reasoner refuses the ontology).
    """
    problems = []
    for ontology in graph.subjects(RDF.type, OWL.Ontology):
        for imported in sorted(str(o) for o in graph.objects(ontology, OWL.imports)):
            if imported.startswith(FOAF):
                problems.append(f"imports FOAF (<{imported}>): FOAF defines foaf:depiction as an object property, which clashes "
                                "with ADIRO's annotation property (OWL 2 DL punning); do not import it")
    depiction = URIRef(FOAF + "depiction")
    for kind in sorted(str(t) for t in graph.objects(depiction, RDF.type)):
        if kind != str(OWL.AnnotationProperty):
            problems.append(f"foaf:depiction is declared as <{kind}>: it must be an owl:AnnotationProperty only (OWL 2 DL punning)")
    return problems


def validate_ontology(ttl_file: Path) -> tuple[bool, list[str], list[str]]:
    """
    Validate an ontology file.
    
    Returns:
        (is_valid, list_of_errors, list_of_warnings)
    """
    errors = []
    warnings = []
    
    try:
        # Parse the ontology
        graph = Graph()
        graph.parse(str(ttl_file), format="turtle")
        
        # Check for circular references
        cycles = find_circular_references(graph)
        
        if cycles:
            for cycle in cycles:
                cycle_str = " → ".join(str(node) for node in cycle)
                errors.append(f"Circular reference detected in class hierarchy: {cycle_str}")
        
        # Check for basic OWL structure
        ontologies = list(graph.subjects(RDF.type, OWL.Ontology))
        if not ontologies:
            errors.append("No ontology declaration found")

        # Check per-module version metadata consistency (RES-66)
        errors.extend(find_version_inconsistencies(graph))

        # owl:priorVersion names all earlier published releases (#122)
        errors.extend(find_prior_version_problems(graph, ttl_file))

        # foaf:depiction stays an annotation property and FOAF is not imported (#157)
        errors.extend(find_foaf_problems(graph))

        # The example-image convention (#145): values and files. Advisory while the older values are migrated
        # (ENFORCE_EXAMPLE_IMAGES=1 makes it blocking); limits on committed files always block.
        image_errors, image_warnings = example_images.messages(
            example_images.problems(graph, ttl_file.stem, ttl_file.parent.parent), ttl_file.stem,
            os.environ.get("ENFORCE_EXAMPLE_IMAGES") == "1")
        errors.extend(image_errors)
        warnings.extend(image_warnings)

        # Every ADIRO term needs a human-readable description (#87).
        # Advisory by default so the existing backlog does not block CI; set
        # ENFORCE_DESCRIPTIONS=1 to promote it to an error once that backlog is
        # cleared, which is the point at which this becomes a real gate.
        unused_pfx = find_unused_prefixes(graph, ttl_file.read_text(encoding="utf-8"))
        if unused_pfx:
            warnings.append("unused @prefix declaration(s): " + ", ".join(unused_pfx))

        unused_imp = find_unused_imports(graph)
        if unused_imp:
            warnings.append("owl:imports never referenced in this file: " + ", ".join(unused_imp)
                            + " (an import can be a dependency used as a data pattern: see config/module_imports.json before removing it)")

        undescribed = find_undescribed_terms(graph)
        if undescribed:
            head = ", ".join(undescribed[:8])
            more = f" ... and {len(undescribed) - 8} more" if len(undescribed) > 8 else ""
            msg = (f"{len(undescribed)} term(s) have no skos:definition "
                   f"(nor rdfs:comment / dcterms:description): {head}{more}. "
                   "Backlog: [#87](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/87); "
                   "`LIST_UNDESCRIBED=1 uv run python scripts/validate_ontology.py` lists every term.")
            if os.environ.get("ENFORCE_DESCRIPTIONS") == "1":
                errors.append(msg)
            else:
                warnings.append(msg)
                if os.environ.get("LIST_UNDESCRIBED") == "1":
                    warnings.extend(f"  undescribed: {t}" for t in undescribed)

        # A definition is a skos:definition and rdfs:comment is commentary (#273). Advisory while the modules are split
        # one by one; ENFORCE_DEFINITIONS=1 makes it blocking once the last is.
        unsplit = find_unsplit_terms(graph)
        if unsplit:
            head = ", ".join(unsplit[:8])
            more = f" ... and {len(unsplit) - 8} more" if len(unsplit) > 8 else ""
            msg = (f"{len(unsplit)} term(s) still carry their definition in rdfs:comment and have no skos:definition: "
                   f"{head}{more}. Move the definition to skos:definition and keep rdfs:comment for commentary "
                   "([#273](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/273)).")
            if os.environ.get("ENFORCE_DEFINITIONS") == "1":
                errors.append(msg)
            else:
                warnings.append(msg)

        return len(errors) == 0, errors, warnings

    except Exception as e:
        errors.append(f"Parse error: {str(e)}")
        return False, errors, []


def find_unused_prefixes(graph, ttl_text: str) -> list[str]:
    """
    @prefix declarations the file never uses.

    Harmless to a reasoner, but they are the fossil record of a removed term:
    the alignment layer kept a `dm:` prefix for months of PR review after the
    mapping that used it was withdrawn. Checked against the parsed graph rather
    than the text, so a prefix used only in a literal's datatype still counts.
    """
    declared = dict(re.findall(r"@prefix[ \t]+([A-Za-z0-9_-]*):[ \t]+<([^>]*)>", ttl_text))
    if not declared:
        return []

    used = set()
    for s_, p_, o_ in graph:
        for term in (s_, p_, o_):
            if isinstance(term, URIRef):
                used.add(str(term))
            elif isinstance(term, Literal) and term.datatype:
                used.add(str(term.datatype))

    unused = []
    for pfx, ns in sorted(declared.items()):
        if not any(iri.startswith(ns) for iri in used):
            unused.append(f"{pfx or '(default)'}: <{ns}>")
    return unused


def find_unused_imports(graph) -> list[str]:
    """
    owl:imports of a module whose terms the file never references.

    Redundant rather than wrong, but it overstates the dependency: a consumer
    reading the header cannot tell which imports the module actually needs.
    """
    unused = []
    for imported in sorted(graph.objects(None, OWL.imports)):
        prefix = str(imported) + "#"
        referenced = any(
            isinstance(t, URIRef) and str(t).startswith(prefix)
            for triple in graph for t in triple
        )
        if not referenced:
            unused.append(str(imported))
    return unused


def _escape_cell(text) -> str:
    """Make a finding safe inside a Markdown table cell.

    An IRI written in angle brackets would be taken as an HTML tag and swallowed, a pipe would end the cell, and a
    newline would end the row.
    """
    return html.escape(" ".join(str(text).split()), quote=False).replace("|", "&#124;")


def _findings_cell(errors: list[str], warnings: list[str], err_marker: str, warn_marker: str) -> str:
    """The expandable findings of one module, errors first (a <details> inside a cell must be on one line).

    It has a column of its own, left-aligned: the counts next to it are right-aligned numbers, and prose beside a
    number in the same right-aligned cell is hard to read. Empty when the module has no findings.
    """
    items = [(err_marker, e) for e in errors] + [(warn_marker, w) for w in warnings]
    if not items:
        return ""
    body = "<br>".join(f"{marker} {_escape_cell(text)}" for marker, text in items)
    return f"<details><summary>Show</summary>{body}</details>"


def write_json(results: list[tuple[str, list[str], list[str]]], out_path: Path) -> None:
    """The findings per module, for a later run to compare with (#311)."""
    data = [{"module": name, "errors": errs, "warnings": warns} for name, errs, warns in results]
    out_path.write_text(json.dumps(data, indent=1), encoding="utf-8")


def read_base_findings(path: Path) -> dict[str, tuple[list[str], list[str]]] | None:
    """The base branch's findings written by `--json`, or None when there are none to read."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {row["module"]: (list(row["errors"]), list(row["warnings"])) for row in data}
    except (OSError, ValueError, KeyError, TypeError):
        return None


def base_for(module: str, base: dict, renames: dict) -> tuple[list[str], list[str]] | None:
    """The base findings of `module`, or of the module it replaced (#171, #281) with its names rewritten; None for a new module."""
    if module in base:
        return base[module]
    old = module_renames.predecessor(renames, module)
    if old is None or old not in base:
        return None
    rename = lambda text: re.sub(rf"\b{re.escape(old)}\b", module, module_renames.rewrite_text(text, renames))
    errs, warns = base[old]
    return [rename(e) for e in errs], [rename(w) for w in warns]


def write_markdown(results: list[tuple[str, list[str], list[str]]], out_path: Path,
                   base: dict[str, tuple[list[str], list[str]]] | None = None, renames: dict | None = None,
                   base_missing: bool = False) -> None:
    """
    Render this script's findings as a markdown section for the PR comment.

    Every check in this script surfaces here automatically: the table is built
    from the errors/warnings each check appends, so adding a check needs no change
    to this function or to the workflow that embeds it. See AGENTS.md, "Adding a
    quality check". The findings of a module sit in its own row, in a column of
    their own that expands in place, so a reader never has to match a count to a
    list further down.

    With the base branch's findings (`base`, #311) the table shows only what the pull request changed: a module has a row
    when its findings differ from the base or it has an error (errors block), and the warnings it did not change go
    into one collapsed backlog block. `base_missing` says the comparison was asked for but did not run.
    """
    if base is not None:
        out_path.write_text(_markdown_against_base(results, base, renames or {}), encoding="utf-8")
        return
    OK, WARN, ERR = "\u2705", "\u26a0\ufe0f", "\u26d4"
    lines = ["### Important checks", ""]
    if base_missing:
        lines += ["The comparison with the base branch did not run, so every module is listed.", ""]
    total_err = sum(len(e) for _, e, _ in results)
    total_warn = sum(len(w) for _, _, w in results)

    if not total_err and not total_warn:
        lines += [OK + " All %d module(s) pass: parse, circular-subclass, version "
                  "consistency, and term descriptions." % len(results), ""]
    else:
        lines += ["| Module | Errors | Warnings | Findings |", "|---|--:|--:|:--|"]
        for name, errs, warns in results:
            mark = ERR if errs else (WARN if warns else OK)
            # a non-breaking space keeps the status icon with the module name when a wide Findings cell squeezes this column
            lines.append("| %s&nbsp;`%s` | %d | %d | %s |" % (mark, name, len(errs), len(warns), _findings_cell(errs, warns, ERR, WARN)))
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")


def _markdown_against_base(results, base, renames) -> str:
    """The Important checks section of `write_markdown` when the base branch's findings are known (#311)."""
    OK, WARN, ERR, NEW, DONE = "✅", "⚠️", "⛔", "\U0001f195", "✔️"
    rows, backlog = [], []
    for name, errs, warns in results:
        before = base_for(name, base, renames)
        b_errs, b_warns = before if before is not None else ([], [])
        new_warns = [w for w in warns if w not in b_warns]
        resolved = [x for x in b_errs + b_warns if x not in errs + warns]
        kept = [w for w in warns if w in b_warns]
        if kept:
            backlog.append((name, kept))
        if not errs and not new_warns and not resolved:
            continue
        count = lambda now, was: str(now) if now == was else f"{was} → {now}"
        items = ([f"{ERR}{' ' + NEW if e not in b_errs else ''} {_escape_cell(e)}" for e in errs]
                 + [f"{WARN} {NEW} {_escape_cell(w)}" for w in new_warns]
                 + [f"{DONE} resolved: {_escape_cell(x)}" for x in resolved])
        if kept:
            items.append(f"and {len(kept)} unchanged warning(s), in the backlog below")
        mark = ERR if errs else (WARN if new_warns else OK)
        rows.append("| %s&nbsp;`%s` | %s | %s | <details><summary>Show</summary>%s</details> |"
                    % (mark, name, count(len(errs), len(b_errs)), count(len(warns), len(b_warns)), "<br>".join(items)))

    lines = ["### Important checks", ""]
    if rows:
        lines += ["Only what this pull request changed, and every error.", "",
                  "| Module | Errors | Warnings | Findings |", "|---|--:|--:|:--|", *rows, ""]
    else:
        lines += [OK + " This pull request changes no finding, and there is no error.", ""]
    if backlog:
        total = sum(len(kept) for _, kept in backlog)
        lines += [f"<details><summary>Backlog, unchanged by this pull request: {total} warning(s) in {len(backlog)} "
                  "module(s)</summary>", "", "| Module | Warnings | Findings |", "|---|--:|:--|"]
        lines += ["| %s&nbsp;`%s` | %d | %s |" % (WARN, name, len(kept), _findings_cell([], kept, ERR, WARN))
                  for name, kept in backlog]
        lines += ["", "</details>", ""]
    return "\n".join(lines)


def main():
    """Main function to validate ontology files."""
    repo_root = Path(__file__).parent.parent
    ttl_files = []

    # --markdown <path> emits a PR-comment section alongside the console output.
    argv = sys.argv[1:]
    # --json <path> writes the findings per module; --base-findings <path> reads the base branch's, so the markdown
    # shows only what changed (#311).
    def option(flag):
        if flag not in argv:
            return None
        i = argv.index(flag)
        value = Path(argv[i + 1])
        del argv[i:i + 2]
        return value

    markdown_path = option("--markdown")
    json_path = option("--json")
    base_path = option("--base-findings")
    sys.argv = [sys.argv[0]] + argv

    if len(sys.argv) < 2:
        # If no files specified, validate all .ttl files in the src directory
        print("No files specified. Validating all .ttl files in src/ directory...")
        src_dir = repo_root / "src"
        if src_dir.exists():
            ttl_files = list(src_dir.glob("*.ttl"))
        else:
            ttl_files = []
        if not ttl_files:
            print("No ontology files found (*.ttl) in src/ directory.", file=sys.stderr)
            print("Usage: python validate_ontology.py <ttl_file> [<ttl_file> ...]")
            sys.exit(1)
    else:
        # Validate specified files
        for ttl_path_str in sys.argv[1:]:
            ttl_file = Path(ttl_path_str)
            if not ttl_file.is_absolute():
                ttl_file = repo_root / ttl_file
            ttl_files.append(ttl_file)
    
    all_valid = True
    results: list[tuple[str, list[str], list[str]]] = []

    for ttl_file in ttl_files:
        if not ttl_file.exists():
            print(f"Error: File not found: {ttl_file}", file=sys.stderr)
            all_valid = False
            continue
        
        print(f"Validating {ttl_file.name}...")
        is_valid, errors, warnings = validate_ontology(ttl_file)

        if is_valid:
            print(f"  [OK] {ttl_file.name} is valid")
        else:
            print(f"  [ERROR] {ttl_file.name} has errors:")
            for error in errors:
                print(f"    • {error}")
            all_valid = False

        for warning in warnings:
            print(f"  [WARN] {warning}")

        results.append((ttl_file.stem, errors, warnings))

    # PR-time changelog check (#105). Needs the PR's base ref (BASE_REF, e.g. origin/main); without it
    # (local runs, the deploy workflow) the check is skipped. Advisory until ENFORCE_CHANGELOG=1.
    base_ref = os.environ.get("BASE_REF")
    if base_ref:
        changed = changed_paths_vs_base(base_ref, repo_root)
        enforce = os.environ.get("ENFORCE_CHANGELOG") == "1"
        if changed is None:
            # Surface it in the results (and so the PR comment), and do not fail open under enforcement.
            msg = f"could not diff against {base_ref}, so the changelog check did not run"
            results.append(("changelog check", [msg] if enforce else [], [] if enforce else [msg]))
            print(f"  [{'ERROR' if enforce else 'WARN'}] {msg}")
            all_valid = all_valid and not enforce
        else:
            for module in missing_changelog_modules(changed, repo_root):
                msg = (f"changelogs/{module}.md was not changed, but src/{module}.ttl was: add an entry under "
                       "[Unreleased] (it becomes the release notes)")
                row = next((r for r in results if r[0] == module), None)
                if row is None:
                    row = (module, [], [])
                    results.append(row)
                (row[1] if enforce else row[2]).append(msg)
                print(f"  [{'ERROR' if enforce else 'WARN'}] {module}: {msg}")
                all_valid = all_valid and not enforce

    # Public-repository guard (#89): hand-written files must not name an internal tool.
    leaks = find_internal_names(repo_root)
    results.append(("public-repo names", leaks, []))
    for leak in leaks:
        print(f"  [ERROR] {leak}")
    all_valid = all_valid and not leaks

    # Whole-repository budget for the example images (#145).
    budget_errors, budget_warnings = example_images.messages(example_images.budget_findings(repo_root), "assets")
    if budget_errors or budget_warnings:
        results.append(("example image budget", budget_errors, budget_warnings))
        for msg in budget_errors:
            print(f"  [ERROR] {msg}")
        for msg in budget_warnings:
            print(f"  [WARN] {msg}")
        all_valid = all_valid and not budget_errors

    if json_path is not None:
        write_json(results, json_path)
        print(f"Wrote the findings to {json_path}")
    if markdown_path is not None:
        base = read_base_findings(base_path) if base_path is not None else None
        write_markdown(results, markdown_path, base=base, renames=module_renames.load(repo_root),
                       base_missing=base_path is not None and base is None)
        print(f"Wrote markdown summary to {markdown_path}")

    if not all_valid:
        sys.exit(1)


if __name__ == "__main__":
    main()
