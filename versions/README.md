# Ontology Versions

This directory contains backups of all ontology files from previous versions.

## Structure

Each version folder (e.g., `v01/`, `v02/`) contains a complete snapshot of all ontology files at that release point:

- `aec_core.ttl`
- `aec_drawing_metadata.ttl`
- `aec_common_symbols.ttl`
- `aec_domain_common.ttl`
- `aec_facade_domain.ttl`

## Automatic Backups

Version backups are automatically created by GitHub Actions when a new release tag is created. The workflow:

1. Detects the new release tag
2. Copies all current ontology files to `versions/v<previous_version>/`
3. Preserves the complete state for historical reference

## Usage

To reference a specific version:

- **Current version**: Use files in the repository root
- **Previous versions**: Use files in `versions/v<version>/`

For example, to load version 01 of the core ontology:

```python
from rdflib import Graph
g = Graph()
g.parse("versions/v01/aec_core.ttl", format="turtle")
```

## Version History

- **v01**: Initial modularized version (current)
