"""The module rename map and the tooling that follows it (config/module_renames.json, #171).

A toy suite of two modules, `aec_a` (released 1.0.0 and 2.0.0) and `aec_b` (released 1.0.0, a subclass of a term of
`aec_a`), renamed to `adiro_a` and `adiro_b`, proves the machinery before the real rename: the compatibility check, the
release cut, the owl:priorVersion checks, the release notes, the version dropdown and the badges.
"""
import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("rdflib")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from rdflib import Graph, URIRef  # noqa: E402

import check_prior_versions as cpv  # noqa: E402
import compat_diff as cd  # noqa: E402
import module_renames as mr  # noqa: E402
import ontology_versions as ov  # noqa: E402
import prepare_release as pr  # noqa: E402
import release_badges as rb  # noqa: E402
import release_notes as rn  # noqa: E402
import validate_ontology as vo  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
W3ID = "https://w3id.org/adiro/"
RENAMES = {"renames": [{"from": "aec_a", "to": "adiro_a", "reason": "test"}, {"from": "aec_b", "to": "adiro_b", "reason": "test"}]}


def ttl(module, version, priors=(), extra="", super_of=None, header=""):
    """A minimal module: one class `Thing`; `super_of` = (module, term) makes Thing a subclass of another module's term."""
    prior_lines = "".join(f"    owl:priorVersion <{W3ID}{m}/{v}> ;\n" for m, v in priors)
    sub = f" ; rdfs:subClassOf <{W3ID}{super_of[0]}#{super_of[1]}>" if super_of else ""
    return (
        f"@prefix : <{W3ID}{module}#> .\n"
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n"
        f"<{W3ID}{module}> a owl:Ontology ;\n{header}{prior_lines}"
        f"    owl:versionIRI <{W3ID}{module}/{version}> ;\n"
        f'    owl:versionInfo "{version}" .\n'
        f':Thing a owl:Class ; rdfs:label "Thing" ; rdfs:comment "A thing."{sub} .\n{extra}'
    )


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def repo(tmp_path):
    """The toy suite midway through the rename: the old modules released and still in src/, the new ones beside them."""
    write(tmp_path / "config" / "module_renames.json", json.dumps(RENAMES))
    write(tmp_path / "versions" / "aec_a" / "1.0.0" / "aec_a.ttl", ttl("aec_a", "1.0.0"))
    write(tmp_path / "versions" / "aec_a" / "2.0.0" / "aec_a.ttl", ttl("aec_a", "2.0.0", [("aec_a", "1.0.0")]))
    write(tmp_path / "versions" / "aec_b" / "1.0.0" / "aec_b.ttl", ttl("aec_b", "1.0.0", super_of=("aec_a", "Thing")))
    write(tmp_path / "src" / "aec_a.ttl", ttl("aec_a", "2.0.0", [("aec_a", "1.0.0")]))
    write(tmp_path / "src" / "aec_b.ttl", ttl("aec_b", "1.0.0", super_of=("aec_a", "Thing")))
    # a renamed module starts with the version of the old module's last release; the release cut makes it + 1 MAJOR
    write(tmp_path / "src" / "adiro_a.ttl", ttl("adiro_a", "2.0.0", [("aec_a", "1.0.0")]))
    write(tmp_path / "src" / "adiro_b.ttl", ttl("adiro_b", "1.0.0", super_of=("adiro_a", "Thing")))
    for module in ("aec_a", "aec_b", "adiro_a", "adiro_b"):
        entry = "### Changed\n\n- Renamed.\n\n" if module.startswith("adiro") else ""
        write(tmp_path / "changelogs" / f"{module}.md", f"# Changelog\n\n## [Unreleased]\n\n{entry}")
    return tmp_path


# --- the map --------------------------------------------------------------------------------------------------------

def test_the_map_gives_each_module_its_history(repo):
    renames = mr.load(repo)
    assert renames == {"adiro_a": "aec_a", "adiro_b": "aec_b"}
    assert mr.lineage(renames, "adiro_a") == ["adiro_a", "aec_a"] and mr.lineage(renames, "aec_a") == ["aec_a"]
    assert mr.predecessor(renames, "adiro_a") == "aec_a" and mr.successor(renames, "aec_a") == "adiro_a"
    assert mr.load(repo / "nowhere") == {}  # no map: no rename


