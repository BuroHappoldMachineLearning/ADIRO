# Build status badges

The **Build status** column at the top of the [README](https://github.com/BuroHappoldMachineLearning/ADIRO#readme) shows whether the automation that
publishes ADIRO is working. Each badge reads the latest run of one workflow and links to its runs, so a red badge opens
the failing run. When a release or publishing workflow fails on `main`, a tracking issue labelled `ci-alert` is also
opened ([`alert-on-failure.yml`](https://github.com/BuroHappoldMachineLearning/ADIRO/blob/main/.github/workflows/alert-on-failure.yml)).

| Badge | What it shows | What red means | What to do |
|---|---|---|---|
| **build & tests** | The latest run of [Generate and Deploy Documentation](https://github.com/BuroHappoldMachineLearning/ADIRO/actions/workflows/generate-deploy-docs.yml) on `main`: validation of the ontologies, the unit tests, the docs build, the deploy to GitHub Pages and the post-deploy checks (the published IRIs and display configs resolve, the links work). | A test, the validation, the build, the commit-back of the generated `docs/` or the deploy failed. The site, the release badges and the version pages stay on the previous state. | Open the run, find the failed job, fix it forward in a pull request. |
| **release PR** | The latest run of [Release PR](https://github.com/BuroHappoldMachineLearning/ADIRO/actions/workflows/release-pr.yml) on `main`. | The Release PR is not rebuilt, or a merged release was not tagged. | Open the run and find the failed job. |
| **snapshot** | The latest run of [Backup Ontology Version](https://github.com/BuroHappoldMachineLearning/ADIRO/actions/workflows/backup-version.yml), which archives a release to `versions/` and starts the docs deploy. | A release has no archive, version page or badge. | `gh workflow run backup-version.yml -f tag=<module>-v<semver>` for each failed tag, once the cause is fixed. |
| **reasoning** | The latest run of [Ontology reasoning on main](https://github.com/BuroHappoldMachineLearning/ADIRO/actions/workflows/reasoning-main.yml): the reasoner over the whole suite at latest. It runs when an ontology file changes. | The combined suite is inconsistent, has an unsatisfiable class or is not valid OWL 2 DL, usually because two pull requests that each passed conflict once both merged. | Fix forward in a pull request; reproduce with `ENFORCE=1 bash scripts/run_reasoning.sh`. |
| **ci-alert issues** | The number of open issues labelled `ci-alert`. Green at 0, yellow above. | A release or publishing workflow failed and nobody has resolved the tracking issue yet. | Open the issue list; the issue names the failed jobs and the next step. |

## What a badge does not show

- **One run, not a history.** A workflow badge shows only the latest run. The **snapshot** workflow runs once per release
  tag, so a later green run for one module can hide an earlier red one for another. The **ci-alert issues** count covers
  this: the snapshot issue stays open until every failed tag is published and a person closes it.
- **A workflow that does not run.** A disabled workflow, or one that never started, leaves its badge on the last result.
- **Pull requests.** The badges describe `main`. The checks on a pull request (validation, the reasoner, the QC and
  guidance comments) report on the pull request itself.
- **Published-link checks have no badge of their own.** They are jobs inside the deploy workflow, so a failure turns
  **build & tests** red.
