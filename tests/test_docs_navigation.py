"""The hand-written docs hold together (#293): the navigation names files that exist, the ORSD and the use-case
documents carry one version in every place that states it, and their relative links reach a file.

`mkdocs build --strict` finds these too, but it runs only on `main`, after the merge; these checks run on the pull request.
"""
import re
from pathlib import Path
from urllib.parse import unquote

import pytest

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
SPEC = DOCS / "specification"
USE_CASES = SPEC / "use-cases"
ORSD_NAME = re.compile(r"ORSD_v\d+\.\d+\.md")
VERSION_FIELD = re.compile(r"\*\*Version:\*\*\s*(\d+(?:\.\d+)*)")
HISTORY_ENTRY = re.compile(r"^###\s+v(\d+(?:\.\d+)*)\b", re.M)


def read(path):
    return path.read_text(encoding="utf-8")


def pages_files():
    return sorted(DOCS.rglob(".pages"))


def nav_entries(pages):
    """The plain file or folder names under `nav:` (the `...` rest marker and titled entries are not names)."""
    entries, in_nav = [], False
    for line in read(pages).splitlines():
        if line.startswith("nav:"):
            in_nav = True
        elif in_nav and line.startswith("  - "):
            entry = line[4:].strip()
            if entry != "..." and ": " not in entry:
                entries.append(entry)
        elif in_nav and line.strip() and not line.startswith(" "):
            in_nav = False
    return entries


def orsd_file():
    found = sorted(SPEC.glob("ORSD_v*.md"))
    assert len(found) == 1, f"expected one ORSD file in docs/specification, found {[p.name for p in found]}"
    return found[0]


def use_case_files():
    return sorted(USE_CASES.glob("UC-*/UC-*.md"))


def history_versions(text, heading):
    """The versions of the `### vX.Y` entries after the `heading` line, newest first (the page's own order)."""
    start = re.search(heading, text, re.M)
    return HISTORY_ENTRY.findall(text[start.end():]) if start else []


@pytest.mark.parametrize("pages", pages_files(), ids=lambda p: p.parent.relative_to(DOCS).as_posix() or "docs")
def test_every_navigation_entry_names_a_file_or_folder_that_exists(pages):
    missing = [e for e in nav_entries(pages) if not (pages.parent / e).exists()]
    assert not missing, f"{pages.relative_to(ROOT).as_posix()} lists {missing}, which are not there: the docs build stops on them"


def test_the_orsd_states_its_file_version_in_the_heading_the_version_line_and_the_history():
    path = orsd_file()
    text = read(path)
    version = re.fullmatch(r"ORSD_v(.+)\.md", path.name).group(1)
    assert re.search(rf"^#\s.*—\s*v{re.escape(version)}\s*$", text, re.M), f"the heading of {path.name} does not say v{version}"
    assert VERSION_FIELD.search(text).group(1) == version, f"the Version line of {path.name} does not say {version}"
    assert history_versions(text, r"^##\s+Version history")[:1] == [version], f"the newest history entry of {path.name} is not v{version}"


def test_every_reference_to_the_orsd_names_the_current_file():
    current = orsd_file().name
    places = [ROOT / "README.md", DOCS / "index.md", ROOT / "mkdocs.yml", ROOT / "scripts" / "generate_docs.py", SPEC / ".pages"]
    stale = {p.relative_to(ROOT).as_posix(): sorted(set(ORSD_NAME.findall(read(p))) - {current}) for p in places}
    assert not any(stale.values()), f"these still name an earlier ORSD file (the current one is {current}): {({k: v for k, v in stale.items() if v})}"


# Use cases that may have no "Version History" section: UC-06 is a first draft. Any other use case must have one.
NO_HISTORY_YET = {"UC-06"}


