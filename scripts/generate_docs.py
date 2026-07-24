#!/usr/bin/env python3
"""
Generate HTML documentation for all TTL ontology files in the repository root.

This script discovers all .ttl files in the root directory and uses pyLODE
to generate HTML documentation for each one.
"""

import sys
import shutil
import re
from pathlib import Path
from pylode.profiles.ontpub import OntPub
from rdflib import Graph
from rdflib.namespace import RDF, RDFS, OWL
from rdflib.namespace import split_uri

# ttl2md is a self-contained package that lives in this repository (see the
# ttl2md/ folder) and is intended to be published separately later. Import it
# directly from its source tree so the docs pipeline works without a separate
# install step. The src path is prepended so the real package wins over the
# repo-root ttl2md/ directory (which would otherwise resolve as an empty
# namespace package).
_TTL2MD_SRC = Path(__file__).parent.parent / "ttl2md" / "src"
if _TTL2MD_SRC.exists() and str(_TTL2MD_SRC) not in sys.path:
    sys.path.insert(0, str(_TTL2MD_SRC))
import ttl2md


def find_ttl_files(root_dir: Path) -> list[Path]:
    """Find all .ttl files in the src directory."""
    src_dir = root_dir / "src"
    if not src_dir.exists():
        return []
    ttl_files = list(src_dir.glob("*.ttl"))
    return sorted(ttl_files)


def sort_by_dependency(ttl_files: list[Path]) -> list[Path]:
    """
    Sort ontology files by their dependency hierarchy.
    
    Order:
    1. Drawing Metadata (no ADIRO imports - core merged into it)
    2. Common Symbols (imports Drawing Metadata)
    3. Domain-common (imports Drawing Metadata + Common Symbols)
    4. Facade Domain (imports Drawing Metadata + Common Symbols + Domain-common)
    5. Drawing Ontology (monolith, last)
    
    Args:
        ttl_files: List of TTL file paths
        
    Returns:
        List of TTL files sorted by dependency order
    """
    # Define dependency order (lower number = fewer dependencies)
    dependency_order = {
        'aec_drawing_metadata': 1,
        'aec_common_symbols': 2,
        'aec_domain_common': 3,
        'aec_facade_domain': 4,
        'aec_drawing_ontology': 5,  # Monolith, put last
    }
    
    def get_order(file_path: Path) -> int:
        """Get the dependency order for a file."""
        stem = file_path.stem
        return dependency_order.get(stem, 999)  # Unknown files go to end
    
    return sorted(ttl_files, key=get_order)


def find_display_json_files(root_dir: Path) -> list[Path]:
    """Find all .display.json files in the src directory."""
    src_dir = root_dir / "src"
    if not src_dir.exists():
        return []
    display_json_files = list(src_dir.glob("*.display.json"))
    return sorted(display_json_files)


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

        # Post-process HTML to render example images inline (if present)
        inject_example_images(ttl_file=ttl_file, html_file=output_file)
        
        print(f"  [OK] Generated: {output_file}")
        
        # Copy the TTL file to the docs directory
        ttl_output = output_dir / ttl_file.name
        shutil.copy2(ttl_file, ttl_output)
        print(f"  [OK] Copied TTL: {ttl_output}")
        
        return True
        
    except Exception as e:
        print(f"  [ERROR] Error processing {ttl_file.name}: {e}", file=sys.stderr)
        return False


def _local_name(term_iri: str) -> str | None:
    """Extract a local name from an IRI for matching HTML entity IDs."""
    try:
        _, name = split_uri(term_iri)
        return name
    except Exception:
        # Fallback for unusual IRIs
        if "#" in term_iri:
            return term_iri.rsplit("#", 1)[-1] or None
        if "/" in term_iri:
            return term_iri.rsplit("/", 1)[-1] or None
        return None


def _is_example_image_predicate(predicate_iri: str) -> bool:
    name = _local_name(predicate_iri)
    return (name or "").lower() == "exampleimage"


