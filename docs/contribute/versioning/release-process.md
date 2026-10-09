# Release Process

How a [Versioning](index.md) bump becomes a published, resolvable ontology release.

## The Release PR

An open pull request titled **Release cut: …** (branch `release/next`) means a release is pending. `release-pr.yml` maintains it:

- After every push to `main` it rebuilds the branch from `main` and updates the PR, so it always covers everything unreleased. When nothing is pending it closes the PR.
- Each module's next version is its last released version plus the bump `scripts/compat_diff.py` requires (a module never released keeps its declared version). The PR bumps `owl:versionInfo` and `owl:versionIRI`, moves `[Unreleased]` under a dated version heading in `changelogs/<module>.md`, and updates the `CHANGELOG.md` rollup and the versions line in `AGENTS.md`.
- The PR is a **draft** while any pending module has an empty `[Unreleased]` section: its release notes would be empty. Add the changelog entry on `main`; the PR updates itself.
- Validation (`validate_ontology.py`, `compat_diff.py --enforce`) runs inside the workflow, because a PR opened with the default `GITHUB_TOKEN` does not start the PR-triggered workflows.
- The bump is the classifier's minimum unless an [override](#overriding-a-bump-or-holding-a-module) raises it. The branch is rebuilt on every merge, so a hand edit to it is overwritten.

### How the bump is chosen

Each module's bump is the **highest** one required by any of its unreleased changes:

| Change since the last release | Bump |
|---|---|
| A term is removed, or changes kind (class ↔ property) | MAJOR |
| A domain, range, superclass, superproperty or restriction is changed or tightened | MAJOR |
| A term is added, or a restriction is loosened or removed | MINOR |
| Only annotations change (labels, comments, definitions) | PATCH |

### Example

How the Release PR evolves as changes reach `main`:

| Merged to `main` | The Release PR then shows |
|---|---|
| A PR adds a class to `aec_common_symbols` and writes its changelog entry | Opens: `aec_common_symbols` 3.0.0 → **3.1.0** (MINOR) |
| A PR removes a property from `aec_common_symbols` | Same PR, updated: `aec_common_symbols` → **4.0.0** (MAJOR replaces MINOR) |
| A PR adds `rdfs:comment` text to `aec_domain_common`, with no changelog entry | Same PR now lists both modules (`aec_domain_common` 2.0.0 → **2.0.1**, PATCH) and becomes a **draft**: its release notes would be empty |
| A PR adds the missing `aec_domain_common` changelog entry | Same PR, ready for review again |
| You merge the Release PR | Both modules are tagged and released; the PR is closed |
| The next ontology change reaches `main` | A new Release PR opens |

**Merging the Release PR is the release.** The next run of `release-pr.yml` tags each module whose declared version has a dated changelog heading but no tag, publishes a GitHub Release for it, and dispatches `backup-version.yml` (a Release created with `GITHUB_TOKEN` does not fire the `release` event). Everything below then runs as before.

## Manual cut

The same cut can still be made by hand, for example when the bot is unavailable:

1. **Determine the bump** — classify the change per the [compatibility-diff spec](compatibility-diff-algorithm-spec.md) → MAJOR / MINOR / PATCH.
2. **Bump** `owl:versionInfo` **and** `owl:versionIRI` in that module's `src/<module>.ttl` on `main` (CI enforces tag == `versionInfo` == `versionIRI` tail).
3. **Move** that module's `[Unreleased]` changelog entries in `changelogs/<module>.md` under the new version heading.
4. **Tag** `<module>-v<semver>` (e.g. `aec_common_symbols-v1.2.0`) and publish a **GitHub Release** from that tag.

> Tag convention: `<module>-v<semver>`. Module names use `_` and never contain `-v`, so the tag parses unambiguously into module + version, and maps 1:1 to the versionIRI path `…/<module>/<semver>`.

Everything after step 4 is automatic.

## What runs automatically

**`backup-version.yml`** — triggered by the GitHub Release being published:

