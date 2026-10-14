"""owl:priorVersion convention (#122): the offline validation and the post-deploy resolution check."""
import sys
from pathlib import Path

import pytest

pytest.importorskip("rdflib")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from rdflib import Graph  # noqa: E402

import check_prior_versions as cpv  # noqa: E402
import validate_ontology as vo  # noqa: E402

W3ID = "https://w3id.org/adiro/aec_x"
LEGACY = "https://burohappoldmachinelearning.github.io/ADIRO/aec_x"


def header(version, priors=(), version_iri=None):
    lines = [f"    owl:priorVersion <{W3ID}/{p}> ;" for p in priors]
    return (
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
        f"<{W3ID}> a owl:Ontology ;\n" + "\n".join(lines) + ("\n" if lines else "")
        + f"    owl:versionIRI <{version_iri or f'{W3ID}/{version}'}> ;\n"
        f'    owl:versionInfo "{version}" .\n'
    )


def make_repo(tmp_path, own, priors=(), archives=(), legacy=(), declared_wrong=()):
    (tmp_path / "src").mkdir()
    ttl = tmp_path / "src" / "aec_x.ttl"
    ttl.write_text(header(own, priors), encoding="utf-8")
    for v in archives:
        iri = f"{LEGACY}/{v}" if v in legacy else f"https://example.org/other/{v}" if v in declared_wrong else None
        folder = tmp_path / "versions" / "aec_x" / v
        folder.mkdir(parents=True)
        (folder / "aec_x.ttl").write_text(header(v, version_iri=iri), encoding="utf-8")
    return ttl


def problems(ttl):
    graph = Graph()
    graph.parse(str(ttl), format="turtle")
    return vo.find_prior_version_problems(graph, ttl)


def test_a_release_naming_all_earlier_archived_versions_is_consistent(tmp_path):
    ttl = make_repo(tmp_path, "1.2.0", priors=("1.0.0", "1.1.0"), archives=("1.0.0", "1.1.0"))
    assert problems(ttl) == []


def test_a_first_release_has_nothing_to_name(tmp_path):
    assert problems(make_repo(tmp_path, "1.0.0")) == []


def test_every_earlier_archived_release_must_be_named(tmp_path):
    ttl = make_repo(tmp_path, "1.2.0", priors=("1.1.0",), archives=("1.0.0", "1.1.0"))
    (msg,) = problems(ttl)
    assert "1.0.0 is archived but not named" in msg and "all earlier versions" in msg


def test_a_prior_version_must_be_an_archived_release(tmp_path):
    ttl = make_repo(tmp_path, "1.2.0", priors=("1.0.0", "1.1.0"), archives=("1.0.0",))
    (msg,) = problems(ttl)
    assert "1.1.0" in msg and "no archived release" in msg


def test_a_prior_version_must_be_earlier_than_the_release(tmp_path):
    ttl = make_repo(tmp_path, "1.1.0", priors=("1.1.0",), archives=("1.1.0",))
    assert any("not earlier than" in m for m in problems(ttl))


def test_a_prior_version_must_be_a_version_iri_of_this_ontology(tmp_path):
    ttl = make_repo(tmp_path, "1.1.0")
    ttl.write_text(ttl.read_text(encoding="utf-8").replace("    owl:versionIRI", "    owl:priorVersion <https://example.org/other/1.0.0> ;\n    owl:versionIRI"), encoding="utf-8")
    assert any("must be a version IRI of this ontology" in m for m in problems(ttl))


def test_a_release_made_before_the_w3id_front_door_is_accepted_but_a_stranger_is_not(tmp_path):
    (tmp_path / "legacy").mkdir()
    (tmp_path / "stranger").mkdir()
    ok = make_repo(tmp_path / "legacy", "2.0.0", priors=("1.0.0",), archives=("1.0.0",), legacy=("1.0.0",))
    assert problems(ok) == []  # the archive declares the old host form of the same version
    bad = make_repo(tmp_path / "stranger", "2.0.0", priors=("1.0.0",), archives=("1.0.0",), declared_wrong=("1.0.0",))
    (msg,) = problems(bad)
    assert "declares owl:versionIRI" in msg


# --- the post-deploy resolution check ---------------------------------------------------------------------------

def fake_site(responses):
    """A fetch function answering from {iri: (status, body)}; unknown IRIs are 404."""
    calls = []

    def fetch(url, timeout=30):
        calls.append(url)
        return responses.get(url, (404, ""))
    fetch.calls = calls
    return fetch