@pytest.mark.parametrize("entries,problem", [
    ([{"from": "a", "to": "b"}, {"from": "a", "to": "c"}], "renamed twice"),
    ([{"from": "a", "to": "c"}, {"from": "b", "to": "c"}], "new name of two modules"),
    ([{"from": "a", "to": "b"}, {"from": "b", "to": "a"}], "cycle"),
    ([{"from": "A-1", "to": "b"}], "two different module names"),
    ([{"from": "a", "to": "a"}], "two different module names"),
])
def test_a_malformed_map_is_refused(tmp_path, entries, problem):
    write(tmp_path / "config" / "module_renames.json", json.dumps({"renames": entries}))
    with pytest.raises(ValueError, match=problem):
        mr.load(tmp_path)


def test_the_repository_map_renames_modules_that_exist():
    renames = mr.load(ROOT)
    for new, old in renames.items():
        assert (ROOT / "src" / f"{old}.ttl").is_file() or (ROOT / "versions" / old).is_dir(), f"{old}: not a module"
        assert new.startswith("adiro_"), new


def test_rename_iri_maps_the_ontology_and_its_terms_but_not_a_version_iri():
    renames = {"adiro_a": "aec_a", "adiro_c": "adiro_a"}  # a chain: aec_a -> adiro_a -> adiro_c
    assert mr.rename_iri(f"{W3ID}aec_a", renames) == f"{W3ID}adiro_c"
    assert mr.rename_iri(f"{W3ID}aec_a#Thing", renames) == f"{W3ID}adiro_c#Thing"
    assert mr.rename_iri(f"{W3ID}aec_a/2.0.0", renames) == f"{W3ID}aec_a/2.0.0"  # an earlier release keeps its IRI
    assert mr.rename_iri(f"{W3ID}aec_ab#Thing", renames) == f"{W3ID}aec_ab#Thing"  # only the exact module
    assert mr.rename_iri("http://www.w3.org/2002/07/owl#Class", renames) == "http://www.w3.org/2002/07/owl#Class"


def test_rewrite_graph_maps_every_renamed_module():
    graph = Graph().parse(data=ttl("aec_b", "1.0.0", super_of=("aec_a", "Thing")), format="turtle")
    out = mr.rewrite_graph(graph, {"adiro_a": "aec_a", "adiro_b": "aec_b"})
    assert (URIRef(f"{W3ID}adiro_b#Thing"), None, URIRef(f"{W3ID}adiro_a#Thing")) in out
    assert not any(str(t).startswith(f"{W3ID}aec_a#") or str(t).startswith(f"{W3ID}aec_b#") for triple in out for t in triple)
    assert (None, None, URIRef(f"{W3ID}aec_b/1.0.0")) in out  # the version IRI is left alone


# --- the compatibility check ----------------------------------------------------------------------------------------

def test_a_renamed_module_is_one_major_change_from_the_old_modules_last_release(repo):
    res = cd.analyze_module(repo, "adiro_a")
    assert res["baseline_module"] == "aec_a" and res["renamed_from"] == "aec_a"
    assert res["deltas"] == [("MODULE_RENAMED", f"{W3ID}adiro_a")]  # not a wall of removed and added terms
    assert (res["old_version"], res["required_bump"], res["prospective_version"], res["verdict"]) == \
        ("2.0.0", cd.BUMP_MAJOR, "3.0.0", "RELEASE_PENDING")


def test_references_to_another_renamed_module_are_compared_under_the_new_names(repo):
    res = cd.analyze_module(repo, "adiro_b")  # Thing is a subclass of aec_a:Thing before, adiro_a:Thing after
    assert res["deltas"] == [("MODULE_RENAMED", f"{W3ID}adiro_b")] and res["prospective_version"] == "2.0.0"


