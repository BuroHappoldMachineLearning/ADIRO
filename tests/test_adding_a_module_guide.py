"""The guide to adding a module names every step a new module needs (#304), so the guide and the checks cannot drift apart.

Each step is tied to what enforces it or depends on it. A new requirement on a module (a new test, a new config file) is
added to the guide and to this list in the same pull request.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GUIDE = (ROOT / "docs" / "contribute" / "adding-ontologies.md").read_text(encoding="utf-8")

# what the guide must name: (the text the guide names it by, the file that enforces or depends on it)
REQUIRED = [
    ("scripts/validate_ontology.py", "scripts/validate_ontology.py"),
    ("config/module_imports.json", "tests/test_module_imports.py"),
    ("tests/test_module_imports.py", "tests/test_module_imports.py"),
    ("src/catalog-v001.xml", "src/catalog-v001.xml"),
    ("changelogs/<module>.md", "scripts/prepare_release.py"),
    ("README.md", "tests/test_readme_badges.py"),
    ("tests/test_readme_badges.py", "tests/test_readme_badges.py"),
    ("dependency_order", "scripts/generate_docs.py"),
    ("tests/test_modularization_page.py", "tests/test_modularization_page.py"),
    ("mkdocs build --strict", "mkdocs.yml"),
]


def test_the_guide_names_every_step_a_new_module_needs():
    missing = [name for name, _ in REQUIRED if name not in GUIDE]
    assert not missing, f"docs/contribute/adding-ontologies.md does not name: {missing}"


def test_what_the_guide_names_exists():
    """A step that names a file or a check that is gone would send a contributor nowhere."""
    gone = [enforcer for _, enforcer in REQUIRED if not (ROOT / enforcer).exists()]
    assert not gone, gone
    assert "dependency_order" in (ROOT / "scripts" / "generate_docs.py").read_text(encoding="utf-8")


def test_the_guide_does_not_promise_a_manual_navigation_step_or_subfolders():
    """The navigation of the ontology pages is generated (docs/ontologies/.pages), and only src/*.ttl is read."""
    assert "nav:" not in GUIDE and "subfolder to `src`" not in GUIDE
