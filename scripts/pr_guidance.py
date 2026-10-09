#!/usr/bin/env python3
"""
Human-readable guidance for an ontology PR (#106), posted by the ADIRO Bot as its own sticky comment.

The QC comment (ontology-reasoning.yml) is the machine report. This one says what a *person* should
do about **this PR's own changes**: it only flags terms the PR adds or edits, never the standing
backlog (#87), so every item is something the author can act on and tick off.

Sections (each appears only when it has something to say):
  - To do: touched terms with no rdfs:comment, touched terms whose label is shared with another term,
    a `.ttl` change with no changelog entry (#105), unused @prefix / owl:imports in a touched module,
    and a `Closes #N` in the description that GitHub did not register;
  - Previews: an OntoCanvas link per touched module that declares classes.

Usage:
    pr_guidance.py --base-ref origin/main --repo OWNER/NAME --head-ref BRANCH --head-sha SHA
                   [--pr N] [--body-file FILE] > guidance.md

Prints the Markdown (empty output = nothing to say). The pure parts are unit-tested.
"""
import argparse
import json
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path

from rdflib import Graph, URIRef
from rdflib.compare import isomorphic
from rdflib.namespace import OWL, RDF, RDFS
from rdflib.term import BNode

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_release import unreleased_body  # noqa: E402
from validate_ontology import (  # noqa: E402
    ADIRO_NS, DESCRIPTION_PROPS, TERM_TYPES, find_unused_imports, find_unused_prefixes)

MARKER = "<!-- adiro-pr-guidance -->"
RELEASE_BRANCH = "release/next"
CLOSING_RE = re.compile(r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)", re.I)


def adiro_terms(graph):
    """ADIRO-namespace terms declared in the graph."""
    return {t for tt in TERM_TYPES for t in graph.subjects(RDF.type, tt)
            if isinstance(t, URIRef) and str(t).startswith(ADIRO_NS)}


def _signature(graph, term):
    return {(p, o) for p, o in graph.predicate_objects(term) if not isinstance(o, BNode)}


def touched_terms(base, head):
    """Terms the PR adds or whose triples differ from the base (`base` may be an empty graph)."""
    return sorted((t for t in adiro_terms(head) if _signature(base, t) != _signature(head, t)), key=str)


def undescribed(head, terms):
    return [t for t in terms if not any((t, p, None) in head for p in DESCRIPTION_PROPS)]


def label_clashes(suite, terms):
    """{term: [other terms with the same rdfs:label]} for the given terms, across the whole suite."""
    by_label = {}
    for t in adiro_terms(suite):
        for lab in suite.objects(t, RDFS.label):
            by_label.setdefault(str(lab).strip().lower(), set()).add(t)
    out = {}
    for t in terms:
        others = set()
        for lab in suite.objects(t, RDFS.label):
            others |= by_label.get(str(lab).strip().lower(), set()) - {t}
        if others:
            out[t] = sorted(others, key=str)
    return out


def local_name(term):
    return str(term).split("#")[-1]


def definition_line(ttl_text, term):
    """1-based line where the term's block starts in the Turtle source, or None."""
    name = re.escape(local_name(term))
    pat = re.compile(rf"^(?::{name}|<{re.escape(str(term))}>)\s", re.M)
    m = pat.search(ttl_text)
    return ttl_text.count("\n", 0, m.start()) + 1 if m else None


def declares_classes(graph):
    return any(isinstance(c, URIRef) and str(c).startswith(ADIRO_NS) for c in graph.subjects(RDF.type, OWL.Class))


def changelog_missing(base_changelog, head_changelog):
    """True when [Unreleased] is empty or identical to the base: this PR added no entry."""
    head = unreleased_body(head_changelog or "")
    return not head or head == unreleased_body(base_changelog or "")


def unregistered_closing(body, registered):
    """Issue numbers named after a closing keyword in `body` that GitHub did not register."""
    named = {int(n) for n in CLOSING_RE.findall(body or "")}
    return sorted(named - set(registered))


def preview_url(repo, head_ref, module):
    raw = f"https://raw.githubusercontent.com/{repo}/{head_ref}/docs/{module}.ttl"
    return "https://alelom.github.io/OntoCanvas/?onto=" + urllib.parse.quote(raw, safe="")


def render(modules, unregistered, repo):
    """`modules`: dicts with name, fixes (list of Markdown strings) and preview (URL or None)."""
    fixes = [(m["name"], f) for m in modules for f in m["fixes"]]
    previews = [(m["name"], m["preview"]) for m in modules if m["preview"]]
    if not fixes and not unregistered and not previews:
        return ""
    out = [MARKER, "## 🤖 ADIRO Bot: what to do on this PR", "",
           "Guidance on **this PR's own changes**; the machine report is the QC comment. "
           "The bot recomputes on every push, so a tick is only a reminder for you.", ""]
    if fixes or unregistered:
        out += ["### To do", ""]
        out += [f"- [ ] `{name}`: {f}" for name, f in fixes]
        for n in unregistered:
            out.append(f"- [ ] The description says it closes [#{n}](https://github.com/{repo}/issues/{n}), but GitHub did "
                       "not link it. Put the keyword at the start of a table row or line, one issue per keyword "
                       "(`Closes #1, #2` links only `#1`).")
        out.append("")
    else:
        out += ["Nothing to fix. 🎉", ""]
    if previews:
        out += ["### Previews", "", "| Module | OntoCanvas |", "|---|---|"]
        out += [f"| `{n}` | [open]({u}) |" for n, u in previews]
        out.append("")
    return "\n".join(out).rstrip("\n") + "\n"


