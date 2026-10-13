#!/usr/bin/env python3
"""
Check that every owl:priorVersion IRI in src/*.ttl resolves to the release it names (#122).

Run after a deploy (generate-deploy-docs.yml, job `verify-prior-versions`), because only the published
site can answer "does this IRI resolve?". For each owl:priorVersion IRI it requests the IRI with
`Accept: text/turtle`, follows the redirects, requires HTTP 200, parses the answer and requires the
file's owl:versionIRI to be that IRI (or its legacy host form, see validate_ontology.py). The offline
half of the convention (the archive exists, the list is complete) is in validate_ontology.py.

Usage:
    check_prior_versions.py [--src DIR] [--retries N] [--wait SECONDS]

A just-deployed site can lag the deploy by a minute, so a failing IRI is retried before it is reported.
Exit code 1 if any IRI does not resolve to its release. stdlib + rdflib.
"""
import argparse
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from rdflib import Graph
from rdflib.namespace import OWL, RDF

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_ontology import accepted_version_iris  # noqa: E402


def prior_versions(src_dir):
    """(module, iri, version) for every owl:priorVersion in the ontology files under `src_dir`."""
    found = []
    for ttl in sorted(Path(src_dir).glob("*.ttl")):
        graph = Graph()
        graph.parse(str(ttl), format="turtle")
        for ont in graph.subjects(RDF.type, OWL.Ontology):
            for iri in sorted(str(o) for o in graph.objects(ont, OWL.priorVersion)):
                found.append((ttl.stem, iri, iri.rsplit("/", 1)[-1]))
    return found


def fetch(url, timeout=30):
    """(HTTP status after redirects, body text); status 0 means the request itself failed."""
    request = urllib.request.Request(url, headers={"Accept": "text/turtle"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as err:
        return err.code, ""
    except (urllib.error.URLError, TimeoutError, OSError):
        return 0, ""


def problem_with(module, iri, version, fetch_fn=fetch):
    """Why `iri` does not resolve to the release it names, or None if it does."""
    status, body = fetch_fn(iri)
    if status != 200:
        return f"<{iri}> does not resolve (HTTP {status or 'no answer'})"
    graph = Graph()
    try:
        graph.parse(data=body, format="turtle")
    except Exception as err:  # noqa: BLE001 - any parse failure means it is not the Turtle release
        return f"<{iri}> resolves but is not Turtle ({type(err).__name__})"
    declared = {str(o) for o in graph.objects(None, OWL.versionIRI)}
    if not declared & accepted_version_iris(module, version):
        return f"<{iri}> resolves to a file declaring owl:versionIRI {sorted(declared)}"
    return None


def check(src_dir, fetch_fn=fetch, retries=5, wait=20, sleep=time.sleep):
    """List of problems (empty if every owl:priorVersion IRI resolves to its release)."""
    problems = []
    for module, iri, version in prior_versions(src_dir):
        problem = problem_with(module, iri, version, fetch_fn)
        attempt = 1
        while problem and attempt <= retries:  # the site can lag a fresh deploy
            sleep(wait)
            problem = problem_with(module, iri, version, fetch_fn)
            attempt += 1
        print(f"{'FAIL' if problem else 'ok  '} {module}: {iri}" + (f"\n     {problem}" if problem else ""))
        if problem:
            problems.append(f"{module}: {problem}")
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(Path(__file__).resolve().parent.parent / "src"))
    ap.add_argument("--retries", type=int, default=5)
    ap.add_argument("--wait", type=int, default=20)
    args = ap.parse_args(argv)
    problems = check(args.src, retries=args.retries, wait=args.wait)
    if problems:
        print(f"\n{len(problems)} owl:priorVersion IRI(s) do not resolve to their release.", file=sys.stderr)
        sys.exit(1)
    print("\nEvery owl:priorVersion IRI resolves to its release.")


if __name__ == "__main__":
    main()
