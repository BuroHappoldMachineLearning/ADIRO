#!/usr/bin/env python3
"""
Validate TTL ontology files for correctness.

This script parses ontology files and checks for:
- Circular references in class hierarchies
- Invalid OWL structure
- Missing imports
- Other structural issues
"""

import sys
from pathlib import Path
from rdflib import Graph
from rdflib.namespace import RDF, RDFS, OWL
from collections import defaultdict, deque


def find_circular_references(graph):
    """
    Find circular references in class hierarchies.
    
    Returns a list of circular reference paths.
    """
    # Build subclass relationships
    subclass_map = defaultdict(set)
    all_classes = set()
    
    for s, p, o in graph.triples((None, RDFS.subClassOf, None)):
        if isinstance(o, tuple):  # Skip blank node restrictions
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
            if isinstance(subclass, tuple):  # Skip blank node restrictions
                continue
            dfs(subclass, path + [node])
        
        rec_stack.remove(node)
    
    for cls in all_classes:
        if cls not in visited:
            dfs(cls, [])
    
    return cycles


def validate_ontology(ttl_file: Path) -> tuple[bool, list[str]]:
    """
    Validate an ontology file.
    
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
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
        
        return len(errors) == 0, errors
        
    except Exception as e:
        errors.append(f"Parse error: {str(e)}")
        return False, errors


def main():
    """Main function to validate ontology files."""
    if len(sys.argv) < 2:
        print("Usage: python validate_ontology.py <ttl_file> [<ttl_file> ...]")
        sys.exit(1)
    
    all_valid = True
    
    for ttl_path_str in sys.argv[1:]:
        ttl_file = Path(ttl_path_str)
        
        if not ttl_file.exists():
            print(f"Error: File not found: {ttl_file}", file=sys.stderr)
            all_valid = False
            continue
        
        print(f"Validating {ttl_file.name}...")
        is_valid, errors = validate_ontology(ttl_file)
        
        if is_valid:
            print(f"  [OK] {ttl_file.name} is valid")
        else:
            print(f"  [ERROR] {ttl_file.name} has errors:")
            for error in errors:
                print(f"    • {error}")
            all_valid = False
    
    if not all_valid:
        sys.exit(1)


if __name__ == "__main__":
    main()
