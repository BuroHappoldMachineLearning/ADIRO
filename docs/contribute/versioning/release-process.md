# Release Process

How a [Versioning](index.md) bump becomes a published, resolvable ontology release.

## Steps

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