def inject_example_images(ttl_file: Path, html_file: Path) -> None:
    """Inject inline image previews for any :exampleImage annotations found in ttl_file.

    pyLODE documents the annotation property itself, but it doesn't include
    per-entity annotation values in the entity tables. This function adds an
    'Example image' row to the relevant entity tables.
    """

    graph = Graph()
    graph.parse(str(ttl_file), format="turtle")

    # Find the exampleImage predicate(s) in this graph (namespace varies per ontology)
    example_predicates = {
        p for p in set(graph.predicates()) if _is_example_image_predicate(str(p))
    }
    if not example_predicates:
        return

    # Collect example images for OWL/RDFS classes
    images_by_entity: dict[str, list[str]] = {}
    class_subjects = set(graph.subjects(RDF.type, OWL.Class)) | set(
        graph.subjects(RDF.type, RDFS.Class)
    )

    for subj in class_subjects:
        subj_name = _local_name(str(subj))
        if not subj_name:
            continue

        image_iris: list[str] = []
        for pred in example_predicates:
            for _, _, obj in graph.triples((subj, pred, None)):
                if obj is None:
                    continue
                obj_str = str(obj).strip()
                if not obj_str:
                    continue
                image_iris.append(obj_str)

        if image_iris:
            # Preserve order while deduplicating
            deduped: list[str] = []
            seen: set[str] = set()
            for iri in image_iris:
                if iri not in seen:
                    deduped.append(iri)
                    seen.add(iri)
            images_by_entity[subj_name] = deduped

    if not images_by_entity:
        return

    html = html_file.read_text(encoding="utf-8")

    # Insert a new table row inside each matching entity div
    for entity_id, image_iris in images_by_entity.items():
        div_marker = f'<div class="property entity" id="{entity_id}">'
        div_start = html.find(div_marker)
        if div_start == -1:
            continue

        table_end = html.find("</table>", div_start)
        if table_end == -1:
            continue

        # Avoid duplicate injection if docs are regenerated without a clean workspace
        existing_slice = html[div_start:table_end]
        if re.search(r">\s*Example image\s*<", existing_slice, flags=re.IGNORECASE):
            continue

        items_html: list[str] = []
        for iri in image_iris:
            # Show as link + inline preview. Keep styling minimal and consistent.
            safe_iri = iri.replace('"', "%22")
            items_html.append(
                "<div>\n"
                f"  <a href=\"{safe_iri}\" target=\"_blank\" rel=\"noopener noreferrer\"><code>{iri}</code></a><br>\n"
                f"  <img src=\"{safe_iri}\" alt=\"Example image for {entity_id}\" style=\"max-width: 500px;\">\n"
                "</div>"
            )

        row_html = (
            "\n            <tr>\n"
            "              <th>\n"
            "                <a class=\"hover_property\" href=\"#exampleimage\" title=\"Links a class or concept to an example image illustrating it.\">Example image</a>\n"
            "              </th>\n"
            f"              <td>{''.join(items_html)}</td>\n"
            "            </tr>\n"
        )

        html = html[:table_end] + row_html + html[table_end:]

    html_file.write_text(html, encoding="utf-8")


def extract_ontology_comment(ttl_file: Path) -> str:
    """
    Extract the rdfs:comment from the ontology declaration in a TTL file.
    
    Args:
        ttl_file: Path to the TTL file
        
    Returns:
        The comment string, or empty string if not found
    """
    try:
        graph = Graph()
        graph.parse(str(ttl_file), format="turtle")
        
        # Find the ontology declaration
        ontologies = list(graph.subjects(RDF.type, OWL.Ontology))
        if not ontologies:
            return ""
        
        ontology = ontologies[0]
        
        # Get the rdfs:comment
        comments = list(graph.objects(ontology, RDFS.comment))
        if comments:
            # Return the first comment, converting to string
            comment = str(comments[0])
            # Remove language tags if present (e.g., "text"@en -> "text")
            if '@' in comment:
                comment = comment.split('@')[0]
            return comment.strip('"')
        
        return ""
    except Exception:
        return ""


