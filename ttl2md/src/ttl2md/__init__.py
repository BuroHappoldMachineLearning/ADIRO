"""ttl2md -- convert OWL/RDFS ontologies to Markdown documentation.

Example
-------
>>> from ttl2md import convert_file
>>> md = convert_file("my_ontology.ttl", asset_prefix="../")
"""

from .converter import (
    DEFAULT_EXAMPLE_IMAGE_LOCAL_NAME,
    MarkdownConverter,
    OntologyDoc,
    Term,
    convert_file,
    convert_graph,
    local_name,
)

__version__ = "0.1.0"

__all__ = [
    "MarkdownConverter",
    "OntologyDoc",
    "Term",
    "convert_file",
    "convert_graph",
    "local_name",
    "DEFAULT_EXAMPLE_IMAGE_LOCAL_NAME",
    "__version__",
]