def test_what_changed_besides_the_name_is_listed_with_the_rename(repo):
    write(repo / "src" / "adiro_a.ttl", ttl("adiro_a", "2.0.0", [("aec_a", "1.0.0")], extra=':Other a owl:Class .\n'))
    deltas = cd.analyze_module(repo, "adiro_a")["deltas"]
    assert deltas == [("MODULE_RENAMED", f"{W3ID}adiro_a"), ("TERM_ADDED", f"{W3ID}adiro_a#Other")]


def test_a_renamed_module_with_releases_of_its_own_compares_with_its_own(repo):
    write(repo / "versions" / "adiro_a" / "3.0.0" / "adiro_a.ttl", ttl("adiro_a", "3.0.0"))
    write(repo / "src" / "adiro_a.ttl", ttl("adiro_a", "3.0.0"))
    res = cd.analyze_module(repo, "adiro_a")
    assert res["baseline_module"] == "adiro_a" and res["renamed_from"] is None and res["deltas"] == []


def test_the_old_module_leaving_src_is_retired_not_removed(repo):
    (repo / "src" / "aec_a.ttl").unlink()
    res = cd.analyze_module(repo, "aec_a")
    assert (res["verdict"], res["required_bump"], res["replaced_by"]) == ("MODULE_RETIRED", cd.BUMP_NONE, "adiro_a")
    (repo / "src" / "adiro_a.ttl").unlink()  # no successor: a removal, as before
    assert cd.analyze_module(repo, "aec_a")["verdict"] == "MODULE_REMOVED"


def test_the_pr_that_renames_diffs_the_new_module_against_the_old_one(repo, tmp_path_factory):
    base = tmp_path_factory.mktemp("base")
    write(base / "aec_a.ttl", ttl("aec_a", "2.0.0", [("aec_a", "1.0.0")]))
    res = cd.analyze_pr_change(repo, base, "adiro_a")
    assert res["renamed_from"] == "aec_a" and res["required_bump"] == cd.BUMP_MAJOR
    assert res["deltas"] == [("MODULE_RENAMED", f"{W3ID}adiro_a")]  # same terms, same header: only the name changed


def test_the_pr_that_removes_the_old_module_retires_it(repo, tmp_path_factory):
    base = tmp_path_factory.mktemp("base")
    write(base / "aec_a.ttl", ttl("aec_a", "2.0.0"))
    (repo / "src" / "aec_a.ttl").unlink()
    res = cd.analyze_pr_change(repo, base, "aec_a")
    assert res["deltas"] == [("MODULE_RETIRED", f"{W3ID}aec_a")] and res["required_bump"] == cd.BUMP_NONE


def test_the_report_says_which_module_a_renamed_one_replaces(repo):
    md = cd.to_markdown([cd.analyze_module(repo, m) for m in ("adiro_a", "aec_a")])
    assert "| `adiro_a` | `aec_a` `2.0.0` | **`3.0.0`** (MAJOR) |" in md
    assert "`adiro_a` replaces `aec_a`" in md


# --- the release cut ------------------------------------------------------------------------------------------------

def test_the_release_cut_continues_the_numbering(repo):
    entries = {e["module"]: e for e in pr.plan(repo)}
    assert set(entries) == {"adiro_a", "adiro_b"}  # the old modules are released already and unchanged
    a = entries["adiro_a"]
    assert (a["released_module"], a["released"], a["next"], a["bump"]) == ("aec_a", "2.0.0", "3.0.0", cd.BUMP_MAJOR)
    assert "| `adiro_a` | `aec_a` 2.0.0 | **3.0.0** | MAJOR |" in pr.body(list(entries.values()), repo)


def test_the_new_module_names_every_release_of_the_old_one(repo):
    assert pr.prior_version_iris(repo, "adiro_a", "3.0.0") == [f"{W3ID}aec_a/1.0.0", f"{W3ID}aec_a/2.0.0"]
    pr.apply_plan(repo, pr.plan(repo), "2026-10-21")
    text = (repo / "src" / "adiro_a.ttl").read_text(encoding="utf-8")
    assert f"owl:versionIRI <{W3ID}adiro_a/3.0.0>" in text and 'owl:versionInfo "3.0.0"' in text
    assert f"owl:priorVersion <{W3ID}aec_a/2.0.0>" in text
    graph = Graph().parse(str(repo / "src" / "adiro_a.ttl"), format="turtle")
    assert vo.find_prior_version_problems(graph, repo / "src" / "adiro_a.ttl") == []


