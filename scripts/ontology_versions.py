#!/usr/bin/env python3
"""
Version list and version selector for the per-ontology documentation pages (#124).

Every ADIRO ontology has one documentation page per version: the latest one at
``/ontologies/<module>/`` and each earlier release at ``/ontologies/<module>/<version>/``. This module holds
the pure logic generate_docs.py needs for that (no pyLODE, no ttl2md), so it can be unit-tested on its own:

- which versions exist (the releases archived under ``versions/<module>/``, plus the version declared in
  ``src/<module>.ttl``, which is the latest one while its snapshot has not been taken yet);
- which is the latest, and the status shown next to a selected version: "latest", or "<latest> available";
- the dropdown that switches between the versions' pages (plain HTML, no script).
"""
import html
import re
from pathlib import Path

SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
VERSION_INFO_RE = re.compile(r'owl:versionInfo\s+"([^"]+)"')


def version_key(version):
    return tuple(int(x) for x in SEMVER_RE.match(version).groups())


def archived_versions(repo_root, module):
    """Versions archived under versions/<module>/ (the published releases), lowest first."""
    base = Path(repo_root) / "versions" / module
    if not base.is_dir():
        return []
    found = [d.name for d in base.iterdir() if d.is_dir() and SEMVER_RE.match(d.name) and (d / f"{module}.ttl").is_file()]
    return sorted(found, key=version_key)


def declared_version(ttl_file):
    """The owl:versionInfo a Turtle file declares, or None."""
    match = VERSION_INFO_RE.search(Path(ttl_file).read_text(encoding="utf-8"))
    return match.group(1) if match else None


def version_list(archived, declared):
    """Every version of a module, newest first: the archived releases plus the declared one."""
    versions = set(archived)
    if declared and SEMVER_RE.match(declared):
        versions.add(declared)
    return sorted(versions, key=version_key, reverse=True)


def status(selected, latest):
    """'latest' for the newest version, '<latest> available' for any other."""
    return "latest" if selected == latest else f"{latest} available"


def button_text(selected, latest):
    return f"Version {selected} ({status(selected, latest)})"


def _href(selected, latest, target):
    """Relative link from the page of `selected` to the page of `target`.

    The latest page lives at /ontologies/<module>/ and every other version at /ontologies/<module>/<version>/,
    so the links are relative and work under any base path (including a local `mkdocs serve`).
    """
    if target == selected:
        return "./"
    if selected == latest:
        return f"{target}/"
    return "../" if target == latest else f"../{target}/"


def selector_html(selected, versions):
    """The dropdown button and its list of versions. One element per line, no blank line (it is embedded in Markdown)."""
    latest = versions[0]
    items = []
    for version in versions:
        label = html.escape(version + (" (latest)" if version == latest else ""))
        current = ' class="adiro-version-current" aria-current="page"' if version == selected else ""
        items.append(f'<li><a href="{_href(selected, latest, version)}"{current}>{label}</a></li>')
    return "\n".join([
        '<details class="adiro-version">',
        f'<summary class="md-button">{html.escape(button_text(selected, latest))}</summary>',
        "<ul>",
        *items,
        "</ul>",
        "</details>",
    ])


def version_page_front_matter():
    """Front matter of a page for an earlier version: kept out of the site search so a term is not found once per version."""
    return "---\nsearch:\n  exclude: true\n---\n\n"
