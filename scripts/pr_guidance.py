#!/usr/bin/env python3
"""
Human-readable guidance for an ontology PR (#106), posted by the ADIRO Bot as its own sticky comment.

The QC comment (ontology-reasoning.yml) is the machine report. This one says what a *person* should
do about **this PR's own changes**: it only flags terms the PR adds or edits, never the standing
backlog (#87), so every item is something the author can act on and tick off.

Findings are grouped by issue type (#144): each type's advice is said once, followed by its items, collapsed
behind <details> when there are more than COLLAPSE_OVER. A new check adds one `Kind` to `kinds()`.

Sections (each appears only when it has something to say):
  - To do: touched terms with no rdfs:comment, touched terms whose label is shared with another term,
    a `.ttl` change with no changelog entry (#105), unused @prefix / owl:imports in a touched module,
    and a `Closes #N` in the description that GitHub did not register;
  - Previews: an OntoCanvas link per touched module that declares classes.

Usage:
    pr_guidance.py --base-ref origin/main --repo OWNER/NAME --head-ref BRANCH --head-sha SHA
                   [--head-repo OWNER/NAME] [--worktree] [--pr N] [--body-file FILE] > guidance.md

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
import example_images  # noqa: E402
import module_renames  # noqa: E402
from ontology_versions import archived_versions, version_key  # noqa: E402
from validate_ontology import (  # noqa: E402
    ADIRO_NS, DESCRIPTION_PROPS, TERM_TYPES, find_unused_imports, find_unused_prefixes, missing_changelog_modules)

MARKER = "<!-- adiro-pr-guidance -->"
RELEASE_BRANCH = "release/next"
CLOSING_RE = re.compile(r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)", re.I)


def adiro_terms(graph):
    """ADIRO-namespace terms declared in the graph."""
    return {t for tt in TERM_TYPES for t in graph.subjects(RDF.type, tt)
            if isinstance(t, URIRef) and str(t).startswith(ADIRO_NS)}


def _node(graph, node, seen=()):
    """A comparable form of an object: IRIs and literals as they are, a blank node as the (recursive) set of its
    own triples, so an edit inside an OWL restriction or list changes the term that owns it."""
    if not isinstance(node, BNode):
        return node
    if node in seen:  # a cycle through blank nodes
        return "_:cycle"
    return frozenset((p, _node(graph, o, seen + (node,))) for p, o in graph.predicate_objects(node))


def _signature(graph, term):
    return {(p, _node(graph, o)) for p, o in graph.predicate_objects(term)}


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


def new_classes_without_image(base, head):
    """New ADIRO classes (no triples in the base) that carry no exampleImage (#145)."""
    props = [URIRef(iri) for iri in example_images.PROPERTY_IRIS]
    return [t for t in sorted(adiro_terms(head), key=str)
            if (t, RDF.type, OWL.Class) in head and not _signature(base, t) and not any((t, p, None) in head for p in props)]


def unregistered_closing(body, registered):
    """Issue numbers named after a closing keyword in `body` that GitHub did not register."""
    named = {int(n) for n in CLOSING_RE.findall(body or "")}
    return sorted(named - set(registered))


def preview_url(repo, head_ref, module):
    raw = f"https://raw.githubusercontent.com/{repo}/{head_ref}/docs/{module}.ttl"
    return "https://alelom.github.io/OntoCanvas/?onto=" + urllib.parse.quote(raw, safe="")


# One entry per issue type. A finding is a (kind, item) pair; render() says the advice once per kind and lists the items,
# collapsed behind <details> when there are more than COLLAPSE_OVER (#144). A new check adds one entry here.
COLLAPSE_OVER = 5


class Kind:
    def __init__(self, key, title, advice, noun, level="required"):
        self.key, self.title, self.advice, self.noun, self.level = key, title, advice, noun, level

    def heading(self, n):
        things = self.noun[0] if n == 1 else self.noun[1]
        return f"**{self.title.format(n=n, things=things)}.** {self.advice}"


def kinds(repo):
    issue = f"https://github.com/{repo}/issues"
    return [
        Kind("undescribed", "No `rdfs:comment` on {n} {things}",
             f"Add a short definition in your own words (convention: [#87]({issue}/87)).", ("term", "terms")),
        Kind("label-clash", "{n} {things} share an `rdfs:label` with another term",
             "Labels are unique across classes so the docs and label search are not ambiguous.", ("term", "terms")),
        Kind("removed", "{n} ontology {things} removed or renamed",
             "That is a breaking change: say so in the changelog and check the dependent modules.", ("file", "files")),
        Kind("changelog", "The ontology changed but {n} {things} did not",
             f"Add an entry under `[Unreleased]`; it becomes the release notes ([#105]({issue}/105)).",
             ("changelog", "changelogs")),
        Kind("unused-prefix", "{n} unused `@prefix` {things}", "Delete the declaration.", ("declaration", "declarations")),
        Kind("unused-import", "{n} `owl:imports` of a module that no axiom of this file uses",
             "Find out why it is there before dropping it: see `config/module_imports.json` and the ORSD. An import can be a "
             "dependency used as a data pattern (a property with no domain): then state the use with an axiom and keep it, "
             "and drop the import only if the pin says it is not needed ([#195]("
             f"{issue}/195)).", ("import", "imports")),
        Kind("no-example-image", "{n} new {things} without an example image",
             f"Consider adding one (a suggestion, not a requirement): [how to add an example image]({example_images.PAGE_URL}).",
             ("class", "classes"), level="suggestion"),
        Kind("closing", "The description names {n} {things} with a closing keyword that GitHub did not link",
             "Put the keyword at the start of a table row or line, one issue per keyword (`Closes #1, #2` links only `#1`).",
             ("issue", "issues")),
    ]


class Caution:
    """A serious finding, shown at the top as a red alert. `detect(changes, ctx)` returns the items (Markdown strings)."""

    def __init__(self, key, title, explanation, detect):
        self.key, self.title, self.explanation, self.detect = key, title, explanation, detect


def _exampleimage_declaration_removed(changes, ctx):
    props = [URIRef(iri) for iri in example_images.PROPERTY_IRIS]
    return [f"`{c['module']}`: the declaration of `{example_images.FOLDER}` is removed or renamed" for c in changes
            if any((p, RDF.type, OWL.AnnotationProperty) in c["base"] and (p, RDF.type, OWL.AnnotationProperty) not in c["head"]
                   for p in props)]


def _import_removed(changes, ctx):
    out = []
    for c in changes:
        base = {str(o) for o in c["base"].objects(None, OWL.imports)}
        head = {str(o) for o in c["head"].objects(None, OWL.imports)}
        out += [f"`{c['module']}`: the import of `{i.rsplit('/', 1)[-1]}` is removed" for i in sorted(base - head)]
    return out


def cautions():
    """The registry of cautions; a new one is one entry here (its detection function, title and explanation)."""
    return [
        Caution("import-removed", "An `owl:imports` is removed",
                "An import is a stated dependency, and it can be one the module's own axioms do not show (a data pattern, a "
                "property with no domain). Check `config/module_imports.json` and the ORSD for why it exists, edit the pin with "
                "the reason if the removal is intended, and say in the changelog that it was removed "
                "([#195](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/195)).",
                _import_removed),
        Caution("exampleimage-renamed", "The `exampleImage` annotation property is removed or renamed",
                f"The images folders, every value and the published image URLs are named after this property. Renaming it means "
                f"renaming the `{example_images.FOLDER}` folders in every module, listing the old folder in `renames.json` so "
                f"the old URLs keep working, and saying so in the changelog ([how]({example_images.PAGE_URL})).",
                _exampleimage_declaration_removed),
    ]


def render_caution(caution, items):
    out = ["> [!CAUTION]", f"> **{caution.title}**", f"> {caution.explanation}", ">"]
    out += [f"> - {i}" for i in items]
    return out + [""]


def render_group(kind, items):
    """Markdown for one issue type: the heading with its advice, then the items (collapsed when there are many)."""
    items = list(items)
    out = [kind.heading(len(items)), ""]
    if len(items) > COLLAPSE_OVER:
        noun = kind.noun[1]
        out += [f"<details><summary>Show the {len(items)} {noun}</summary>", ""]
        out += [f"- {i}" for i in items]
        out += ["", "</details>", ""]
    else:
        out += [f"- {i}" for i in items] + [""]
    return out


def render(findings, previews, repo, caution_items=()):
    """`findings`: (kind key, item Markdown) pairs; `previews`: (module, OntoCanvas URL) pairs;
    `caution_items`: (caution key, item Markdown) pairs, shown first as red alerts."""
    by_kind, by_caution = {}, {}
    for key, item in findings:
        by_kind.setdefault(key, []).append(item)
    for key, item in caution_items:
        by_caution.setdefault(key, []).append(item)
    if not by_kind and not by_caution:  # nothing to say: no comment at all (previews alone are not worth one)
        return ""
    required = [k for k in kinds(repo) if k.level == "required" and k.key in by_kind]
    suggestions = [k for k in kinds(repo) if k.level == "suggestion" and k.key in by_kind]
    unknown = set(by_kind) - {k.key for k in kinds(repo)}
    assert not unknown, f"findings of an unregistered kind: {sorted(unknown)}"
    out = [MARKER]
    for caution in cautions():
        if caution.key in by_caution:
            out += render_caution(caution, by_caution.pop(caution.key))
    assert not by_caution, f"cautions of an unregistered kind: {sorted(by_caution)}"
    if required:
        out += ["## Required improvements", ""]
        for kind in required:
            out += render_group(kind, by_kind[kind.key])
    if suggestions:
        out += ["### Suggestions" if required else "## Suggestions", ""]
        for kind in suggestions:
            out += render_group(kind, by_kind[kind.key])
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
    ap.add_argument("--head-repo", help="repository holding the head branch (a fork); default: --repo")
    ap.add_argument("--worktree", action="store_true",
                    help="the working tree already holds the PR's src/ and changelogs/ over the base (fork PRs, "
                         "pull_request_target): diff the working tree against --base-ref instead of HEAD")
    ap.add_argument("--head-sha", required=True)
    ap.add_argument("--pr", type=int)
    ap.add_argument("--body-file")
    ap.add_argument("--root", default=".")
    args = ap.parse_args(argv)
    root = Path(args.root)

    # The bot's own cut (a branch of THIS repository) needs nothing from a person; a fork's branch that happens
    # to be called release/next is an ordinary PR.
    if args.head_ref == RELEASE_BRANCH and (args.head_repo or args.repo) == args.repo:
        return
    # The comparison point is the merge base, so edits that landed on the base branch after this PR branched
    # are not mistaken for the PR's own (--worktree callers already pass a merge-base SHA).
    base_commit = args.base_ref
    if not args.worktree:
        mb = subprocess.run(["git", "merge-base", args.base_ref, "HEAD"], capture_output=True, text=True, cwd=root)
        base_commit = mb.stdout.strip() or args.base_ref
    spec = args.base_ref if args.worktree else f"{args.base_ref}...HEAD"
    changed = subprocess.run(["git", "diff", "--name-only", "--no-renames", spec, "--", "src", "changelogs"],
                             capture_output=True, text=True, cwd=root).stdout.split()
    no_changelog = set(missing_changelog_modules(changed))  # the same check as validate_ontology.py (#105)
    texts = {f"src/{p.name}": p.read_text(encoding="utf-8") for p in sorted((root / "src").glob("*.ttl"))}
    # A module that a renamed one replaces, kept in src/ for one more cycle, repeats every term of its successor under
    # the old IRIs (#171): its labels are not clashes, so the suite the labels are compared in leaves it out.
    renames = module_renames.load(root)
    retiring = module_renames.superseded(renames, [Path(p).stem for p in texts])
    suite = Graph()
    for path, text in texts.items():
        if Path(path).stem not in retiring:
            suite.parse(data=text, format="turtle")

    changes = []
    findings, previews = [], []  # findings: (kind key, item Markdown); each kind's advice is said once by render()
    for path in (p for p in changed if re.fullmatch(r"src/[^/]+\.ttl", p)):  # includes deleted modules
        module = Path(path).stem
        head = _load(texts.get(path))
        base_text = _git_show(base_commit, path, root)
        old_name = module_renames.predecessor(renames, module)
        if base_text is None and old_name:  # a renamed module: what it changes is measured against the module it replaces
            base_text = module_renames.rewrite_text(_git_show(base_commit, f"src/{old_name}.ttl", root) or "", renames) or None
        base = _load(base_text)
        if isomorphic(base, head):
            continue
        touched = touched_terms(base, head)
        for t in undescribed(head, touched):
            ln = definition_line(texts[path], t)
            where = f", [line {ln}](https://github.com/{args.repo}/blob/{args.head_sha}/{path}#L{ln})" if ln else ""
            findings.append(("undescribed", f"`{local_name(t)}` (`{module}`{where})"))
        for t, others in label_clashes(suite, touched).items():
            findings.append(("label-clash", f"`{local_name(t)}` (`{module}`) shares it with "
                                            + ", ".join(f"`{local_name(o)}`" for o in others)))
        if path not in texts:
            findings.append(("removed", f"`{path}`"))
        if module in no_changelog:
            findings.append(("changelog", f"`changelogs/{module}.md`"))
        # only what this PR introduces: a module's standing leftovers are not the author's to fix here
        base_text = base_text or ""
        if path in texts:
            findings += [("unused-prefix", f"`@prefix` {pfx} (`{module}`)")
                         for pfx in sorted(set(find_unused_prefixes(head, texts[path])) - set(find_unused_prefixes(base, base_text)))]
            findings += [("unused-import", f"`owl:imports <{imp}>` (`{module}`)")
                         for imp in sorted(set(find_unused_imports(head)) - set(find_unused_imports(base)))]
        if path in texts:
            findings += [("no-example-image", f"`{local_name(t)}` (`{module}`)") for t in new_classes_without_image(base, head)]
        changes.append({"module": module, "base": base, "head": head})
        if path in texts and declares_classes(head):
            previews.append((module, preview_url(args.head_repo or args.repo, args.head_ref, module)))

    if args.pr and args.body_file and Path(args.body_file).is_file():
        registered = registered_closing(args.repo, args.pr)
        if registered is not None:
            findings += [("closing", f"[#{n}](https://github.com/{args.repo}/issues/{n})")
                         for n in unregistered_closing(Path(args.body_file).read_text(encoding="utf-8"), registered)]
    caution_items = [(c.key, item) for c in cautions() for item in c.detect(changes, None)]
    sys.stdout.buffer.write(render(findings, previews, args.repo, caution_items).encode("utf-8"))


if __name__ == "__main__":
    main()