def use_case_problems(path_name, text, readme, no_history_yet=NO_HISTORY_YET):
    """What disagrees about a use case's version, or is missing so that it cannot be checked."""
    version = VERSION_FIELD.search(text).group(1)
    problems = []
    history = history_versions(text, r"^##\s+\d+\.\s+Version History")
    if history:
        if history[0] != version:
            problems.append(f"the header says {version}, the newest history entry says v{history[0]}")
    elif re.match(r"UC-\d+", path_name).group(0) not in no_history_yet:
        problems.append("it has no 'N. Version History' section with a '### vX.Y' entry")
    row = next((line for line in readme.splitlines() if "ORSD Status" in line and path_name in line), None)
    if row is None:
        problems.append("use-cases/README.md has no 'ORSD Status' row that links it")
    elif not re.search(rf"\(v{re.escape(version)}\)", row):
        problems.append(f"its row in use-cases/README.md does not say (v{version})")
    return problems


@pytest.mark.parametrize("path", use_case_files(), ids=lambda p: p.parent.name)
def test_a_use_case_states_one_version_in_its_header_its_history_and_the_use_case_table(path):
    problems = use_case_problems(path.name, read(path), read(USE_CASES / "README.md"))
    assert not problems, f"{path.name}: " + "; ".join(problems)


UC_TEXT = "**Version:** 0.2 (draft)\n\n## 9. Version History\n\n### v0.2\n\nx\n"
UC_README = "| **ORSD Status** | [Draft (v0.2)](<UC-09/UC-09 x.md>) |\n"


def test_a_use_case_with_nothing_to_compare_is_reported_not_skipped():
    assert use_case_problems("UC-09 x.md", UC_TEXT, UC_README) == []
    assert use_case_problems("UC-09 x.md", UC_TEXT.replace("0.2 (draft)", "0.3 (draft)"), UC_README) == [
        "the header says 0.3, the newest history entry says v0.2", "its row in use-cases/README.md does not say (v0.3)"]
    (no_history,) = use_case_problems("UC-09 x.md", "**Version:** 0.2\n", UC_README)
    assert "no 'N. Version History' section" in no_history
    uc06_readme = UC_README.replace("UC-09/UC-09 x", "UC-06/UC-06 x")
    assert use_case_problems("UC-06 x.md", "**Version:** 0.2\n", uc06_readme) == []
    (no_row,) = use_case_problems("UC-09 y.md", UC_TEXT, UC_README)
    assert "no 'ORSD Status' row" in no_row


def link_targets(text):
    for match in re.finditer(r"\]\((<[^>]+>|[^)\s]+)\)", text):
        target = match.group(1).strip("<>")
        if not re.match(r"[a-z][a-z0-9+.-]*:|#|/", target, re.I):
            yield unquote(target.split("#")[0])


def hand_written_pages():
    skipped = {"ontologies", "ai", "brainstorming"}
    for path in sorted(DOCS.rglob("*.md")):
        parts = path.relative_to(DOCS).parts
        if parts[0] not in skipped and not (len(parts) > 1 and parts[0] == "migration"):
            yield path


def broken_links(path, docs=DOCS):
    """Relative links of a page whose target is not a file inside `docs`: the build rejects a link that leaves it."""
    root = docs.resolve()
    broken = []
    for target in link_targets(read(path)):
        if not target:
            continue
        resolved = (path.parent / target).resolve()
        if not (resolved.exists() and root in resolved.parents):
            broken.append(target)
    return broken


@pytest.mark.parametrize("path", list(hand_written_pages()), ids=lambda p: p.relative_to(DOCS).as_posix())
def test_a_relative_link_in_a_hand_written_page_reaches_a_file_inside_docs(path):
    broken = broken_links(path)
    assert not broken, f"{path.relative_to(ROOT).as_posix()} links to files that are not in docs/ (the build rejects them): {broken}"


def test_a_link_to_a_file_outside_docs_or_a_missing_file_is_broken(tmp_path):
    docs = tmp_path / "docs"
    (docs / "sub").mkdir(parents=True)
    (tmp_path / "README.md").write_text("x", encoding="utf-8")
    (docs / "other.md").write_text("x", encoding="utf-8")
    page = docs / "sub" / "page.md"
    page.write_text("[ok](../other.md) [anchor](../other.md#a) [web](https://x.org/a.md) "
                    "[outside](../../README.md) [missing](../gone.md)", encoding="utf-8")
    assert broken_links(page, docs) == ["../../README.md", "../gone.md"]
