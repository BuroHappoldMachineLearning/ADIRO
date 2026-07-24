# Versioning

The ontologies use OWL 2 versioning best practices with unversioned and versioned IRIs:

- **Unversioned ontology IRI**: `https://burohappoldmachinelearning.github.io/ADIRO/aec-core` (always resolves to current version)
- **Versioned ontology IRI**: `https://burohappoldmachinelearning.github.io/ADIRO/aec-core/1.0.0` (specific version)
- **Namespace prefix**: `https://burohappoldmachinelearning.github.io/ADIRO/aec-core#` (unversioned, always current)

Each ontology declares both an unversioned IRI and a versioned IRI using `owl:versionIRI` and `owl:versionInfo`. The filenames do not include version numbers (e.g., `aec_core.ttl` rather than `aec_core_v01.ttl`).

## Version Backups

When a new version is released (via a tagged release in GitHub), the current version of all ontology files is automatically backed up to the `versions/` folder. The backup process is triggered automatically by GitHub Actions when a release tag is created or published.

The backup structure is:

```
versions/
  1.0.0/
    aec_core.ttl
    aec_drawing_metadata.ttl
    aec_common_symbols.ttl
    aec_domain_common.ttl
    aec_facade_domain.ttl
  1.1.0/
    ...
```

This backup process preserves the complete state of all ontology files at each release point, allowing for:

- Historical reference and comparison
- Rollback capabilities if needed
- Clear versioning documentation

## Creating a New Version

To create a new version:

1. Make your changes to the ontology files in `src/`
2. Update the version number in the ontology IRI (e.g., `1.0.0` → `1.1.0`) and update `owl:versionIRI` and `owl:versionInfo` in all ontology files
3. Commit and push your changes to `main` or `master`
4. The `deploy-docs` workflow will automatically:
   - Validate all ontology files
   - Generate documentation
   - Deploy to GitHub Pages
5. Create a new release in GitHub with a tag matching the version (e.g., `v1.1.0` or `1.1.0`)
6. The `backup-version` workflow will automatically:
   - Extract the version from the release tag
   - Copy all `.ttl` files from `src/` to `versions/<version>/`
   - Commit and push the backup to the repository