- Verifies the tag's module/version match what `src/<module>.ttl` declares at that tag.
- Snapshots `src/<module>.ttl` to `versions/<module>/<semver>/` and pushes the commit to `main`.
- Sets the Release notes from `changelogs/<module>.md` plus the resolvable `w3id.org/adiro` URLs for that version.

The job then dispatches **`generate-deploy-docs.yml`** explicitly (a push made with the default `GITHUB_TOKEN` does not start other workflows, so the snapshot push cannot trigger it). That workflow regenerates the docs, builds the MkDocs site (`--strict`, so a broken link would fail the build here), and deploys to GitHub Pages — publishing both the unversioned "latest" `…/<module>.ttl` and the new versioned snapshot `…/<module>/<semver>/<module>.ttl` as resolvable URLs.

The same job can be started by hand for an existing tag — `gh workflow run backup-version.yml -f tag=<module>-v<semver>` — which is what a Release published with `GITHUB_TOKEN` (and therefore not firing the `release` event) needs. The deploy dispatch is unconditional: it runs whether or not the job pushed a new snapshot, so re-running the job for a tag whose snapshot already exists repairs a release whose Pages deploy was missed. The cost of a re-run is one extra docs build, and the deploy publishes the current state of `main` (not the tagged commit), exactly as any push to `main` does.

If several modules changed together, cut **one tag per changed module** — each is an independent release, and each publishes through this same chain on its own.

## Overriding a bump or holding a module

The bump is the compat-diff minimum, and that tool compares the Turtle syntactically. Two cases need a human decision, and both are made in `config/release_overrides.json` on `main`, where the choice is reviewed like any other commit and survives every rebuild of the Release PR. The file maps a module to **one value**:

```json
{
  "aec_domain_common": "minor",
  "aec_facade_domain": "hold"
}
```

| Value | Effect |
|---|---|
| `"patch"`, `"minor"`, `"major"` | Raises the module's bump to at least that level. It never lowers it below what the changes require; a lower value has no effect, and the PR says so. Consumed by the release cut, so it applies to one release only. |
| `"hold"` | Leaves the module out of the Release PR (listed under "Held back") until the entry is deleted. |

Examples. Ten `rdfs:comment` definitions in `aec_domain_common` are reworded and one changes what `Beam` means: the classifier sees annotation changes only (PATCH), and `"minor"` records that consumers should notice. `aec_drawing_metadata` is needed now while `aec_domain_common` holds unfinished work: `"aec_domain_common": "hold"` releases the first only. An unknown module or any other value fails the workflow, so a typo cannot silently do nothing.

## Design decisions

- **Default `GITHUB_TOKEN`, no PAT or app secret.** Nothing created with it starts other workflows, so the Release PR gets no PR-triggered checks. The release job validates (`validate_ontology.py`, `compat_diff.py --enforce`) before pushing the branch. It does **not** re-run the reasoner (HermiT/ROBOT): that already gates every ontology PR, and a release cut changes only version strings and changelogs, so it cannot change entailments. Re-running it would reason over the same `main` and add no coverage. The one gap that exists — a PR's reasoner check is not repeated if another PR merges after its last push — is independent of releases and is tracked in [#104](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/104).
- **PATCH-only (annotation) changes also open a Release PR.** Opening a PR forces nothing; merging does. The purpose is that a pending release is always visible, and hiding PATCH changes would leave them unreleased and unseen until something larger arrived.
- **An empty `[Unreleased]` section makes the PR a draft** rather than failing the job or only warning. A draft cannot be merged by accident with empty release notes, it still shows that a release is pending, and it becomes ready on its own once the changelog entry is added. This is the fallback: the earlier check belongs at PR time, where the author can write the entry while the change is fresh ([#105](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/105)).
- **Overrides live in a file on `main`, not on the PR branch**, because the branch is regenerated from `main` on every merge. One value per module (a bump level or `hold`) keeps it to a single thing to remember, and a bump can only be raised so that a breaking change cannot be released as a PATCH.

