"""Imports and released changelogs are changed on purpose (#195).

An `owl:imports` can be a dependency that the module's own axioms do not show (a data pattern, a property with no domain),
so a warning that calls it unused is a question about intent, not an instruction. The intended imports and their reasons are
pinned in `config/module_imports.json`, and a released changelog section never changes after its tag, except for a correction
that is listed here with its reason.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("rdflib")
from rdflib import Graph, URIRef  # noqa: E402
from rdflib.namespace import OWL, RDF  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
PIN = json.loads((ROOT / "config" / "module_imports.json").read_text(encoding="utf-8"))
PIN = {module: reasons for module, reasons in PIN.items() if not module.startswith("_")}
MODULES = sorted(p.stem for p in (ROOT / "src").glob("*.ttl"))
PREFIX = "https://w3id.org/adiro/"


def real_imports(module):
    graph = Graph().parse(str(ROOT / "src" / f"{module}.ttl"), format="turtle")
    return sorted(str(o).removeprefix(PREFIX) for o in graph.objects(None, OWL.imports))


def test_every_module_is_pinned_and_every_pin_is_a_module():
    assert sorted(PIN) == MODULES, "config/module_imports.json must list exactly the modules in src/"


@pytest.mark.parametrize("module", MODULES)
def test_the_real_imports_are_the_pinned_ones(module):
    pinned = sorted(PIN[module])
    assert real_imports(module) == pinned, (
        f"{module}: the imports in src/ differ from config/module_imports.json. If the change is intended, edit that file in the same "
        f"pull request and give the reason; if an import looked unused, find why it exists first (the pin, the ORSD, git log -S)."
    )


def test_every_pinned_import_has_a_reason():
    for module, imports in PIN.items():
        for imported, reason in imports.items():
            assert len(reason.split()) >= 5, f"{module} imports {imported}: say why"


# --- the caution when an import is removed ---------------------------------------------------------------------------
def test_removing_an_import_is_a_caution_and_adding_one_is_not():
    import pr_guidance as pg

    def ontology(imports):
        g = Graph()
        ont = URIRef("https://w3id.org/adiro/m")
        g.add((ont, RDF.type, OWL.Ontology))
        for i in imports:
            g.add((ont, OWL.imports, URIRef(PREFIX + i)))
        return g

    base, head = ontology(["aec_geometry", "aec_provenance"]), ontology(["aec_provenance"])
    caution = next(c for c in pg.cautions() if c.key == "import-removed")
    assert caution.detect([{"module": "m", "base": base, "head": head}], None) == [
        "`m`: the import of `aec_geometry` is removed"]
    assert caution.detect([{"module": "m", "base": head, "head": base}], None) == []
    assert caution.detect([{"module": "m", "base": base, "head": base}], None) == []


def test_the_advice_for_an_unused_import_says_to_look_first_and_never_just_to_drop_it():
    import pr_guidance as pg

    kind = next(k for k in pg.kinds("o/r") if k.key == "unused-import")
    assert "module_imports.json" in kind.advice and "why" in kind.advice.lower()
    assert not kind.advice.startswith("Drop the import"), "a warning is a question, not an instruction"


# --- a released changelog section does not change --------------------------------------------------------------------
# Corrections made on purpose after a release (a migrated link, a moved page, a typo), each with its reason. A new entry here
# is a decision a reviewer sees; an accident, such as entries that landed under a released heading in a merge, is not one.
KNOWN_CORRECTIONS = {
    "aec_common_symbols-v2.0.0": "a link or wording in the IRI-migration entry was corrected",
    "aec_domain_common-v2.0.0": "a link or wording in the IRI-migration entry was corrected",
    "aec_drawing_metadata-v3.0.0": "entries missing from the release notes at the tag were added to the section afterwards, and the IRI-migration entry was corrected",
    "aec_facade_domain-v2.0.0": "a link or wording in the IRI-migration entry was corrected",
    "aec_geometry-v1.0.0": "a link to a design page that moved in the navigation reorganisation",
    "aec_provenance-v1.0.0": "a link to a design page that moved in the navigation reorganisation",
}


def git(*args):
    done = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    return done.stdout if done.returncode == 0 else None


def section(text, version):
    found = re.search(r"(?m)^## \[%s\][^\n]*\n(.*?)(?=^## \[|\Z)" % re.escape(version), text.replace("\r\n", "\n"), re.S)
    return found.group(0).strip() if found else None


def released_tags():
    tags = git("tag", "-l", "aec_*-v*")
    return [t for t in (tags or "").split() if re.fullmatch(r"aec_[a-z_]+-v\d+\.\d+\.\d+", t)]


def test_a_released_changelog_section_is_what_it_was_at_its_tag():
    tags = released_tags()
    if not tags:
        pytest.skip("no release tags in this checkout (fetch them to run this check)")
    changed = []
    for tag in tags:
        module, version = re.fullmatch(r"(aec_[a-z_]+)-v(\d+\.\d+\.\d+)", tag).groups()
        at_tag, now = git("show", f"{tag}:changelogs/{module}.md"), (ROOT / "changelogs" / f"{module}.md").read_text(encoding="utf-8")
        if at_tag is None or section(at_tag, version) is None:
            continue  # no changelog entry was published at that tag
        if section(at_tag, version) != section(now, version) and tag not in KNOWN_CORRECTIONS:
            changed.append(tag)
    assert changed == [], (
        f"the released changelog section of {changed} differs from the one at its tag. Entries that landed under a released heading "
        f"(a merge with a moved section) belong under [Unreleased]; a deliberate correction is added to KNOWN_CORRECTIONS with its reason."
    )
