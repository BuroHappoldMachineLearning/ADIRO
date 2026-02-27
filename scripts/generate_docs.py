#!/usr/bin/env python3
"""
Generate HTML documentation for all TTL ontology files in the repository root.

This script discovers all .ttl files in the root directory and uses pyLODE
to generate HTML documentation for each one.
"""

import sys
import shutil
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
        
        # Copy the TTL file to the docs directory
        ttl_output = output_dir / ttl_file.name
        shutil.copy2(ttl_file, ttl_output)
        print(f"  ✓ Copied TTL: {ttl_output}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error processing {ttl_file.name}: {e}", file=sys.stderr)
        return False


def generate_index(ttl_files: list[Path], output_dir: Path) -> None:
    """
    Generate an index.html file that lists all generated documentation.
    
    Args:
        ttl_files: List of TTL files that were processed
        output_dir: Directory where HTML files are located
    """
    index_file = output_dir / "index.html"
    
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ADIRO Ontology Documentation</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            background-color: #f5f5f5;
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #007acc;
            padding-bottom: 0.5rem;
        }
        .intro {
            background-color: white;
            padding: 1.5rem;
            border-radius: 8px;
            margin-bottom: 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .ontology-list {
            list-style: none;
            padding: 0;
        }
        .ontology-list li {
            background-color: white;
            margin-bottom: 1rem;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .ontology-list li:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        .ontology-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
        }
        .ontology-link-container {
            flex: 1;
        }
        .ontology-list a {
            text-decoration: none;
            color: #007acc;
            font-weight: 500;
            font-size: 1.1rem;
        }
        .ontology-list a:hover {
            text-decoration: underline;
        }
        .file-name {
            color: #666;
            font-size: 0.9rem;
            margin-top: 0.5rem;
        }
        .ontocanvas-button {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            background-color: #007acc;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-size: 0.9rem;
            font-weight: 500;
            transition: background-color 0.2s, transform 0.2s;
            white-space: nowrap;
        }
        .ontocanvas-button:hover {
            background-color: #005a9e;
            transform: translateY(-1px);
            text-decoration: none;
            color: white;
        }
        .ontocanvas-button:active {
            transform: translateY(0);
        }
        .ontocanvas-icon {
            width: 20px;
            height: 20px;
            vertical-align: middle;
        }
        footer {
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #666;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <h1>ADIRO Ontology Documentation</h1>
    
    <div class="intro">
        <p>This site contains automatically generated HTML documentation for all ontology files in the ADIRO repository.</p>
        <p>Documentation is generated using <a href="https://github.com/RDFLib/pyLODE" target="_blank">pyLODE</a> and updated automatically when changes are pushed to the repository.</p>
    </div>
    
    <h2>Available Ontologies</h2>
    <ul class="ontology-list">
"""
    
    for ttl_file in ttl_files:
        html_filename = f"{ttl_file.stem}.html"
        html_content += f"""        <li>
            <div class="ontology-item">
                <div class="ontology-link-container">
                    <a href="{html_filename}">{ttl_file.stem.replace('_', ' ').title()}</a>
                    <div class="file-name">Source: {ttl_file.name}</div>
                </div>
                <a href="#" class="ontocanvas-button" data-ontology="{html_filename}" target="_blank">
                    <img src="https://raw.githubusercontent.com/alelom/OntoCanvas/main/OntoCanvas.png" alt="OntoCanvas" class="ontocanvas-icon">
                    Open in OntoCanvas
                </a>
            </div>
        </li>
"""
    
    html_content += """    </ul>
    
    <footer>
        <p>Generated automatically by <a href="https://github.com/RDFLib/pyLODE" target="_blank">pyLODE</a></p>
    </footer>
    
    <script>
        // Set up OntoCanvas button links
        document.addEventListener('DOMContentLoaded', function() {
            const buttons = document.querySelectorAll('.ontocanvas-button');
            buttons.forEach(function(button) {
                const ontologyFile = button.getAttribute('data-ontology');
                // Construct full URL to the ontology HTML file
                const baseUrl = window.location.origin + window.location.pathname.replace(/\/[^\/]*$/, '');
                const ontologyUrl = baseUrl + '/' + ontologyFile;
                const ontocanvasUrl = 'https://alelom.github.io/OntoCanvas/?onto=' + encodeURIComponent(ontologyUrl);
                button.setAttribute('href', ontocanvasUrl);
            });
        });
    </script>
</body>
</html>
"""
    
    index_file.write_text(html_content, encoding='utf-8')
    print(f"  ✓ Generated index: {index_file}")


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
    
    # Generate index.html
    print("-" * 60)
    generate_index(ttl_files, output_dir)
    
    print("-" * 60)
    print(f"Documentation generation complete: {success_count}/{len(ttl_files)} files processed successfully.")
    
    if success_count < len(ttl_files):
        sys.exit(1)


if __name__ == "__main__":
    main()