def _git_show(ref, path, cwd):
    r = subprocess.run(["git", "show", f"{ref}:{path}"], capture_output=True, text=True, encoding="utf-8", cwd=cwd)
    return r.stdout if r.returncode == 0 else None


def _load(text):
    g = Graph()
    if text:
        g.parse(data=text, format="turtle")
    return g


def registered_closing(repo, pr):
    owner, name = repo.split("/")
    q = ("query($o:String!,$n:String!,$pr:Int!){repository(owner:$o,name:$n){pullRequest(number:$pr)"
         "{closingIssuesReferences(first:50){nodes{number}}}}}")
    r = subprocess.run(["gh", "api", "graphql", "-f", f"query={q}", "-f", f"o={owner}", "-f", f"n={name}", "-F", f"pr={pr}"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f"::warning::could not read closingIssuesReferences (gh exit {r.returncode}); skipping that check", file=sys.stderr)
        return None
    nodes = json.loads(r.stdout)["data"]["repository"]["pullRequest"]["closingIssuesReferences"]["nodes"]
    return [n["number"] for n in nodes]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-ref", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--head-ref", required=True)
    ap.add_argument("--head-sha", required=True)
    ap.add_argument("--pr", type=int)
    ap.add_argument("--body-file")
    ap.add_argument("--root", default=".")
    args = ap.parse_args(argv)
    root = Path(args.root)

    if args.head_ref == RELEASE_BRANCH:  # the bot's own cut: nothing for a person to do here
        return
    changed = subprocess.run(["git", "diff", "--name-only", f"{args.base_ref}...HEAD", "--", "src"],
                             capture_output=True, text=True, cwd=root).stdout.split()
    texts = {f"src/{p.name}": p.read_text(encoding="utf-8") for p in sorted((root / "src").glob("*.ttl"))}
    suite = Graph()
    for text in texts.values():
        suite.parse(data=text, format="turtle")

    modules = []
    for path in (p for p in changed if p in texts):
        module = Path(path).stem
        head = _load(texts[path])
        base = _load(_git_show(args.base_ref, path, root))
        if isomorphic(base, head):
            continue
        touched = touched_terms(base, head)
        fixes = []
        for t in undescribed(head, touched):
            ln = definition_line(texts[path], t)
            where = f" ([line {ln}](https://github.com/{args.repo}/blob/{args.head_sha}/{path}#L{ln}))" if ln else ""
            fixes.append(f"`{local_name(t)}`{where} has no `rdfs:comment`. Add a short definition in your own words "
                         f"(convention: [#87](https://github.com/{args.repo}/issues/87)).")
        for t, others in label_clashes(suite, touched).items():
            fixes.append(f"`{local_name(t)}` shares its `rdfs:label` with " + ", ".join(f"`{local_name(o)}`" for o in others)
                         + ". Labels are unique across classes so the docs and label search are not ambiguous.")
        cl_path = f"changelogs/{module}.md"
        head_cl = (root / cl_path).read_text(encoding="utf-8") if (root / cl_path).is_file() else ""
        if changelog_missing(_git_show(args.base_ref, cl_path, root), head_cl):
            fixes.append(f"this PR changes the ontology but adds no entry under `[Unreleased]` in `{cl_path}`. "
                         f"Record the change there; the next release cut reads it ([#105](https://github.com/{args.repo}/issues/105)).")
        # only what this PR introduces: a module's standing leftovers are not the author's to fix here
        base_text = _git_show(args.base_ref, path, root) or ""
        fixes += [f"unused `@prefix` {pfx}: delete the declaration."
                  for pfx in sorted(set(find_unused_prefixes(head, texts[path])) - set(find_unused_prefixes(base, base_text)))]
        fixes += [f"`owl:imports <{imp}>` but no term of it is used: drop the import or use it."
                  for imp in sorted(set(find_unused_imports(head)) - set(find_unused_imports(base)))]
        modules.append({"name": module, "fixes": fixes,
                        "preview": preview_url(args.repo, args.head_ref, module) if declares_classes(head) else None})

    unregistered = []
    if args.pr and args.body_file and Path(args.body_file).is_file():
        registered = registered_closing(args.repo, args.pr)
        if registered is not None:
            unregistered = unregistered_closing(Path(args.body_file).read_text(encoding="utf-8"), registered)
    sys.stdout.buffer.write(render(modules, unregistered, args.repo).encode("utf-8"))


if __name__ == "__main__":
    main()