def test_the_prior_version_check_requires_the_old_modules_releases(repo):
    path = repo / "src" / "adiro_a.ttl"
    write(path, ttl("adiro_a", "3.0.0", [("aec_a", "1.0.0")]))  # aec_a 2.0.0 is missing
    problems = vo.find_prior_version_problems(Graph().parse(str(path), format="turtle"), path)
    assert len(problems) == 1 and "release 2.0.0 of aec_a is archived but not named" in problems[0]
    write(path, ttl("adiro_a", "3.0.0", [("aec_a", "1.0.0"), ("aec_a", "2.0.0"), ("aec_b", "1.0.0")]))  # not its history
    problems = vo.find_prior_version_problems(Graph().parse(str(path), format="turtle"), path)
    assert len(problems) == 1 and "must be a version IRI of this ontology" in problems[0] and "aec_a which it replaced" in problems[0]


def test_the_release_pr_lists_the_changes_since_the_old_modules_last_tag(repo, monkeypatch):
    calls = []
    monkeypatch.setattr(pr, "_tag_exists", lambda root, tag: tag == "aec_a-v2.0.0")
    entries = [e for e in pr.plan(repo) if e["module"] == "adiro_a"]
    pr.merged_changes(repo, entries, "o/r", collect=lambda *a, **k: calls.append((a[2:], k)) or [])
    assert calls == [(("adiro_a", "2.0.0", "HEAD"), {"previous_module": "aec_a"})]


def test_the_order_puts_a_module_and_the_one_it_replaced_in_the_same_place():
    renames = {"adiro_provenance": "aec_provenance", "adiro_facade_domain": "aec_facade_domain"}
    names = ["aec_facade_domain", "adiro_geometry", "aec_provenance", "adiro_provenance"]
    assert sorted(names, key=lambda m: pr.order_key(m, renames)) == \
        ["adiro_provenance", "aec_provenance", "adiro_geometry", "aec_facade_domain"]


def test_the_names_of_a_module_and_the_superseded_modules():
    renames = {"adiro_a": "aec_a", "adiro_b": "aec_b"}
    assert mr.names(renames, "aec_a") == ["adiro_a", "aec_a"] and mr.names(renames, "adiro_a") == ["adiro_a", "aec_a"]
    assert mr.superseded(renames, ["aec_a", "adiro_a", "aec_b"]) == {"aec_a"}  # aec_b's successor is not there


# --- release notes, published checks, documentation, badges --------------------------------------------------------

def test_the_first_release_of_a_renamed_module_follows_the_old_ones_last(repo):
    tags = {"aec_a": ["aec_a-v1.0.0", "aec_a-v2.0.0"], "adiro_a": []}
    module, previous, found = rn.previous_across_renames(repo, "adiro_a", "3.0.0", "", tag_lister=lambda m: tags.get(m, []))
    assert (module, previous) == ("aec_a", "2.0.0") and "aec_a-v2.0.0" in found
    notes = rn.render("adiro_a", "3.0.0", previous, "Renamed.", [], "o/r", True, previous_module="aec_a")
    assert notes.startswith("**MAJOR release** · `aec_a` 2.0.0 → `adiro_a` 3.0.0 · ")
    assert "compare/aec_a-v2.0.0...adiro_a-v3.0.0" in notes and "Renamed from `aec_a`" in notes


def test_the_changes_of_a_renamed_module_count_both_files(monkeypatch):
    calls = []
    monkeypatch.setattr(rn, "_run", lambda args, root: calls.append(args) or type("R", (), {"stdout": "", "returncode": 0})())
    rn.collect_changes(".", "o/r", "adiro_a", "2.0.0", "adiro_a-v3.0.0", previous_module="aec_a")
    assert "aec_a-v2.0.0..adiro_a-v3.0.0" in calls[0] and calls[0][-2:] == ["src/adiro_a.ttl", "src/aec_a.ttl"]


