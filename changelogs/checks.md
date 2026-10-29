# Changelog — checks

The data-validation shapes (`data-validation/`) and the UC-01 competency queries, released together as their own versioned
artefact ([#240](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/240)): tag `checks-v<semver>`, served under
`https://w3id.org/adiro/checks/<semver>/`. How to pin them, and what a version bump means here, is in
[../docs/contribute/data-validation.md](../docs/contribute/data-validation.md).
Format: [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- **Interrupted runs and the time an extraction job took** ([#249](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/249)). Queries `cq-10-5.rq` (the runs with no end recorded, their last recorded work and the run that continued each), `cq-10-6.rq` (the runs of each extraction job) and `cq-10-7.rq` (each job's elapsed and processing time, in seconds), and the shape file `runs.shacl.ttl` (a run or a step has at most one start, not after its end). Nothing that passed fails, except data with two starts or an end before the start.

## [1.0.0] — 2026-10-29

### Added
- **The first release of the checks** ([#240](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/240)). Every shape file of `data-validation/`, the public-release shapes included, and every recorded UC-01 competency query (CQ 1.3 to CQ 11.4, and the promotion; the integration example CQ-I 1 needs a reasoner and is not one), each in its own `.rq` file, with a `manifest.json` naming the module versions they were tested with.
