#!/usr/bin/env python3
"""
Generate HTML documentation for all TTL ontology files in the repository root.

This script discovers all .ttl files in the root directory and uses pyLODE
to generate HTML documentation for each one.
"""

import sys
from pathlib import Path
from pylode.profiles.ontpub import OntPub


def find_ttl_files(root_dir: Path) -> list[Path]:
    """Find all .ttl files in the root directory."""
    ttl_files = list(root_dir.glob("*.ttl"))
    return sorted(ttl_files)


def generate_documentation(ttl_file: Path, output_dir: Path) -> bool:
    """
    Generate HTML documentation for a TTL file using pyLODE.
    
    Args:
        ttl_file: Path to the input TTL file
        output_dir: Directory where HTML output should be saved
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate output filename (replace .ttl with .html)
        output_file = output_dir / f"{ttl_file.stem}.html"
        
        print(f"Generating documentation for {ttl_file.name}...")
        
        # Use pyLODE's OntPub profile to generate HTML
        od = OntPub(ontology=str(ttl_file))
        od.make_html(destination=str(output_file))
        
        print(f"  ✓ Generated: {output_file}")
        return True
        
    except Exception as e:
        print(f"  ✗ Error processing {ttl_file.name}: {e}", file=sys.stderr)
        return False


def main():
    """Main function to generate documentation for all TTL files."""
    # Get repository root (parent of scripts directory)
    repo_root = Path(__file__).parent.parent
    output_dir = repo_root / "docs"
    
    print(f"Scanning for TTL files in: {repo_root}")
    
    # Find all TTL files in root
    ttl_files = find_ttl_files(repo_root)
    
    if not ttl_files:
        print("No TTL files found in repository root.")
        sys.exit(1)
    
    print(f"Found {len(ttl_files)} TTL file(s):")
    for ttl_file in ttl_files:
        print(f"  - {ttl_file.name}")
    
    print(f"\nGenerating documentation to: {output_dir}")
    print("-" * 60)
    
    # Generate documentation for each file
    success_count = 0
    for ttl_file in ttl_files:
        if generate_documentation(ttl_file, output_dir):
            success_count += 1
    
    print("-" * 60)
    print(f"Documentation generation complete: {success_count}/{len(ttl_files)} files processed successfully.")
    
    if success_count < len(ttl_files):
        sys.exit(1)


if __name__ == "__main__":
    main()
