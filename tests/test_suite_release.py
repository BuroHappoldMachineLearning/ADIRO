"""A suite-level release archives the repository on Zenodo (#275) and must not start a module snapshot."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = (ROOT / ".github" / "workflows" / "backup-version.yml").read_text(encoding="utf-8")


def test_the_snapshot_job_skips_a_suite_release_but_not_a_module_release_or_a_manual_run():
    job = re.search(r"(?m)^  backup-version:\n((?:    .*\n|\n)*?)    runs-on:", WORKFLOW)
    assert job, "the job has a condition before runs-on"
    condition = re.search(r"(?m)^    if: \$\{\{ (.*) \}\}$", job.group(1))
    assert condition, "the job is conditional"
    guard = condition.group(1)
    assert "github.event_name != 'release'" in guard  # a manual run (workflow_dispatch) always goes ahead
    assert "startsWith(github.event.release.tag_name, 'suite-')" in guard and guard.count("startsWith") == 1


def test_the_module_tag_pattern_does_not_match_a_suite_tag():
    pattern = re.compile(r"^([a-z0-9_]+)-v([0-9]+\.[0-9]+\.[0-9]+)$")
    assert not pattern.match("suite-2026-11-17") and pattern.match("adiro_geometry-v3.1.0")


def test_the_citation_file_names_no_module_and_no_version():
    text = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    assert re.search(r"(?m)^type: software$", text) and not re.search(r"(?m)^version:", text)
    assert "adiro_" not in text  # a module rename leaves the record correct


def test_the_zenodo_doi_is_the_same_in_the_readme_and_the_documentation_index():
    """#275: the README and the generated index carry the same concept DOI, and the badge is keyed by the repository's ID."""
    badge = re.compile(r"zenodo\.org/badge/(\d+)\.svg.*?doi\.org/(10\.5281/zenodo\.\d+)", re.S)
    found = {}
    for name, text in (("README", (ROOT / "README.md").read_text(encoding="utf-8")),
                       ("generator", (ROOT / "scripts" / "generate_docs.py").read_text(encoding="utf-8")),
                       ("index", (ROOT / "docs" / "index.md").read_text(encoding="utf-8"))):
        m = badge.search(text) or re.search(r"doi\.org/(10\.5281/zenodo\.\d+).*?zenodo\.org/badge/(\d+)\.svg", text, re.S)
        assert m, f"{name} has a Zenodo DOI badge"
        found[name] = tuple(sorted(m.groups()))
    assert len(set(found.values())) == 1, found
