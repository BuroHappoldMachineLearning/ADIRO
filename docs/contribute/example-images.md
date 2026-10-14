# Example images

An **example image** shows what a class or relationship looks like on a drawing. It is linked to the term with the
`exampleImage` annotation property, and it is part of the ontology: the documentation pages show it, and downstream
tools (annotation tools, machine-learning workflows) read it by its URI. This page is how to add one.

## What makes a good image

- **It shows the term, clearly.** Crop the source drawing to the part being illustrated when the drawing shows other
  things as well.
- **It is small.** Aim for 250 KB or less; 500 KB is the limit. The documentation shows images 500 px wide, so
  1600 px on the longest side is more than enough. PNG, JPG and WebP are accepted.
- **It is cleared for publication, and shows nothing private.** The image is published in a public repository and
  stays in its history. Before adding it:
    - check that you may publish it (see the statement below);
    - obscure or remove private information: names, addresses, project or client identifiers, signatures;
    - strip embedded metadata (EXIF, GPS position, author, software notes). Most image editors have an "export without
      metadata" option; the check reports an image that still carries metadata.

## Where it goes and what it is called

Each module has one folder, named like the annotation property:

```
assets/<module>/exampleImage/<LocalName>_NN.<ext>
```

- `<module>` is the ontology module, for example `aec_drawing_metadata`.
- `<LocalName>` is the local name of the class or relationship the image shows, exactly as in its IRI.
- `NN` is a two-digit number, always present, starting at `01`: even a term's only image is `Titleblock_01.png`. The
  number is the display order (a preview takes `_01`), and a new image takes the next free number. Numbers need not be
  contiguous.
- `<ext>` is `png`, `jpg` or `webp`, in lower case.

The image is published at `https://w3id.org/adiro/<module>/exampleImage/<LocalName>_NN.<ext>`. The documentation build
copies the folder into the site, so the image is committed once, in `assets/`.

## Linking it from the ontology

The value of `exampleImage` is the full URI of the image. Declare one prefix for the module's folder, and write the file
part only:

```turtle
@prefix img: <https://w3id.org/adiro/aec_drawing_metadata/exampleImage/> .

:Titleblock a owl:Class ;
    :exampleImage img:Titleblock_01.png , img:Titleblock_02.png .
```

The prefix expands to the full IRI, so `img:Titleblock_01.png` is
`<https://w3id.org/adiro/aec_drawing_metadata/exampleImage/Titleblock_01.png>`. The value is an IRI, not a text literal.

## The statement in the pull request

A pull request that adds or replaces an image has a section **Example images** in its description. For each image, or
group of images, it says where the image comes from and why it may be published (your own work, public domain, licensed
with the licence named, or cleared by its owner), and what was obscured or removed. A sentence is enough. The reviewer
judges it; the checks cannot.

## When a term is renamed or removed

- **Renamed.** Rename its images to follow the new name, and list the old names in
  `assets/<module>/exampleImage/renames.json` (`{"Old_01.png": "New_01.png"}`). The documentation build serves each old
  name as a copy of the new file, so a released version that names the old file still shows its image.
- **Removed.** Move its images to `assets/<module>/exampleImage/deletedAfterV<x.y.z>/`, where `<x.y.z>` is the last
  release that still has the term. That release then still shows them.
- **Taken down.** An image that was published by mistake (a rights problem, private information) is deleted in the pull
  request and its path is added to `assets/<module>/exampleImage/takedowns.txt`, one path per line followed by a reason
  code (`copyright` or `privacy`). A listed path needs no backup and no rename entry, and is never copied to the site.
  The file stays in the git history; removing it from the history is a separate maintainer action.

The `exampleImage` property itself is not renamed. If a pull request removes or renames it, the ADIRO Bot raises a
caution at the top of its comment.

## The checks

`scripts/validate_ontology.py` checks the values and the files, and its findings appear in the QC comment of the pull
request:

- every value is an absolute `https` IRI in the module's `exampleImage` folder, and the file exists;
- the file name is the local name of the term that carries the value, then `_NN`, then a lower-case extension;
- no file is left in a folder that no term uses (other than the `deletedAfter…` backups and takedowns), and no two
  files differ only by case;
- the size, the dimensions and the embedded metadata of each file, and the total size of all example images.

Findings about values and names are advisory while the older images are migrated; the limits on files that follow the
convention (500 KB, embedded metadata, the 250 MB total) block. To run the checks locally:

```bash
uv run python scripts/validate_ontology.py
```

The ADIRO Bot also suggests an example image for every class a pull request adds without one. It is a suggestion, not
a requirement.
