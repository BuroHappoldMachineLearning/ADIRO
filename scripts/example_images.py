#!/usr/bin/env python3
"""
The example-image convention (#145): checks, and the build step that publishes the images.

`exampleImage` links a class or relationship to an image. The images of a module are committed once, in
`assets/<module>/exampleImage/<LocalName>_NN.<ext>`, and published at
`https://w3id.org/adiro/<module>/exampleImage/<LocalName>_NN.<ext>`. The guidance page for contributors is
docs/contribute/example-images.md (PAGE_URL); every finding points to it.

    example_images.py stage        # copy assets/<module>/exampleImage/ into docs/<module>/exampleImage/ (git-ignored)

The checks (`problems`) are pure functions over a module's graph and the `assets/` folder, used by
scripts/validate_ontology.py. A finding is (kind, blocking, item): kinds that describe a backlog (the values written
before the convention) are advisory, the limits on files that are committed under the convention are blocking.
Standard library + rdflib.
"""
import json
import re
import shutil
import struct
import sys
from collections import namedtuple
from pathlib import Path

from rdflib import Literal, URIRef

ROOT = Path(__file__).resolve().parent.parent
PROPERTY_IRI = "https://w3id.org/adiro/aec_drawing_metadata#exampleImage"
FOLDER = PROPERTY_IRI.rsplit("#", 1)[1]  # the folder is named like the annotation property (decision 10)
PAGE_URL = "https://w3id.org/adiro/contribute/example-images/"
BASES = ("https://w3id.org/adiro/", "https://burohappoldmachinelearning.github.io/ADIRO/")
ALLOWED_EXTENSIONS = (".png", ".jpg", ".webp")
SOFT_BYTES, HARD_BYTES = 250 * 1024, 500 * 1024
SOFT_PIXELS = 1600
BUDGET_WARN, BUDGET_BLOCK = 100 * 1024 * 1024, 250 * 1024 * 1024
NAME_RE = re.compile(r"^(?P<term>.+)_(?P<n>\d{2})$")
FILE_CHARS_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]*[A-Za-z0-9_-]$")  # valid inside a Turtle prefixed name
DELETED_RE = re.compile(r"^deletedAfterV\d+\.\d+\.\d+$")
RENAMES, TAKEDOWNS = "renames.json", "takedowns.txt"

Finding = namedtuple("Finding", "kind blocking item")

# kind -> (title with {n}, blocking). The titles are what validate_ontology.py shows, once per kind.
KINDS = {
    "value-form": "{n} exampleImage value(s) are not an absolute https IRI",
    "value-location": "{n} exampleImage value(s) are not in the module's `{folder}` folder",
    "file-name": "{n} example image file name(s) do not follow `<LocalName>_NN.<ext>` (lower-case extension png, jpg or webp)",
    "file-missing": "{n} exampleImage value(s) name a file that is not in `assets/<module>/{folder}/`",
    "file-orphan": "{n} file(s) in `assets/<module>/{folder}/` are used by no term",
    "file-size": "{n} example image(s) over the advised 250 KB",
    "file-size-hard": "{n} example image(s) over the 500 KB limit",
    "file-extension": "{n} example image file(s) with an extension other than lower-case png, jpg or webp",
    "file-dimensions": "{n} example image(s) wider or taller than 1600 px",
    "file-metadata": "{n} example image(s) carry embedded metadata (EXIF, GPS, text chunks)",
    "case-clash": "{n} file name(s) differ only by case",
    "budget": "the example images take {n}",
    "renames": "{n} entry(ies) of `{renames}` name a file that does not exist",
}


def local_name(iri):
    return str(iri).rsplit("#", 1)[-1].rsplit("/", 1)[-1]


def module_folder(root, module):
    return Path(root) / "assets" / module / FOLDER


# --- reading the values -----------------------------------------------------------------------------------------

def values(graph):
    """(term, value) for every exampleImage assertion in the graph, sorted."""
    return sorted(((s, o) for s, o in graph.subject_objects(URIRef(PROPERTY_IRI))), key=lambda t: (str(t[0]), str(t[1])))


