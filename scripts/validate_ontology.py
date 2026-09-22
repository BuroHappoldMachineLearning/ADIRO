#!/usr/bin/env python3
"""
Validate TTL ontology files for correctness.

This script parses ontology files and checks for:
- Circular references in class hierarchies
- Invalid OWL structure
- Missing imports
- Other structural issues
"""

import os
import sys
from pathlib import Path
from rdflib import Graph, URIRef
from rdflib.namespace import RDF, RDFS, OWL, SKOS, DCTERMS
from rdflib.term import BNode
from collections import defaultdict, deque


# Every ADIRO term must carry a human-readable description. ADIRO's definition
# vocabulary is rdfs:comment - NOT the OBO convention IAO:0000115 that ROBOT's
# built-in `missing_definition` rule looks for. See
# docs/design-decisions/usage-of-annotation-properties.md for why.
#
# skos:definition and dcterms:description are accepted too: those are the other
# properties pyLODE normalises into a rendered description, so a term carrying
# one of them still documents itself on the published site.
ADIRO_NS = "https://w3id.org/adiro/"
DESCRIPTION_PROPS = (RDFS.comment, SKOS.definition, DCTERMS.description)
TERM_TYPES = (OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty,
              OWL.AnnotationProperty, OWL.NamedIndividual)


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


def find_undescribed_terms(graph) -> list[str]:
    """
    ADIRO-namespace terms with no human-readable description.

    Terms from other namespaces are exempt by design: an external term declared
    as a local stub is a name, not a definition - the definition lives at the
    source, which is what its rdfs:isDefinedBy points at. Describing it here
    would be asserting someone else's definition.
    """
    undescribed = []
    for term_type in TERM_TYPES:
        for term in graph.subjects(RDF.type, term_type):
            if not isinstance(term, URIRef) or not str(term).startswith(ADIRO_NS):
                continue
            if any((term, prop, None) in graph for prop in DESCRIPTION_PROPS):
                continue
            label = graph.value(term, RDFS.label)
            name = str(term).split("#")[-1]
            undescribed.append(f"{name} ({label})" if label else name)
    return sorted(set(undescribed))


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

        # Every ADIRO term needs a human-readable description (#87).
        # Advisory by default so the existing backlog does not block CI; set
        # ENFORCE_DESCRIPTIONS=1 to promote it to an error once that backlog is
        # cleared, which is the point at which this becomes a real gate.
        undescribed = find_undescribed_terms(graph)
        if undescribed:
            head = ", ".join(undescribed[:8])
            more = f" ... and {len(undescribed) - 8} more" if len(undescribed) > 8 else ""
            msg = (f"{len(undescribed)} term(s) have no rdfs:comment "
                   f"(nor skos:definition / dcterms:description): {head}{more}")
            if os.environ.get("ENFORCE_DESCRIPTIONS") == "1":
                errors.append(msg)
            else:
                warnings.append(msg)
                if os.environ.get("LIST_UNDESCRIBED") == "1":
                    warnings.extend(f"  undescribed: {t}" for t in undescribed)

        return len(errors) == 0, errors, warnings

    except Exception as e:
        errors.append(f"Parse error: {str(e)}")
        return False, errors, []


def write_markdown(results: list[tuple[str, list[str], list[str]]], out_path: Path) -> None:
    """
    Render this script's findings as a markdown section for the PR comment.

    Every check in this script surfaces here automatically: the table is built
    from the errors/warnings each check appends, so adding a check needs no change
    to this function or to the workflow that embeds it. See AGENTS.md, "Adding a
    quality check".
    """
    OK, WARN, ERR = "\u2705", "\u26a0\ufe0f", "\u26d4"
    lines = ["### \U0001f9ea Repo-specific checks (`scripts/validate_ontology.py`)", ""]
    total_err = sum(len(e) for _, e, _ in results)
    total_warn = sum(len(w) for _, _, w in results)

    if not total_err and not total_warn:
        lines += [OK + " All %d module(s) pass: parse, circular-subclass, version "
                  "consistency, and term descriptions." % len(results), ""]
    else:
        lines += ["| Module | Errors | Warnings |", "|---|--:|--:|"]
        for name, errs, warns in results:
            mark = ERR if errs else (WARN if warns else OK)
            lines.append("| %s `%s` | %d | %d |" % (mark, name, len(errs), len(warns)))
        lines += ["", "**%d error(s), %d warning(s).** Errors block; warnings are advisory."
                  % (total_err, total_warn), ""]
        lines += ["<details><summary>Details</summary>", ""]
        for name, errs, warns in results:
            if not errs and not warns:
                continue
            lines.append("**`%s`**" % name)
            lines += ["- " + ERR + " " + e for e in errs]
            lines += ["- " + WARN + " " + w for w in warns]
            lines.append("")
        lines += ["</details>", ""]

    out_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    """Main function to validate ontology files."""
    repo_root = Path(__file__).parent.parent
    ttl_files = []

    # --markdown <path> emits a PR-comment section alongside the console output.
    argv = sys.argv[1:]
    markdown_path = None
    if "--markdown" in argv:
        i = argv.index("--markdown")
        markdown_path = Path(argv[i + 1])
        del argv[i:i + 2]
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

    if markdown_path is not None:
        write_markdown(results, markdown_path)
        print(f"Wrote markdown summary to {markdown_path}")

    if not all_valid:
        sys.exit(1)


if __name__ == "__main__":
    main()
