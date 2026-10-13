"""Version list and selector for the per-ontology documentation pages (scripts/ontology_versions.py, #124)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import ontology_versions as ov  # noqa: E402


def make_repo(tmp_path, archived, declared="1.0.0", module="aec_x"):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / f"{module}.ttl").write_text(f'owl:versionInfo "{declared}" .\n', encoding="utf-8")
    for v in archived:
        folder = tmp_path / "versions" / module / v
        folder.mkdir(parents=True)
        (folder / f"{module}.ttl").write_text(f'owl:versionInfo "{v}" .\n', encoding="utf-8")
    return tmp_path


def test_archived_versions_are_ordered_numerically_and_ignore_other_folders(tmp_path):
    repo = make_repo(tmp_path, ["1.2.0", "1.10.0", "1.9.0"])
    (repo / "versions" / "aec_x" / "draft").mkdir()  # not a version
    (repo / "versions" / "aec_x" / "2.0.0").mkdir()  # no snapshot inside
    assert ov.archived_versions(repo, "aec_x") == ["1.2.0", "1.9.0", "1.10.0"]
    assert ov.archived_versions(repo, "aec_none") == []


def test_the_declared_version_is_read_from_the_turtle_file(tmp_path):
    repo = make_repo(tmp_path, [], declared="3.1.4")
    assert ov.declared_version(repo / "src" / "aec_x.ttl") == "3.1.4"


def test_version_list_is_newest_first_without_duplicates():
    assert ov.version_list(["1.0.0", "2.0.0"], "2.0.0") == ["2.0.0", "1.0.0"]  # released: declared == highest archived
    assert ov.version_list(["1.0.0", "2.0.0"], "2.0.1") == ["2.0.1", "2.0.0", "1.0.0"]  # a cut whose snapshot is not taken yet
    assert ov.version_list([], "1.0.0") == ["1.0.0"]  # a first release awaiting its snapshot
    assert ov.version_list(["1.9.0", "1.10.0"], None) == ["1.10.0", "1.9.0"]
    assert ov.version_list(["1.0.0"], "not-a-version") == ["1.0.0"]


def test_status_shows_latest_or_which_version_is_available():
    assert ov.button_text("4.0.1", "4.0.1") == "Version 4.0.1 (latest)"
    assert ov.button_text("3.0.0", "4.0.1") == "Version 3.0.0 (4.0.1 available)"


def test_links_from_the_latest_page_go_down_to_each_version():
    html = ov.selector_html("4.0.1", ["4.0.1", "4.0.0", "3.0.0"])
    assert '<a href="./" class="adiro-version-current" aria-current="page">4.0.1 (latest)</a>' in html
    assert '<a href="4.0.0/">4.0.0</a>' in html and '<a href="3.0.0/">3.0.0</a>' in html


def test_links_from_an_earlier_page_go_to_the_latest_page_and_to_siblings():
    html = ov.selector_html("3.0.0", ["4.0.1", "4.0.0", "3.0.0"])
    assert '<summary class="md-button">Version 3.0.0 (4.0.1 available)</summary>' in html
    assert '<a href="../">4.0.1 (latest)</a>' in html  # the latest page is one level up
    assert '<a href="../4.0.0/">4.0.0</a>' in html
    assert '<a href="./" class="adiro-version-current" aria-current="page">3.0.0</a>' in html


def test_the_selector_lists_every_version_once_and_embeds_in_markdown_without_blank_lines():
    versions = ["2.0.0", "1.0.0"]
    html = ov.selector_html("2.0.0", versions)
    assert html.count("<li>") == len(versions)
    assert "\n\n" not in html and html.startswith('<details class="adiro-version">') and html.endswith("</details>")


def test_a_single_version_still_gets_a_selector():
    html = ov.selector_html("1.0.0", ["1.0.0"])
    assert "Version 1.0.0 (latest)" in html and html.count("<li>") == 1


def test_an_earlier_version_page_is_excluded_from_the_search():
    assert ov.version_page_front_matter() == "---\nsearch:\n  exclude: true\n---\n\n"
