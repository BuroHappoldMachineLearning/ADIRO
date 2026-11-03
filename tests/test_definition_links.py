"""The pyLODE pages link the names of terms in a definition to their documentation, like the Markdown pages (#252)."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import generate_docs as gd  # noqa: E402

X = "https://w3id.org/adiro/adiro_x#"
P = "https://w3id.org/adiro/adiro_provenance#"

MODULE = """@prefix : <https://w3id.org/adiro/adiro_x#> .
@prefix aprov: <https://w3id.org/adiro/adiro_provenance#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
<https://w3id.org/adiro/adiro_x> a owl:Ontology .
:Box a owl:Class ; rdfs:comment "A Box, an InferredEntity in a LayoutContentType, made by a prov:Activity, never Failed." .
:LayoutContentType a owl:Class ; rdfs:label "Layout content type" ; rdfs:comment "Where a Box is." .
prov:Activity a owl:Class .
"""

PROVENANCE = """@prefix : <https://w3id.org/adiro/adiro_provenance#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
<https://w3id.org/adiro/adiro_provenance> a owl:Ontology .
:InferredEntity a owl:Class ; rdfs:label "Inferred entity" .
:Failed a owl:NamedIndividual .
"""


def entity(fid, iri, description):
    return (f'<div class="property entity" id="{fid}">\n<table><tr><th>IRI</th>\n<td>\n<code>{iri}</code>\n</td></tr>\n'
            f'<tr><th><a class="hover_property" href="http://purl.org/dc/terms/description" title="">Description</a></th>\n'
            f'<td><p>{description}</p></td></tr></table>\n</div>\n')


# pyLODE makes an id from the label when it can: LayoutContentType is #Layoutcontenttype, InferredEntity #Inferredentity.
X_PAGE = ("<html>" + entity("Box", X + "Box", "A Box, an InferredEntity in a LayoutContentType, made by a prov:Activity, never Failed.")
          + entity("Layoutcontenttype", X + "LayoutContentType", "Where a Box is.")
          + entity("Activity", "http://www.w3.org/ns/prov#Activity", "Local typing stub.") + "</html>")
P_PAGE = "<html>" + entity("Inferredentity", P + "InferredEntity", "Anything inferred.") + "</html>"


def site(tmp_path, deprecated=False):
    (tmp_path / "src").mkdir()
    module = tmp_path / "src" / "adiro_x.ttl"
    module.write_text(MODULE.replace("a owl:Ontology .", "a owl:Ontology ; owl:deprecated true .") if deprecated else MODULE,
                      encoding="utf-8")
    (tmp_path / "src" / "adiro_provenance.ttl").write_text(PROVENANCE, encoding="utf-8")
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "adiro_x.html").write_text(X_PAGE, encoding="utf-8")
    (docs / "adiro_provenance.html").write_text(P_PAGE, encoding="utf-8")
    return [module, tmp_path / "src" / "adiro_provenance.ttl"], docs


def test_pylode_ids_reads_each_entrys_id_from_the_page():
    assert gd.pylode_ids(X_PAGE) == {X + "Box": "Box", X + "LayoutContentType": "Layoutcontenttype",
                                     "http://www.w3.org/ns/prov#Activity": "Activity"}


def test_suite_terms_lists_each_modules_own_terms_and_which_are_individuals(tmp_path):
    files, _ = site(tmp_path)
    suite = gd.suite_terms(files)
    assert suite[P + "Failed"] == ("adiro_provenance", "Failed", True)
    assert suite[X + "Box"] == ("adiro_x", "Box", False)
    assert "http://www.w3.org/ns/prov#Activity" not in suite  # a stub is not the module's own term


def test_definitions_link_to_the_ids_pylode_gave_on_this_page_and_on_another_modules_page(tmp_path):
    files, docs = site(tmp_path)
    assert gd.link_pylode_pages(files, tmp_path, docs) == 1
    page = (docs / "adiro_x.html").read_text(encoding="utf-8")
    assert ('<td><p>A Box, an <a href="adiro_provenance.html#Inferredentity">InferredEntity</a> in a '
            '<a href="#Layoutcontenttype">LayoutContentType</a>, made by a <a href="#Activity">prov:Activity</a>, '
            'never Failed.</p></td>') in page  # Failed is an individual: the pyLODE page has no entry for it
    assert '<td><p>Where a <a href="#Box">Box</a> is.</p></td>' in page
    assert gd.link_pylode_pages(files, tmp_path, docs) == 0  # running it again changes nothing


def test_an_earlier_releases_page_links_two_levels_up(tmp_path):
    files, docs = site(tmp_path)
    (tmp_path / "versions" / "adiro_x" / "1.0.0").mkdir(parents=True)
    (tmp_path / "versions" / "adiro_x" / "1.0.0" / "adiro_x.ttl").write_text(MODULE, encoding="utf-8")
    (docs / "adiro_x" / "1.0.0").mkdir(parents=True)
    (docs / "adiro_x" / "1.0.0" / "adiro_x.html").write_text(X_PAGE, encoding="utf-8")
    gd.link_pylode_pages(files, tmp_path, docs)
    assert '<a href="../../adiro_provenance.html#Inferredentity">' in (docs / "adiro_x" / "1.0.0" / "adiro_x.html").read_text(encoding="utf-8")


def test_the_page_of_a_deprecated_module_links_only_within_itself(tmp_path):
    files, docs = site(tmp_path, deprecated=True)
    gd.link_pylode_pages(files, tmp_path, docs)
    page = (docs / "adiro_x.html").read_text(encoding="utf-8")
    assert "adiro_provenance.html" not in page and '<a href="#Layoutcontenttype">LayoutContentType</a>' in page


# The published pages: every link added to a definition reaches an entry. The site build does not check it (mkdocs reports
# a missing anchor only as information, and does not read the pyLODE pages).

DOCS = ROOT / "docs"
_ANCHOR = re.compile(r'<a href="([^"#]*)#([^"]+)">')


def html_ids(page: Path) -> set[str]:
    return set(gd._ENTITY_DIV.findall(page.read_text(encoding="utf-8")))


def test_every_link_in_a_pylode_definition_reaches_an_entry():
    pages = sorted(DOCS.glob("*.html")) + sorted(DOCS.glob("*/*/*.html"))
    broken = []
    for page in pages:
        for cell in gd._DESCRIPTION_CELL.finditer(page.read_text(encoding="utf-8")):
            for target, fid in _ANCHOR.findall(cell.group(2)):
                target_page = (page.parent / target).resolve() if target else page
                if not target_page.is_file() or fid not in html_ids(target_page):
                    broken.append(f"{page.relative_to(DOCS)} -> {target}#{fid}")
    assert not broken, broken[:20]


def test_every_link_on_a_markdown_ontology_page_reaches_an_entry():
    broken = []
    for page in sorted((DOCS / "ontologies").rglob("*.md")):
        text = page.read_text(encoding="utf-8")
        for target, fid in re.findall(r"\]\(([^)#\s]*\.md)?#([^)\s]+)\)", text):
            target_page = (page.parent / target).resolve() if target else page
            if not target_page.is_file() or f"{{#{fid}}}" not in target_page.read_text(encoding="utf-8"):
                broken.append(f"{page.relative_to(DOCS)} -> {target}#{fid}")
    assert not broken, broken[:20]


def test_the_published_pages_link_the_example_of_the_issue():
    md = (DOCS / "ontologies" / "adiro_provenance.md").read_text(encoding="utf-8")
    assert "each recorded as a [FieldAssertion](#FieldAssertion)." in md
    html = (DOCS / "adiro_provenance.html").read_text(encoding="utf-8")
    assert '<a href="#errorMessage">errorMessage</a>' in html
