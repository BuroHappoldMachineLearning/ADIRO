# Build status badges

The **Build status** column at the top of the [README](https://github.com/BuroHappoldMachineLearning/ADIRO#readme) shows whether the automation that
publishes ADIRO is working. Each badge reads the latest run of one workflow and links to its section below, which says what
it measures, what red means and what to do, and links to the runs. When a release or publishing workflow fails on `main`, a
tracking issue labelled `ci-alert` is also opened
([`alert-on-failure.yml`](https://github.com/BuroHappoldMachineLearning/ADIRO/blob/main/.github/workflows/alert-on-failure.yml)).

## Build & tests { #build-and-tests }

[Latest runs on `main`](https://github.com/BuroHappoldMachineLearning/ADIRO/actions/workflows/generate-deploy-docs.yml?query=branch%3Amain)

- **Shows:** the latest run of *Generate and Deploy Documentation* on `main`: validation of the ontologies, the unit tests, the
  docs build and the deploy to GitHub Pages. The checks of the published site are [their own badge](#post-deploy-checks).
- **Red means:** a test, the validation, the build, the commit-back of the generated `docs/` or the deploy failed. The site, the
  release badges and the version pages stay on the previous state.
- **What to do:** open the run, find the failed job, fix it forward in a pull request.

## Site checks { #post-deploy-checks }

[Latest runs](https://github.com/BuroHappoldMachineLearning/ADIRO/actions/workflows/post-deploy-checks.yml)

- **Shows:** the latest run of *Post-deploy checks*, which runs after each successful deploy of `main`: the external links of
  the site work, and every published release IRI, archived display config and archived example image resolves. It has its own
  queue, so a deploy does not wait for it; a newer successful deploy cancels the checks of an older one, and a failed deploy
  cancels nothing, because the live site is still the previous one
  ([#217](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/217)).
- **Red means:** the site is published, but a link is broken or an earlier release no longer resolves.
- **What to do:** open the run and find the failed job, then fix the cause in a pull request. The checks run again after the
  next deploy, or now with `gh workflow run post-deploy-checks.yml`, which checks the latest successful deploy (its built site
  is kept for a week).

## Release PR { #release-pr }

[Latest runs on `main`](https://github.com/BuroHappoldMachineLearning/ADIRO/actions/workflows/release-pr.yml?query=branch%3Amain)

- **Shows:** the latest run of *Release PR* on `main`, the workflow that rebuilds the Release PR after every push and tags a release when it merges.
- **Red means:** the Release PR is not rebuilt, or a merged release was not tagged.
- **What to do:** open the run and find the failed job.

## Snapshot { #snapshot }

[Latest runs](https://github.com/BuroHappoldMachineLearning/ADIRO/actions/workflows/backup-version.yml)

- **Shows:** the latest run of *Backup Ontology Version*, which archives a release to `versions/` and starts the docs deploy.
  It runs once per release tag, so the badge shows the most recent tag only.
- **Red means:** a release has no archive, no version page and no badge.
- **What to do:** once the cause is fixed, run `gh workflow run backup-version.yml -f tag=<module>-v<semver>` for each failed tag.

## Reasoning { #reasoning }

[Latest runs on `main`](https://github.com/BuroHappoldMachineLearning/ADIRO/actions/workflows/reasoning-main.yml?query=branch%3Amain)

- **Shows:** the latest run of *Ontology reasoning on main*: the reasoner over the whole suite at latest. It runs when an ontology file changes.
- **Red means:** the combined suite is inconsistent, has an unsatisfiable class or is not valid OWL 2 DL, usually because two
  pull requests that each passed conflict once both merged.
- **What to do:** fix forward in a pull request; reproduce with `ENFORCE=1 bash scripts/run_reasoning.sh`.

## CI alert issues { #ci-alert-issues }

[Open alerts](https://github.com/BuroHappoldMachineLearning/ADIRO/issues?q=is%3Aissue+is%3Aopen+label%3Aci-alert)

- **Shows:** the number of open issues labelled `ci-alert`, which the alert workflow opens when a release or publishing
  workflow fails. Green at 0, yellow above.
- **Yellow means:** a workflow failed and nobody has resolved its tracking issue yet.
- **What to do:** open the issue; it names the failed jobs and the next step. The deploy and Release PR issues close themselves
  when a later run passes; the snapshot issue is closed by hand once every failed tag is published.

## What a badge does not show

- **One run, not a history.** A workflow badge shows only the latest run. The **snapshot** workflow runs once per release
  tag, so a later green run for one module can hide an earlier red one for another. The **CI alert issues** count covers
  this: the snapshot issue stays open until every failed tag is published and a person closes it.
- **A workflow that does not run.** A disabled workflow, or one that never started, leaves its badge on the last result.
- **Pull requests.** The badges describe `main`. The checks on a pull request (validation, the reasoner, the QC and
  guidance comments) report on the pull request itself.
- **Published-link checks have no badge of their own.** They are jobs inside the deploy workflow, so a failure turns
  **build & tests** red.