def extract_adiro_dependencies(ttl_file: Path) -> list[str]:
    """
    Extract ADIRO ontology dependencies from owl:imports statements.
    
    Args:
        ttl_file: Path to the TTL file
        
    Returns:
        List of dependency names (e.g., ['aec-core', 'aec-drawing-metadata'])
    """
    try:
        graph = Graph()
        graph.parse(str(ttl_file), format="turtle")
        
        # Find the ontology declaration
        ontologies = list(graph.subjects(RDF.type, OWL.Ontology))
        if not ontologies:
            return []
        
        ontology = ontologies[0]
        
        # Get all owl:imports
        imports = list(graph.objects(ontology, OWL.imports))
        
        # Filter for ADIRO imports and extract the ontology name
        adiro_base = "https://burohappoldmachinelearning.github.io/ADIRO/"
        dependencies = []
        
        for imp in imports:
            imp_str = str(imp)
            if imp_str.startswith(adiro_base):
                # Extract ontology name (e.g., "aec-core" from full IRI)
                dep_name = imp_str.replace(adiro_base, "").split("/")[0]
                dependencies.append(dep_name)
        
        return sorted(dependencies)  # Sort for consistent display
        
    except Exception:
        return []


# Base URL of the published GitHub Pages site. Used to build absolute links for
# external tools (e.g. OntoCanvas) that need the full URL of an ontology page.
SITE_BASE_URL = "https://burohappoldmachinelearning.github.io/ADIRO"

# OntoCanvas branding icon, reused from the previous HTML landing page.
ONTOCANVAS_ICON_URL = "https://raw.githubusercontent.com/alelom/OntoCanvas/main/OntoCanvas.png"


def generate_index(ttl_files: list[Path], output_dir: Path) -> None:
    """
    Generate the Material for MkDocs landing page (``index.md``).

    The page replicates the previous standalone ``index.html`` landing page: an
    intro, links to the Use Cases and ORSD documentation, and a card grid of the
    available ontologies (each linking to its pyLODE HTML page, its source TTL,
    and OntoCanvas). The list of ontologies is generated automatically from the
    TTL files so newly added ontologies appear without manual edits.

    Args:
        ttl_files: List of TTL files that were processed
        output_dir: Directory where the MkDocs source lives (docs/)
    """
    index_file = output_dir / "index.md"

    lines: list[str] = []
    lines.append("# ADIRO Ontologies Documentation")
    lines.append("")
    lines.append('![ADIRO](img/adiro_banner.png){ .adiro-banner }')
    lines.append("")
    lines.append(
        "ADIRO (*AEC Drawing Information Representation Ontologies*) is a set of "
        "ontologies for AEC (*Architecture, Engineering, and Construction*) drawing "
        "representation, designed to support machine learning tasks, in particular "
        "information extraction workflows."
    )
    lines.append("")
    lines.append(
        "The ontologies include concepts for drawing metadata, common symbols, "
        "domain-common symbols, and domain-specific symbols. They can be used to "
        "represent the information in AEC drawings, to make them machine-readable, "
        "and to support the creation of graph databases and knowledge graphs."
    )
    lines.append("")
    lines.append(
        "[:fontawesome-brands-github: View on GitHub]"
        "(https://github.com/BuroHappoldMachineLearning/ADIRO){ .md-button }"
    )
    lines.append("")

    # Documentation sections (Use Cases + ORSD)
    lines.append("## Documentation")
    lines.append("")
    lines.append('<div class="grid cards" markdown>')
    lines.append("")
    lines.append("-   :material-file-document-check-outline: __Ontology Requirements (ORSD)__")
    lines.append("")
    lines.append(
        "    Ontology Requirements Specification Document: purpose, scope, intended "
        "users and uses, and the functional/non-functional requirements."
    )
    lines.append("")
    lines.append("    [:octicons-arrow-right-24: ORSD](ORSD_v1.md)")
    lines.append("")
    lines.append("-   :material-clipboard-list-outline: __Use Cases__")
    lines.append("")
    lines.append(
        "    Use case catalogue (UC-01 through UC-07), prioritization matrix, and "
        "current ORSD status across all use cases."
    )
    lines.append("")
    lines.append("    [:octicons-arrow-right-24: Use Cases](uc-orsd/README.md)")
    lines.append("")
    lines.append("</div>")
    lines.append("")

    # Available ontologies
    lines.append("## Available Ontologies")
    lines.append("")
    lines.append('<div class="grid cards" markdown>')
    lines.append("")

    for ttl_file in ttl_files:
        html_filename = f"{ttl_file.stem}.html"
        ttl_filename = ttl_file.name
        title = ttl_file.stem.replace("_", " ").title()
        comment = extract_ontology_comment(ttl_file)
        dependencies = extract_adiro_dependencies(ttl_file)
        ontocanvas_url = f"https://alelom.github.io/OntoCanvas/?onto={SITE_BASE_URL}/{html_filename}"

        lines.append(f"-   ### [{title}]({html_filename})")
        lines.append("")
        if comment:
            lines.append(f"    {comment}")
            lines.append("")
        if dependencies:
            deps_text = ", ".join(dependencies)
            lines.append(f"    *Imports: {deps_text}*")
            lines.append("")
        lines.append(f"    Source: [`{ttl_filename}`]({ttl_filename})")
        lines.append("")
        lines.append(
            f"    [![OntoCanvas]({ONTOCANVAS_ICON_URL}){{ .ontocanvas-icon }} Open in OntoCanvas]"
            f"({ontocanvas_url}){{ .md-button target=_blank }}"
        )
        lines.append("")

    lines.append("</div>")
    lines.append("")

    index_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"  [OK] Generated index: {index_file}")