def file_of(value, module):
    """The file name an https value points to in the module's folder, or ('form'|'location', None) when it does not."""
    if isinstance(value, Literal) or not isinstance(value, URIRef):
        return "form", None
    text = str(value)
    base = next((b for b in BASES if text.startswith(b)), None)
    if base is None:
        return ("location" if text.startswith("https://") else "form"), None
    rest = text[len(base):]
    prefix = f"{module}/{FOLDER}/"
    if not rest.startswith(prefix) or "/" in rest[len(prefix):] or not rest[len(prefix):]:
        return "location", None
    return "ok", rest[len(prefix):]


# --- reading the image files ------------------------------------------------------------------------------------

def image_info(path):
    """(width, height, has_metadata) of a PNG, JPEG or WebP; width/height None when they cannot be read."""
    data = Path(path).read_bytes()
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        width = height = None
        meta, pos = False, 8
        while pos + 8 <= len(data):
            length, kind = struct.unpack(">I4s", data[pos:pos + 8])
            if kind == b"IHDR":
                width, height = struct.unpack(">II", data[pos + 8:pos + 16])
            if kind in (b"tEXt", b"zTXt", b"iTXt", b"eXIf"):
                meta = True
            pos += 12 + length
        return width, height, meta
    if data[:2] == b"\xff\xd8":
        width = height = None
        meta, pos = False, 2
        while pos + 4 <= len(data):
            if data[pos] != 0xFF:
                break
            marker = data[pos + 1]
            if marker == 0xD9 or marker == 0xDA:
                break
            if marker in (0x01,) or 0xD0 <= marker <= 0xD8:
                pos += 2
                continue
            length = struct.unpack(">H", data[pos + 2:pos + 4])[0]
            if marker in (0xC0, 0xC1, 0xC2):
                height, width = struct.unpack(">HH", data[pos + 5:pos + 9])
            if marker in (0xE1, 0xED, 0xFE):  # EXIF / XMP, Photoshop, comment
                meta = True
            pos += 2 + length
        return width, height, meta
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        width = height = None
        meta, pos = False, 12
        while pos + 8 <= len(data):
            kind, length = data[pos:pos + 4], struct.unpack("<I", data[pos + 4:pos + 8])[0]
            if kind == b"VP8X":
                width = 1 + int.from_bytes(data[pos + 12:pos + 15], "little")
                height = 1 + int.from_bytes(data[pos + 15:pos + 18], "little")
            if kind in (b"EXIF", b"XMP "):
                meta = True
            pos += 8 + length + (length & 1)
        return width, height, meta
    return None, None, False


# --- the files an author may add or remove ----------------------------------------------------------------------

def load_renames(folder):
    path = Path(folder) / RENAMES
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return {}
    return {str(k): str(v) for k, v in data.items()} if isinstance(data, dict) else {}


def load_takedowns(folder):
    """Paths named in takedowns.txt (one per line, then an optional reason code)."""
    path = Path(folder) / TAKEDOWNS
    if not path.is_file():
        return set()
    return {line.split()[0] for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")}


def current_files(folder):
    """Image files directly in the module's folder (not the deletedAfter backups or the bookkeeping files)."""
    folder = Path(folder)
    if not folder.is_dir():
        return []
    return sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".gif", ".svg"))


# --- the checks -------------------------------------------------------------------------------------------------

