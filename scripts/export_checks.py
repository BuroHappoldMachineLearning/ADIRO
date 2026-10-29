#!/usr/bin/env python3
"""
Export the checks: the data-validation shapes and the UC-01 competency queries, as files a consumer can pin (#240).

A system that writes ADIRO data tests it against the shapes in `data-validation/` and the competency queries recorded in the
UC-01 ORSD. The checks are released together, as their own versioned artefact (tag `checks-v<semver>`, changelog
`changelogs/checks.md`), and served under `https://w3id.org/adiro/checks/<semver>/`. This script writes what is served:

    OUT/manifest.json                    the version, the module versions the checks were tested with, and every file
    OUT/shapes/<topic>.shacl.ttl         every shape file, as in data-validation/
    OUT/shapes/release/<topic>.shacl.ttl the shapes that run only for a public release
    OUT/queries/uc01/<name>.rq           each recorded UC-01 query (cq-10-1.rq, promotion.rq, ...)

The ORSD stays the one place a query is written: the tests read it there, and this script copies it out. Only a block whose
first comment line names it ("# CQ 10.1: ..." or "# Promotion: ...") is a recorded query; the other SPARQL blocks of the ORSD
are illustrations.

    python3 scripts/export_checks.py OUT [--version 1.0.0] [--root TREE]   # write the checks
    python3 scripts/export_checks.py --notes 1.0.0                         # the release notes of a version

Standard library only: the release workflow runs it with no packages installed.
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ORSD = Path("docs/specification/use-cases/UC-01/UC-01-Titleblock-Based Drawing Search.md")
SHAPES_DIR = Path("data-validation")
CHANGELOG = Path("changelogs/checks.md")
MARKER = re.compile(r"^# (CQ (\d+)\.(\d+)|Promotion):", re.M)
VERSION_INFO = re.compile(r'owl:versionInfo\s+"(\d+\.\d+\.\d+)"')
W3ID = "https://w3id.org/adiro/checks"


def recorded_queries(root=ROOT):
    """{file name: query text} for every recorded UC-01 query, in the order of the ORSD."""
    text = (Path(root) / ORSD).read_text(encoding="utf-8")
    queries = {}
    for block in re.findall(r"```sparql\n(.*?)```", text, re.S):
        match = MARKER.search(block)
        if not match:
            continue
        name = "promotion.rq" if match.group(1) == "Promotion" else f"cq-{match.group(2)}-{match.group(3)}.rq"
        if name in queries:
            raise ValueError(f"two recorded queries are named {name}")
        queries[name] = block
    return queries


def shape_files(root=ROOT):
    """Every shape file, relative to data-validation/: the topic files, then the release ones."""
    base = Path(root) / SHAPES_DIR
    return sorted(p.relative_to(base).as_posix() for p in base.rglob("*.shacl.ttl"))


def module_versions(root=ROOT):
    """{module: owl:versionInfo} of every module in src/ when the checks are released: the versions they were tested with,
    with any unreleased change of src/ on top (a module's version moves only at its own release)."""
    versions = {}
    for path in sorted((Path(root) / "src").glob("*.ttl")):
        match = VERSION_INFO.search(path.read_text(encoding="utf-8"))
        if match:
            versions[path.stem] = match.group(1)
    return versions


def released_version(root=ROOT):
    """The newest released version in changelogs/checks.md ("## [1.0.0] — date"), or None before the first release."""
    match = re.search(r"^## \[(\d+\.\d+\.\d+)\]", (Path(root) / CHANGELOG).read_text(encoding="utf-8"), re.M)
    return match.group(1) if match else None


def changelog_section(version, root=ROOT):
    """The text of the section of changelogs/checks.md for a released version, or None if it has no section."""
    text = (Path(root) / CHANGELOG).read_text(encoding="utf-8")
    match = re.search(rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|\Z)", text, re.M | re.S)
    return match.group(1).strip() if match else None


def release_notes(version, root=ROOT):
    """The notes of the GitHub Release of checks-v<version>: its changelog section and where it is served."""
    section = changelog_section(version, root)
    if section is None:
        raise ValueError(f"changelogs/checks.md has no section for {version}")
    base = f"{W3ID}/{version}"
    return (f"The data-validation shapes and the UC-01 competency queries, version {version}.\n\n{section}\n\n"
            f"- Manifest (every file, and the module versions the checks were tested with): {base}/manifest.json\n"
            f"- Shapes: {base}/shapes/ (the release shapes under {base}/shapes/release/)\n"
            f"- Queries: {base}/queries/uc01/\n")


def export(out, root=ROOT, version=None):
    out = Path(out)
    if out.exists():
        shutil.rmtree(out)
    shapes = shape_files(root)
    for name in shapes:
        target = out / "shapes" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path(root) / SHAPES_DIR / name, target)
    queries = recorded_queries(root)
    (out / "queries" / "uc01").mkdir(parents=True, exist_ok=True)
    for name, text in queries.items():
        (out / "queries" / "uc01" / name).write_text(text, encoding="utf-8", newline="\n")
    manifest = {
        "artefact": "ADIRO checks",
        "version": version or released_version(root),
        "testedWithModules": module_versions(root),
        "testedWithModulesNote": "The owl:versionInfo of each module in src/ when the checks were released; src/ may hold unreleased changes on top of it.",
        "shapes": [f"shapes/{name}" for name in shapes],
        "releaseShapes": "The shapes under shapes/release/ run only for a public release, with an allowlist of public hosts.",
        "queries": [f"queries/uc01/{name}" for name in queries],
        "source": "https://github.com/BuroHappoldMachineLearning/ADIRO",
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("out", nargs="?", help="the folder to write the checks into (replaced)")
    parser.add_argument("--version", help="the version to record (default: the newest in changelogs/checks.md)")
    parser.add_argument("--root", default=str(ROOT), help="the repository tree to read (default: this one), e.g. a tag checked out")
    parser.add_argument("--notes", metavar="VERSION", help="print the release notes of a released version instead")
    args = parser.parse_args(argv)
    if args.notes:
        print(release_notes(args.notes, args.root), end="")
        return 0
    if not args.out:
        parser.error("give the folder to write the checks into, or --notes VERSION")
    manifest = export(args.out, root=args.root, version=args.version)
    print(f"Exported {len(manifest['shapes'])} shape files and {len(manifest['queries'])} queries, version {manifest['version']}, to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
