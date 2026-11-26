"""The modularization page describes the suite as it is (#305): every live module, its namespace and its imports."""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "docs" / "specification" / "design-decisions" / "modularization" / "index.md"


def live_modules():
    """The modules in src/ that are not deprecated (a deprecated predecessor stays in src/ for one release cycle)."""
    rdflib = pytest.importorskip("rdflib")
    out = {}
    for path in sorted((ROOT / "src").glob("*.ttl")):
        graph = rdflib.Graph().parse(str(path), format="turtle")
        ontology = next(graph.subjects(rdflib.RDF.type, rdflib.OWL.Ontology))
        if (ontology, rdflib.OWL.deprecated, None) not in graph:
            out[path.stem] = str(ontology) + "#"
    return out


def page_table():
    """{module: (namespace, imports)} from the page's table of modules."""
    rows = {}
    for line in PAGE.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 5 and re.fullmatch(r"`\w+`", cells[0]) and cells[0] != "`Module`":
            imports = set(re.findall(r"`(\w+)`", cells[3]))
            rows[cells[0].strip("`")] = (cells[2].strip("`"), imports)
    return rows


def test_every_live_module_is_on_the_page_with_its_namespace():
    modules, rows = live_modules(), page_table()
    assert set(rows) == set(modules), f"on the page: {sorted(rows)}; in src/: {sorted(modules)}"
    for module, namespace in modules.items():
        assert rows[module][0] == namespace, module


def test_each_modules_imports_on_the_page_are_its_pinned_imports():
    """config/module_imports.json is compared with the real owl:imports by tests/test_module_imports.py."""
    pin = json.loads((ROOT / "config" / "module_imports.json").read_text(encoding="utf-8"))
    for module, (_, imports) in page_table().items():
        assert imports == set(pin[module]), f"{module}: page {sorted(imports)}, pin {sorted(pin[module])}"


def test_the_diagram_draws_exactly_the_pinned_imports():
    pin = json.loads((ROOT / "config" / "module_imports.json").read_text(encoding="utf-8"))
    text = PAGE.read_text(encoding="utf-8")
    diagram = text.split("```mermaid")[1].split("```")[0]
    names = dict(re.findall(r'(\w+)\["(\w+)"\]', diagram))
    edges = {(names[a], names[b]) for a, b in re.findall(r"(\w+) --> (\w+)", diagram)}
    expected = {(m, i) for m in page_table() for i in pin[m]}
    assert edges == expected, (sorted(edges - expected), sorted(expected - edges))