def problems(graph, module, root=ROOT):
    """Findings for one module: its exampleImage values against the convention and the files in assets/."""
    root = Path(root)
    folder = module_folder(root, module)
    found = []
    used = set()
    for term, value in values(graph):
        label = f"`{local_name(term)}`"
        state, name = file_of(value, module)
        if state == "form":
            found.append(Finding("value-form", False, f"{label}: {value}"))
            continue
        if state == "location":
            found.append(Finding("value-location", False, f"{label}: {value}"))
            continue
        used.add(name)
        stem, ext = Path(name).stem, Path(name).suffix
        match = NAME_RE.match(stem)
        if (ext not in ALLOWED_EXTENSIONS or not match or match.group("term") != local_name(term)
                or not FILE_CHARS_RE.match(name)):
            found.append(Finding("file-name", False, f"{label}: {name}"))
        if not (folder / name).is_file():
            found.append(Finding("file-missing", False, f"{label}: {name}"))
    seen_lower = {}
    for path in current_files(folder):
        seen_lower.setdefault(path.name.lower(), []).append(path.name)
        if path.name not in used and path.name not in load_takedowns(folder):
            found.append(Finding("file-orphan", False, f"{module}/{path.name}"))
        size = path.stat().st_size
        if size > SOFT_BYTES:
            found.append(Finding("file-size-hard" if size > HARD_BYTES else "file-size", size > HARD_BYTES, f"{module}/{path.name} ({size // 1024} KB)"))
        width, height, meta = image_info(path)
        if width and height and max(width, height) > SOFT_PIXELS:
            found.append(Finding("file-dimensions", False, f"{module}/{path.name} ({width}x{height})"))
        if meta:
            found.append(Finding("file-metadata", True, f"{module}/{path.name}"))
        if path.suffix != path.suffix.lower() or path.suffix.lower() not in ALLOWED_EXTENSIONS:
            found.append(Finding("file-extension", True, f"{module}/{path.name}"))
    for names in seen_lower.values():
        if len(names) > 1:
            found.append(Finding("case-clash", True, f"{module}/" + ", ".join(names)))
    for old, new in sorted(load_renames(folder).items()):
        if not (folder / new).is_file():
            found.append(Finding("renames", True, f"{module}/{FOLDER}/{RENAMES}: {old} -> {new}"))
    return found


def budget_findings(root=ROOT):
    """The whole-repository budget for example images (decision 3): warn at 100 MB, block at 250 MB."""
    total = sum(p.stat().st_size for d in (Path(root) / "assets").glob(f"*/{FOLDER}") for p in d.rglob("*") if p.is_file())
    if total > BUDGET_WARN:
        return [Finding("budget", total > BUDGET_BLOCK, f"{total // (1024 * 1024)} MB of the 100 MB budget (blocking above 250 MB)")]
    return []


def messages(findings, module, enforce=False):
    """(errors, warnings): one message per kind, with the page link, as validate_ontology.py reports them."""
    errors, warnings = [], []
    by_kind = {}
    for f in findings:
        by_kind.setdefault(f.kind, []).append(f)
    for kind, items in by_kind.items():
        title = KINDS[kind].format(n=len(items), folder=FOLDER, renames=RENAMES)
        shown = ", ".join(i.item for i in items[:8]) + (f" ... and {len(items) - 8} more" if len(items) > 8 else "")
        text = f"{title}: {shown}. See {PAGE_URL}"
        (errors if enforce or any(i.blocking for i in items) else warnings).append(text)
    return errors, warnings


# --- the build step ---------------------------------------------------------------------------------------------

def stage(root=ROOT, docs=None):
    """Copy each assets/<module>/exampleImage/ into docs/<module>/exampleImage/ so the site publishes it.

    The copy is a build artefact: docs/*/exampleImage/ is git-ignored, so the images are committed once. The rename
    mapping is applied here: an old file name is served as a copy of the new file, so a released snapshot that names
    the old file still shows it. Takedown-listed paths are never copied.
    """
    root = Path(root)
    docs = Path(docs) if docs else root / "docs"
    staged = []
    for src in sorted((root / "assets").glob(f"*/{FOLDER}")):
        module = src.parent.name
        dest = docs / module / FOLDER
        shutil.rmtree(dest, ignore_errors=True)
        takedowns = load_takedowns(src)
        for path in sorted(p for p in src.rglob("*") if p.is_file()):
            rel = path.relative_to(src).as_posix()
            if rel in (RENAMES, TAKEDOWNS) or rel in takedowns:
                continue
            (dest / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest / rel)
            staged.append(f"{module}/{FOLDER}/{rel}")
        for old, new in sorted(load_renames(src).items()):
            if (dest / new).is_file() and not (dest / old).exists():
                (dest / old).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dest / new, dest / old)
                staged.append(f"{module}/{FOLDER}/{old} (old name of {new})")
    return staged


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv != ["stage"]:
        print(__doc__)
        return 2
    for line in stage():
        print(f"staged {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