def src_with_priors(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "aec_x.ttl").write_text(header("1.2.0", ("1.0.0", "1.1.0")), encoding="utf-8")
    return tmp_path / "src"


def test_prior_versions_are_read_from_the_ontology_files(tmp_path):
    assert cpv.prior_versions(src_with_priors(tmp_path)) == [
        ("aec_x", f"{W3ID}/1.0.0", "1.0.0"),
        ("aec_x", f"{W3ID}/1.1.0", "1.1.0"),
    ]


def test_every_iri_resolving_to_its_release_passes(tmp_path):
    site = fake_site({f"{W3ID}/1.0.0": (200, header("1.0.0")), f"{W3ID}/1.1.0": (200, header("1.1.0"))})
    assert cpv.check(src_with_priors(tmp_path), fetch_fn=site, retries=0) == []


def test_an_unresolvable_iri_is_retried_then_reported(tmp_path):
    site = fake_site({f"{W3ID}/1.0.0": (200, header("1.0.0"))})  # 1.1.0 is a 404
    waits = []
    out = cpv.check(src_with_priors(tmp_path), fetch_fn=site, retries=2, wait=7, sleep=waits.append)
    assert len(out) == 1 and "1.1.0" in out[0] and "HTTP 404" in out[0]
    assert waits == [7, 7] and site.calls.count(f"{W3ID}/1.1.0") == 3  # first try plus two retries


def test_a_late_deploy_that_appears_on_a_retry_passes(tmp_path):
    answers = iter([(404, ""), (200, header("1.1.0"))])
    site_ok = {f"{W3ID}/1.0.0": (200, header("1.0.0"))}

    def fetch(url, timeout=30):
        return site_ok[url] if url in site_ok else next(answers)
    assert cpv.check(src_with_priors(tmp_path), fetch_fn=fetch, retries=3, wait=0, sleep=lambda s: None) == []


def test_an_iri_that_resolves_to_the_wrong_release_fails(tmp_path):
    site = fake_site({f"{W3ID}/1.0.0": (200, header("1.0.0")), f"{W3ID}/1.1.0": (200, header("1.0.0"))})
    out = cpv.check(src_with_priors(tmp_path), fetch_fn=site, retries=0)
    assert len(out) == 1 and "1.1.0" in out[0] and "declaring owl:versionIRI" in out[0]


def test_a_non_turtle_answer_fails(tmp_path):
    site = fake_site({f"{W3ID}/1.0.0": (200, "<html>not turtle</html>"), f"{W3ID}/1.1.0": (200, header("1.1.0"))})
    out = cpv.check(src_with_priors(tmp_path), fetch_fn=site, retries=0)
    assert len(out) == 1 and "not Turtle" in out[0]


def test_archived_display_configs_are_found_next_to_their_ttl(tmp_path):
    for rel in ("aec_x/1.0.0/aec_x.display.json", "aec_x/1.0.0/aec_x.ttl", "aec_x/1.1.0/aec_x.ttl", "aec_y/2.0.0/aec_y.display.json"):
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")
    assert cpv.archived_display_configs(tmp_path) == [
        ("aec_x", "1.0.0", "https://w3id.org/adiro/aec_x/1.0.0/aec_x.display.json"),
        ("aec_y", "2.0.0", "https://w3id.org/adiro/aec_y/2.0.0/aec_y.display.json"),
    ]


def test_a_display_config_must_answer_200_with_json(tmp_path):
    url = "https://w3id.org/adiro/aec_x/1.0.0/aec_x.display.json"
    assert cpv.display_config_problem(url, lambda u: (200, '{"a": 1}')) is None
    assert "HTTP 404" in cpv.display_config_problem(url, lambda u: (404, ""))
    assert "not JSON" in cpv.display_config_problem(url, lambda u: (200, "<html>"))


def test_a_missing_display_config_is_retried_and_then_reported(tmp_path):
    path = tmp_path / "aec_x" / "1.0.0" / "aec_x.display.json"
    path.parent.mkdir(parents=True)
    path.write_text("{}", encoding="utf-8")
    answers = iter([(404, ""), (404, ""), (200, "{}")])
    assert cpv.check_display_configs(tmp_path, lambda u: next(answers), retries=3, wait=0, sleep=lambda s: None) == []
    problems = cpv.check_display_configs(tmp_path, lambda u: (404, ""), retries=1, wait=0, sleep=lambda s: None)
    assert len(problems) == 1 and problems[0].startswith("aec_x 1.0.0:")
