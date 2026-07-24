"""Command-line interface for ttl2md.

Usage::

    ttl2md input.ttl -o output.md
    ttl2md input.ttl --asset-prefix ../ --title "My Ontology"
    python -m ttl2md input.ttl        # prints to stdout
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .converter import convert_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ttl2md",
        description="Convert an OWL/RDFS ontology to Markdown documentation.",
    )
    parser.add_argument("input", type=Path, help="Path to the ontology file (.ttl, .owl, .rdf, …)")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output Markdown file. Prints to stdout if omitted.",
    )
    parser.add_argument(
        "-t",
        "--title",
        default=None,
        help="Override the page title (defaults to the ontology rdfs:label).",
    )
    parser.add_argument(
        "--asset-prefix",
        default="",
        help="Prefix prepended to relative image references (e.g. '../').",
    )
    parser.add_argument(
        "-f",
        "--format",
        dest="rdf_format",
        default=None,
        help="RDF serialization of the input (turtle, xml, json-ld, …).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    markdown = convert_file(
        args.input,
        title=args.title,
        rdf_format=args.rdf_format,
        asset_prefix=args.asset_prefix,
    )
    if args.output is None:
        sys.stdout.write(markdown)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(markdown, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
