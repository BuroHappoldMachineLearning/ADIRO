# Changelog

ADIRO's modules are versioned **independently** (per-module SemVer — see
[docs/contribute/versioning/](docs/contribute/versioning/)). This file is a rollup; the
**source of truth** for each module is its own changelog under `changelogs/`.

| Module | Version | Changelog |
|---|---|---|
| `adiro_provenance` | 2.3.2 | [changelogs/adiro_provenance.md](changelogs/adiro_provenance.md) |
| `adiro_geometry` | 3.1.2 | [changelogs/adiro_geometry.md](changelogs/adiro_geometry.md) |
| `adiro_drawing_metadata` | 8.0.1 | [changelogs/adiro_drawing_metadata.md](changelogs/adiro_drawing_metadata.md) |
| `adiro_drawing_symbology` | 6.0.1 | [changelogs/adiro_drawing_symbology.md](changelogs/adiro_drawing_symbology.md) |
| `adiro_discipline_core` | 5.0.1 | [changelogs/adiro_discipline_core.md](changelogs/adiro_discipline_core.md) |
| `adiro_facade_discipline` | 5.0.1 | [changelogs/adiro_facade_discipline.md](changelogs/adiro_facade_discipline.md) |

The versions above are the latest released versions. Changes not yet released accumulate in each module's
`[Unreleased]` changelog section until the next release cut.

Three modules were renamed again ([#281](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/281)); their former modules are deprecated, stay published, and their history continues under the new names.

| Former module | Final release | Changelog |
|---|---|---|
| `adiro_common_symbols` | 5.0.1 | [changelogs/adiro_common_symbols.md](changelogs/adiro_common_symbols.md) |
| `adiro_domain_common` | 4.0.1 | [changelogs/adiro_domain_common.md](changelogs/adiro_domain_common.md) |
| `adiro_facade_domain` | 4.0.1 | [changelogs/adiro_facade_domain.md](changelogs/adiro_facade_domain.md) |

The `adiro_*` modules were called `aec_*` until the final releases below ([#171](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/171)); those releases are deprecated, stay published, and their history is in their own changelogs. See [Moving from `aec_*` to `adiro_*`](docs/migrating-from-aec.md).

| Former module | Final release | Changelog |
|---|---|---|
| `aec_provenance` | 1.1.0 | [changelogs/aec_provenance.md](changelogs/aec_provenance.md) |
| `aec_geometry` | 2.0.0 | [changelogs/aec_geometry.md](changelogs/aec_geometry.md) |
| `aec_drawing_metadata` | 6.0.0 | [changelogs/aec_drawing_metadata.md](changelogs/aec_drawing_metadata.md) |
| `aec_common_symbols` | 4.0.1 | [changelogs/aec_common_symbols.md](changelogs/aec_common_symbols.md) |
| `aec_domain_common` | 3.0.1 | [changelogs/aec_domain_common.md](changelogs/aec_domain_common.md) |
| `aec_facade_domain` | 3.0.1 | [changelogs/aec_facade_domain.md](changelogs/aec_facade_domain.md) |