def build_dependency_mermaid(ttl_files: list[Path], highlight: str | None = None) -> list[str]:
    """Build a Mermaid flowchart of the owl:imports between ADIRO ontologies.

    Edges point from an ontology to the ontology it imports (i.e. depends on).
    When ``highlight`` (an ontology stem) is given, that node is styled as the
    "current" ontology, for use on the per-ontology sub-pages.
    """
    stems = [f.stem for f in ttl_files]
    titles = {f.stem: f.stem.replace("_", " ").title() for f in ttl_files}
    deps = {f.stem: extract_adiro_dependencies(f) for f in ttl_files}

    # Bottom-to-top layout: edges still read "imports" (importer --> imported),
    # but the imported base ontologies are drawn at the top and the leaf
    # ontologies (which import others but are imported by none) at the bottom.
    lines = ["```mermaid", "graph BT"]
    for stem in stems:
        lines.append(f'    {stem}["{titles[stem]}"]')
    for stem in stems:
        for imp in deps[stem]:
            if imp in titles:
                lines.append(f"    {stem} --> {imp}")
    if highlight and highlight in titles:
        lines.append(
            "    classDef highlight fill:#1e88e5,stroke:#0d47a1,"
            "stroke-width:3px,color:#ffffff;"
        )
        lines.append(f"    class {highlight} highlight;")
    lines.append("```")
    return lines