def test_the_published_check_resolves_an_old_modules_release_under_its_own_name(repo):
    write(repo / "src" / "adiro_a.ttl", ttl("adiro_a", "3.0.0", [("aec_a", "1.0.0"), ("aec_a", "2.0.0")]))
    found = [f for f in cpv.prior_versions(repo / "src") if f[1].startswith(f"{W3ID}aec_a/")]
    assert ("aec_a", f"{W3ID}aec_a/2.0.0", "2.0.0") in found
    answer = (200, ttl("aec_a", "2.0.0"))
    assert cpv.problem_with("aec_a", f"{W3ID}aec_a/2.0.0", "2.0.0", lambda url: answer) is None


def test_the_dropdown_lists_the_old_modules_releases_after_the_new_ones(repo):
    earlier = ov.earlier_names(repo, "adiro_a")
    assert earlier == [("aec_a", ["2.0.0", "1.0.0"])]
    latest_page = ov.selector_html("3.0.0", ["3.0.0"], earlier)
    assert '<a href="../aec_a/">aec_a 2.0.0</a>' in latest_page  # the old module's newest is its main page
    assert '<a href="../aec_a/1.0.0/">aec_a 1.0.0</a>' in latest_page
    assert latest_page.index("3.0.0 (latest)") < latest_page.index("aec_a 2.0.0")
    earlier_page = ov.selector_html("3.0.0", ["4.0.0", "3.0.0"], earlier)  # one directory deeper
    assert '<a href="../../aec_a/1.0.0/">aec_a 1.0.0</a>' in earlier_page


def test_the_generated_page_of_a_renamed_module_links_the_old_modules_pages(repo):
    import types

    # generate_docs imports pyLODE at module level; the Markdown pages never call it (as in test_version_docs.py)
    for name in ("pylode", "pylode.profiles", "pylode.profiles.ontpub"):
        sys.modules.setdefault(name, types.ModuleType(name))
    sys.modules["pylode.profiles.ontpub"].__dict__.setdefault("OntPub", object)
    import generate_docs as gd

    gd.generate_ontology_markdown_pages(gd.sort_by_dependency(sorted((repo / "src").glob("*.ttl"))), repo / "docs", repo)
    page = (repo / "docs" / "ontologies" / "adiro_a.md").read_text(encoding="utf-8")
    assert "Version 2.0.0 (latest)" in page and '<a href="../aec_a/1.0.0/">aec_a 1.0.0</a>' in page
    assert "aec_a 1.0.0" not in (repo / "docs" / "ontologies" / "aec_a.md").read_text(encoding="utf-8")  # only its own


def test_a_badge_says_deprecated_once_the_deprecated_release_is_out(repo):
    assert rb.badge_json(repo, "aec_a")["message"] == "2.0.0"
    header = '    owl:deprecated true ;\n'
    write(repo / "versions" / "aec_a" / "2.0.0" / "aec_a.ttl", ttl("aec_a", "2.0.0", [("aec_a", "1.0.0")], header=header))
    badge = rb.badge_json(repo, "aec_a")
    assert (badge["message"], badge["color"]) == ("2.0.0 (deprecated)", rb.COLOR_UNRELEASED)


# --- the deprecation of a renamed module (step 2) -------------------------------------------------------------------

DEPRECATED = '    owl:deprecated true ;\n    dcterms:isReplacedBy <https://w3id.org/adiro/adiro_a> ;\n'


def deprecated_ttl():
    return "@prefix dcterms: <http://purl.org/dc/terms/> .\n" + ttl("aec_a", "2.0.0", header=DEPRECATED)


def generate_docs_module():
    import types

    for name in ("pylode", "pylode.profiles", "pylode.profiles.ontpub"):
        sys.modules.setdefault(name, types.ModuleType(name))
    sys.modules["pylode.profiles.ontpub"].__dict__.setdefault("OntPub", object)
    import generate_docs as gd
    return gd


