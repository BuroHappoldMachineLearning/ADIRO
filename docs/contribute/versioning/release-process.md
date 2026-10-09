# Release Process

How a [Versioning](index.md) bump becomes a published, resolvable ontology release.

## The Release PR

An open pull request titled **Release cut: …** (branch `release/next`) means a release is pending. `release-pr.yml` maintains it:

- After every push to `main` it rebuilds the branch from `main` and updates the PR, so it always covers everything unreleased. When nothing is pending it closes the PR.
- Each module's next version is its last released version plus the bump `scripts/compat_diff.py` requires (a module never released keeps its declared version). The PR bumps `owl:versionInfo` and `owl:versionIRI`, moves `[Unreleased]` under a dated version heading in `changelogs/<module>.md`, and updates the `CHANGELOG.md` rollup and the versions line in `AGENTS.md`.
- The PR is a **draft** while any pending module has an empty `[Unreleased]` section: its release notes would be empty. Add the changelog entry on `main`; the PR updates itself.
- The PR is opened by the **ADIRO Bot** GitHub App, so it gets the normal PR checks (validation, reasoning, version-impact comment). The workflow also runs `validate_ontology.py` and `compat_diff.py --enforce` before pushing the branch, as a fail-fast check on its own output.
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

**Merging the Release PR is the release.** The next run of `release-pr.yml` completes each release whose cut has been merged (declared version has a dated changelog heading, but no snapshot under `versions/` yet): it publishes the GitHub Release, or re-dispatches `backup-version.yml` if the Release already exists. Because a release stays pending until its snapshot lands, a run that failed half way is picked up by the next push to `main`. Once nothing is pending, the run also deletes the `release/next` branch left behind by the merge. Both jobs run only on the default branch: a manual dispatch naming any other ref is skipped, so a feature branch can never publish tags or rewrite `release/next`. Publishing the Release (as the ADIRO Bot) fires the `release` event, which starts `backup-version.yml`; everything below then runs as before.

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
- Sets the Release notes (`scripts/release_notes.py`): a summary line with the SemVer bump (MAJOR / MINOR / PATCH, or first release), the previous → this version, a link to the module's [published documentation page](https://burohappoldmachinelearning.github.io/ADIRO/ontologies/aec_common_symbols/) and a compare link; the module's `changelogs/<module>.md` section; the pull requests that changed `src/<module>.ttl` since the previous release (a bare commit is listed where there was no PR); and the resolvable `w3id.org/adiro` URLs for that version.

The job then dispatches **`generate-deploy-docs.yml`** explicitly (a push made with the default `GITHUB_TOKEN` does not start other workflows, so the snapshot push cannot trigger it). That workflow regenerates the docs, builds the MkDocs site (`--strict`, so a broken link would fail the build here), and deploys to GitHub Pages — publishing both the unversioned "latest" `…/<module>.ttl` and the new versioned snapshot `…/<module>/<semver>/<module>.ttl` as resolvable URLs.

The same job can be started by hand for an existing tag — `gh workflow run backup-version.yml -f tag=<module>-v<semver>` — which is what a Release published with `GITHUB_TOKEN` (and therefore not firing the `release` event) needs. The deploy dispatch is unconditional: it runs whether or not the job pushed a new snapshot, so re-running the job for a tag whose snapshot already exists repairs a release whose Pages deploy was missed. The cost of a re-run is one extra docs build, and the deploy publishes the current state of `main` (not the tagged commit), exactly as any push to `main` does.

If several modules changed together, cut **one tag per changed module** — each is an independent release, and each publishes through this same chain on its own.

## Release badges

The README shows the latest released version of every module as a badge beside the banner. Each badge reads `badges/<module>.json` from the published site; `scripts/release_badges.py` (called by `generate_docs.py`) writes those files from the highest SemVer under `versions/<module>/`, so they refresh on every docs deploy, including the one dispatched after a release. They follow the shields.io endpoint schema (`schemaVersion`, `label`, `message`, `color`) and can feed anything else that needs the latest version of each module. A badge links to the module's documentation page. A new module needs its badge in `README.md` (`tests/test_readme_badges.py` enforces it).

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

- **The workflow acts as the ADIRO Bot GitHub App, not as `GITHUB_TOKEN`.** Events created with `GITHUB_TOKEN` start no other workflows, so a bot PR would get no PR checks and a published Release would not start `backup-version.yml`; both needed workarounds. An app installation token has neither limit, and the bot gets its own name and logo. The app is registered at organisation level and installed on this repository; its credentials are the repository secrets `ADIRO_BOT_APP_ID` and `ADIRO_BOT_PRIVATE_KEY`, and the workflow requests a short-lived token from them on each run. The same identity is meant for other bot features ([#106](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/106)).
- **The Release PR is reasoned over like any ontology PR.** It changes `src/*.ttl` (version strings), so `ontology-reasoning.yml` runs on it. It cannot change entailments, so this adds no new coverage; the one real gap — a PR's reasoner check is not repeated if another PR merges after its last push — is independent of releases and is tracked in [#104](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/104).
- **PATCH-only (annotation) changes also open a Release PR.** Opening a PR forces nothing; merging does. The purpose is that a pending release is always visible, and hiding PATCH changes would leave them unreleased and unseen until something larger arrived.
- **An empty `[Unreleased]` section makes the PR a draft** rather than failing the job or only warning. A draft cannot be merged by accident with empty release notes, it still shows that a release is pending, and it becomes ready on its own once the changelog entry is added. This is the fallback: the earlier check belongs at PR time, where the author can write the entry while the change is fresh ([#105](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/105)).
- **Overrides live in a file on `main`, not on the PR branch**, because the branch is regenerated from `main` on every merge. One value per module (a bump level or `hold`) keeps it to a single thing to remember, and a bump can only be raised so that a breaking change cannot be released as a PATCH.