def generate_ontology_markdown_pages(ttl_files: list[Path], output_dir: Path) -> None:
    """Generate native Markdown pages for each ontology using ttl2md.

    These pages populate the "Ontologies" section of the MkDocs site: unlike the
    standalone pyLODE HTML pages (kept for the interactive/OntoCanvas view), they
    are themed by Material, indexed by the site search and get an in-page table
    of contents. Each page also links out to the pyLODE HTML, the TTL source and
    OntoCanvas.

    Example images (the ``:exampleImage`` annotations) are rendered inline by
    ttl2md, reproducing the behaviour of the pyLODE HTML post-processing.
    """
    ontologies_dir = output_dir / "ontologies"
    ontologies_dir.mkdir(parents=True, exist_ok=True)

    index_lines: list[str] = [
        "# Ontologies",
        "",
        "Reference documentation for each ADIRO ontology, generated from the "
        "Turtle sources. Each page also links to an interactive HTML view "
        "(pyLODE) and to OntoCanvas.",
        "",
        "## Dependencies",
        "",
        "The ADIRO ontologies are modular and build on one another via "
        "`owl:imports`. Arrows point from an ontology to the ontologies it "
        "imports.",
        "",
        *build_dependency_mermaid(ttl_files),
        "",
        "## Available ontologies",
        "",
        '<div class="grid cards" markdown>',
        "",
    ]

    for ttl_file in ttl_files:
        stem = ttl_file.stem
        title = stem.replace("_", " ").title()
        html_filename = f"{stem}.html"
        ontocanvas_url = (
            f"https://alelom.github.io/OntoCanvas/?onto={SITE_BASE_URL}/{html_filename}"
        )

        # Pages live in docs/ontologies/, one level below docs/img/, so relative
        # image references (if any) resolve via "../"; absolute image URLs (the
        # ADIRO case, resolved against @base) are left untouched by ttl2md.
        body = ttl2md.convert_file(ttl_file, title=title, asset_prefix="../")

        links_block = (
            f"[![OntoCanvas]({ONTOCANVAS_ICON_URL}){{ .ontocanvas-icon }} Open in OntoCanvas]"
            f"({ontocanvas_url}){{ .md-button target=_blank }}\n"
            f"[:material-file-document-outline: TTL source]({SITE_BASE_URL}/{ttl_file.name}){{ .md-button }}\n"
            f"[:material-file-code: pyLODE HTML]({SITE_BASE_URL}/{html_filename}){{ .md-button }}"
        )

        # Insert the links row directly under the H1 emitted by ttl2md.
        body_lines = body.splitlines()
        rest = body_lines[1:]
        while rest and rest[0] == "":
            rest.pop(0)

        # Insert a dependency diagram (with the current ontology highlighted)
        # after the ontology description/metadata and before the first term
        # section (## …).
        dep_section = [
            "## Dependencies",
            "",
            "Arrows point from an ontology to the ontologies it imports; the "
            "current ontology is highlighted.",
            "",
            *build_dependency_mermaid(ttl_files, highlight=stem),
            "",
        ]
        insert_at = next(
            (i for i, line in enumerate(rest) if line.startswith("## ")), len(rest)
        )
        rest = rest[:insert_at] + dep_section + rest[insert_at:]

        page = "\n".join([body_lines[0], "", links_block, ""] + rest).rstrip() + "\n"

        page_file = ontologies_dir / f"{stem}.md"
        page_file.write_text(page, encoding="utf-8")
        print(f"  [OK] Generated ontology page: {page_file}")

        comment = extract_ontology_comment(ttl_file)
        dependencies = extract_adiro_dependencies(ttl_file)
        index_lines.append(f"-   ### [{title}]({stem}.md)")
        index_lines.append("")
        if comment:
            index_lines.append(f"    {comment}")
            index_lines.append("")
        if dependencies:
            index_lines.append(f"    *Imports: {', '.join(dependencies)}*")
            index_lines.append("")

    index_lines.append("</div>")
    index_lines.append("")

    index_file = ontologies_dir / "index.md"
    index_file.write_text("\n".join(index_lines), encoding="utf-8")
    print(f"  [OK] Generated ontologies index: {index_file}")


def main():
    """Main function to generate documentation for all TTL files."""
    # Get repository root (parent of scripts directory)
    repo_root = Path(__file__).parent.parent
    output_dir = repo_root / "docs"

    # Keep docs/img in sync with src/images for GitHub Pages publishing
    src_images_dir = repo_root / "src" / "images"
    docs_img_dir = output_dir / "img"
    if src_images_dir.exists():
        docs_img_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_images_dir, docs_img_dir, dirs_exist_ok=True)
    
    print(f"Scanning for TTL files in: {repo_root}")
    
    # Find all TTL files in root
    ttl_files = find_ttl_files(repo_root)
    # Sort by dependency order
    ttl_files = sort_by_dependency(ttl_files)
    display_json_files = find_display_json_files(repo_root)
    
    if not ttl_files:
        print("No TTL files found in repository root.")
        sys.exit(1)
    
    print(f"Found {len(ttl_files)} TTL file(s):")
    for ttl_file in ttl_files:
        print(f"  - {ttl_file.name}")

    print(f"Found {len(display_json_files)} display JSON file(s):")
    for display_json_file in display_json_files:
        print(f"  - {display_json_file.name}")
    
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

    # Generate native Markdown ontology pages (Ontologies nav section)
    generate_ontology_markdown_pages(ttl_files, output_dir)

    # Copy all .display.json files to docs directory for GitHub Pages publishing
    for display_json_file in display_json_files:
        display_json_output = output_dir / display_json_file.name
        shutil.copy2(display_json_file, display_json_output)
        print(f"  [OK] Copied display JSON: {display_json_output}")
    
    print("-" * 60)
    print(f"Documentation generation complete: {success_count}/{len(ttl_files)} files processed successfully.")
    
    if success_count < len(ttl_files):
        sys.exit(1)


if __name__ == "__main__":
    main()