def test_the_page_of_a_deprecated_module_names_its_replacement(tmp_path):
    import pylode_metadata as pm

    gd = generate_docs_module()
    write(tmp_path / "aec_a.ttl", deprecated_ttl())
    assert pm.replacements(tmp_path / "aec_a.ttl") == ["adiro_a"]
    alone = "\n".join(gd.deprecation_notice(tmp_path / "aec_a.ttl", [tmp_path / "aec_a.ttl"], False))
    assert alone.startswith('!!! warning "Deprecated"') and "replaced by `adiro_a`" in alone  # no page yet: no link
    both = [tmp_path / "aec_a.ttl", tmp_path / "adiro_a.ttl"]
    assert "[`adiro_a`](adiro_a.md)" in "\n".join(gd.deprecation_notice(tmp_path / "aec_a.ttl", both, False))
    assert "[`adiro_a`](../adiro_a.md)" in "\n".join(gd.deprecation_notice(tmp_path / "aec_a.ttl", both, True))
    write(tmp_path / "aec_b.ttl", ttl("aec_b", "1.0.0"))
    assert pm.replacements(tmp_path / "aec_b.ttl") is None and gd.deprecation_notice(tmp_path / "aec_b.ttl", both, False) == []


def test_the_pylode_page_of_a_deprecated_module_gets_a_row(tmp_path):
    import pylode_metadata as pm

    write(tmp_path / "aec_a.ttl", deprecated_ttl())
    write(tmp_path / "aec_b.ttl", ttl("aec_b", "1.0.0"))
    page = ('<div class="section" id="metadata"><h1>A</h1><dl><div><dt><strong>IRI</strong></dt><dd><code>'
            f"{W3ID}aec_a</code></dd></div></dl></div>")
    once = pm.add_deprecation(page, tmp_path / "aec_a.ttl")
    assert "<strong>Deprecated</strong>" in once and "<code>adiro_a</code>" in once
    assert pm.add_deprecation(once, tmp_path / "aec_a.ttl") == once  # idempotent
    assert pm.add_deprecation(page, tmp_path / "aec_b.ttl") == page  # not deprecated: unchanged


def test_every_old_module_still_in_src_is_deprecated_and_names_its_successor():
    import pylode_metadata as pm

    for new, old in mr.load(ROOT).items():
        src = ROOT / "src" / f"{old}.ttl"
        if src.is_file():
            assert pm.replacements(src) == [new], f"{old}: owl:deprecated true and dcterms:isReplacedBy <{W3ID}{new}>"


# --- the old module leaves src/ (step 4) ----------------------------------------------------------------------------

def test_a_retired_module_is_documented_from_its_final_release(repo):
    gd = generate_docs_module()
    (repo / "src" / "aec_a.ttl").unlink()
    assert mr.retired(mr.load(repo), [p.stem for p in (repo / "src").glob("*.ttl")]) == {"aec_a"}
    files = gd.find_ttl_files(repo)
    assert repo / "versions" / "aec_a" / "2.0.0" / "aec_a.ttl" in files  # its final release plays its src/ file
    gd.generate_ontology_markdown_pages(gd.sort_by_dependency(files), repo / "docs", repo)
    page = (repo / "docs" / "ontologies" / "aec_a.md").read_text(encoding="utf-8")
    assert page.startswith("---\nsearch:\n  exclude: true") and "Version 2.0.0 (latest)" in page
    assert "aec_a.md" not in (repo / "docs" / "ontologies" / ".pages").read_text(encoding="utf-8")
    assert '<a href="../aec_a/">aec_a 2.0.0</a>' in (repo / "docs" / "ontologies" / "adiro_a.md").read_text(encoding="utf-8")


def test_a_retired_module_needs_no_changelog_entry(repo):
    (repo / "src" / "aec_a.ttl").unlink()
    assert vo.missing_changelog_modules(["src/aec_a.ttl"], repo) == []
    (repo / "src" / "adiro_a.ttl").unlink()  # no successor: a removal, which needs one
    assert vo.missing_changelog_modules(["src/aec_a.ttl", "src/adiro_a.ttl"], repo) == ["adiro_a", "aec_a"]
