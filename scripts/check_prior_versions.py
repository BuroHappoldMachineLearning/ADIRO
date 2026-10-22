#!/usr/bin/env python3
"""
Check that every owl:priorVersion IRI in src/*.ttl resolves to the release it names (#122).

Run after a deploy (post-deploy-checks.yml, job `verify-prior-versions`, #217), because only the published
site can answer "does this IRI resolve?". For each owl:priorVersion IRI it requests the IRI with
`Accept: text/turtle`, follows the redirects, requires HTTP 200, parses the answer and requires the
file's owl:versionIRI to be that IRI (or its legacy host form, see validate_ontology.py). The offline
half of the convention (the archive exists, the list is complete) is in validate_ontology.py.

It also checks that every example image an archived release names is served (#154): an image answers 200 with an image
content type, and a taken-down address serves the placeholder of the version it was removed after.

It also checks that every archived release's display config (versions/<module>/<semver>/<module>.display.json, #140) is
served at the release's IRI path, so an earlier release opens in the viewer with its own layout.

Usage:
    check_prior_versions.py [--src DIR] [--versions DIR] [--assets DIR] [--retries N] [--wait SECONDS]

A just-deployed site can lag the deploy by a minute, so a failing IRI is retried before it is reported.
Exit code 1 if any IRI does not resolve to its release. stdlib + rdflib.
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from rdflib import Graph
from rdflib.namespace import OWL, RDF

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_ontology import accepted_version_iris  # noqa: E402
import example_images  # noqa: E402

SITE = "https://w3id.org/adiro"


def prior_versions(src_dir):
    """(module, iri, version) for every owl:priorVersion in the ontology files under `src_dir`.

    The module is the one the IRI names (``…/<module>/<version>``), not the file's: a renamed module also names the
    releases of the module it replaced (#171).
    """
    found = []
    for ttl in sorted(Path(src_dir).glob("*.ttl")):
        graph = Graph()
        graph.parse(str(ttl), format="turtle")
        for ont in graph.subjects(RDF.type, OWL.Ontology):
            for iri in sorted(str(o) for o in graph.objects(ont, OWL.priorVersion)):
                module, version = iri.rsplit("/", 2)[-2:]
                found.append((module, iri, version))
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


def archived_display_configs(versions_dir):
    """(module, version, url) for every archived display config under `versions_dir`."""
    found = []
    for path in sorted(Path(versions_dir).glob("*/*/*.display.json")):
        version, module = path.parent.name, path.parent.parent.name
        if path.name == f"{module}.display.json":
            found.append((module, version, f"https://w3id.org/adiro/{module}/{version}/{module}.display.json"))
    return found


def display_config_problem(url, fetch_fn=fetch):
    """Why the archived display config at `url` is not served, or None if it is."""
    status, body = fetch_fn(url)
    if status != 200:
        return f"<{url}> does not resolve (HTTP {status or 'no answer'})"
    try:
        json.loads(body)
    except ValueError:
        return f"<{url}> resolves but is not JSON"
    return None


def check_display_configs(versions_dir, fetch_fn=fetch, retries=5, wait=20, sleep=time.sleep):
    """List of problems (empty if every archived display config is served)."""
    problems = []
    for module, version, url in archived_display_configs(versions_dir):
        problem = display_config_problem(url, fetch_fn)
        attempt = 1
        while problem and attempt <= retries:  # the site can lag a fresh deploy
            sleep(wait)
            problem = display_config_problem(url, fetch_fn)
            attempt += 1
        print(f"{'FAIL' if problem else 'ok  '} {module} {version}: {url}" + (f"\n     {problem}" if problem else ""))
        if problem:
            problems.append(f"{module} {version}: {problem}")
    return problems


def fetch_image(url, timeout=30):
    """(HTTP status after redirects, content type, body bytes); status 0 means the request itself failed."""
    request = urllib.request.Request(url, headers={"Accept": "image/*"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.headers.get("Content-Type", ""), response.read()
    except urllib.error.HTTPError as err:
        return err.code, "", b""
    except (urllib.error.URLError, TimeoutError, OSError):
        return 0, "", b""


def archived_example_images(versions_dir, assets_dir):
    """(url, versions, expected) for every example image an archived release names, one entry per address.

    `expected` is the bytes of the placeholder when the address is a takedown (it must serve that), else None.
    """
    versions_dir, assets_dir = Path(versions_dir), Path(assets_dir)
    root = versions_dir.parent
    found = {}
    for module_dir in sorted(p for p in versions_dir.iterdir() if p.is_dir()):
        module = module_dir.name
        folder = assets_dir / module / example_images.FOLDER
        entries = example_images.load_takedown_entries(folder)
        for version, _, kind, target in example_images.snapshot_values(root, module):
            url = f"{SITE}{target}" if kind == "legacy" else f"{SITE}/{module}/{example_images.FOLDER}/{target}"
            expected = None
            version_taken = entries.get(target, (None, None))[1]
            if version_taken:
                holder = example_images.placeholder_file(folder, version_taken)
                expected = holder.read_bytes() if holder.is_file() else None
            versions = found.setdefault(url, ([], expected))[0]
            if f"{module} {version}" not in versions:
                versions.append(f"{module} {version}")
    return [(url, versions, expected) for url, (versions, expected) in sorted(found.items())]


def example_image_problem(url, expected, fetch_fn=fetch_image):
    """Why the example image at `url` is not served as it should be, or None if it is."""
    status, content_type, body = fetch_fn(url)
    if status != 200:
        return f"<{url}> does not resolve (HTTP {status or 'no answer'})"
    if not content_type.lower().startswith("image/"):
        return f"<{url}> resolves but is not an image ({content_type or 'no content type'})"
    if expected is not None and body != expected:
        return f"<{url}> is taken down, but it does not serve the placeholder"
    return None


def check_example_images(versions_dir, assets_dir, fetch_fn=fetch_image, retries=5, wait=20, sleep=time.sleep):
    """List of problems (empty if every example image an archived release names is served)."""
    problems = []
    for url, versions, expected in archived_example_images(versions_dir, assets_dir):
        problem = example_image_problem(url, expected, fetch_fn)
        attempt = 1
        while problem and attempt <= retries:  # the site can lag a fresh deploy
            sleep(wait)
            problem = example_image_problem(url, expected, fetch_fn)
            attempt += 1
        print(f"{'FAIL' if problem else 'ok  '} {', '.join(versions)}: {url}" + (f"\n     {problem}" if problem else ""))
        if problem:
            problems.append(f"{', '.join(versions)}: {problem}")
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(Path(__file__).resolve().parent.parent / "src"))
    ap.add_argument("--versions", default=str(Path(__file__).resolve().parent.parent / "versions"))
    ap.add_argument("--assets", default=str(Path(__file__).resolve().parent.parent / "assets"))
    ap.add_argument("--retries", type=int, default=5)
    ap.add_argument("--wait", type=int, default=20)
    args = ap.parse_args(argv)
    problems = check(args.src, retries=args.retries, wait=args.wait)
    config_problems = check_display_configs(args.versions, retries=args.retries, wait=args.wait)
    image_problems = check_example_images(args.versions, args.assets, retries=args.retries, wait=args.wait)
    if problems or config_problems or image_problems:
        print(f"\n{len(problems)} owl:priorVersion IRI(s) do not resolve to their release, "
              f"{len(config_problems)} archived display config(s) are not served, "
              f"{len(image_problems)} archived example image(s) are not served.", file=sys.stderr)
        sys.exit(1)
    print("\nEvery owl:priorVersion IRI resolves to its release, and every archived display config and example image is served.")


if __name__ == "__main__":
    main()
