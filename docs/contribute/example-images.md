# Example images

An **example image** shows what a class or relationship looks like on a drawing. It is linked to the term with the
`exampleImage` annotation property, and it is part of the ontology: the documentation pages show it, and downstream
tools (annotation tools, machine-learning workflows) read it by its URI. This page is how to add one.

## The standard property it belongs to

`exampleImage` is a sub-property of the standard `foaf:depiction`, so a tool that reads `foaf:depiction` finds ADIRO's
images without knowing ADIRO. `exampleImage` keeps its own meaning (an example of how the term looks on a drawing), its
numbering and its checks. The ontology declares `foaf:depiction` as an annotation property, as the OBO ontologies do,
and never imports FOAF. That matters: FOAF itself defines `depiction` as an object property, and OWL 2 DL does not allow
one IRI to be both an annotation property and an object property. If FOAF's own definition is loaded together with
ADIRO, the merged ontology is no longer OWL 2 DL (Protégé reports illegal punning, and a strict reasoner refuses it). So
do not import FOAF into an ADIRO module, and a consumer that merges both should drop FOAF's declaration of `depiction`.
`scripts/validate_ontology.py` fails a module that imports FOAF or declares `foaf:depiction` as anything but an
annotation property, and the reasoning check validates the OWL 2 DL profile of the merged modules.

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

- `<module>` is the ontology module, for example `adiro_drawing_metadata`.
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
@prefix img: <https://w3id.org/adiro/adiro_drawing_metadata/exampleImage/> .

:Titleblock a owl:Class ;
    :exampleImage img:Titleblock_01.png , img:Titleblock_02.png .
```

The prefix expands to the full IRI, so `img:Titleblock_01.png` is
`<https://w3id.org/adiro/adiro_drawing_metadata/exampleImage/Titleblock_01.png>`. The value is an IRI, not a text literal.

## The statement in the pull request

A pull request that adds or replaces an image has a section **Example images** in its description. For each image, or
group of images, it says where the image comes from and why it may be published (your own work, public domain, licensed
with the licence named, or cleared by its owner), and what was obscured or removed. A sentence is enough. The reviewer
judges it; the checks cannot.

## When a term is renamed or removed

- **Renamed.** Rename its images to follow the new name, and list the old names in
  `assets/<module>/exampleImage/renames.json` (`{"Old_01.png": "New_01.png"}`). The documentation build serves each old
  name as a copy of the new file, so a released version that names the old file still shows its image.
- **Removed.** Leave its images where they are. A released version never changes, so the address it names must keep
  working for good; the checks accept a file that an archived release still names. An image that no release names is
  reported as unused and can be deleted.
- **Taken down.** An image that was published by mistake (a rights problem, private information) is deleted in the pull
  request and its path is added to `assets/<module>/exampleImage/takedowns.txt`, one line per path: the path, a reason
  code (`copyright` or `privacy`) and `after=<x.y.z>`, the last release that showed it. The path is relative to the
  folder (or a site path starting with `/`, for the images published before the convention). The site then serves a
  placeholder at that address, "Image removed after v<x.y.z>", so an older release shows a notice, not a broken image. The
  placeholder for each version is `assets/<module>/exampleImage/removed/after-v<x.y.z>.png`, drawn by
  `scripts/synthetic_example_images.py`. The file stays in the git history; removing it from the history is a separate
  maintainer action.
- **A name stays reserved.** A name that an archived release gives to a term, or that `takedowns.txt` lists, is not used
  for another image: a different image takes the next number (`Stamp_02.png`). Reusing the name would change what the
  older release shows.

The `exampleImage` property itself is not renamed. If a pull request removes or renames it, the ADIRO Bot raises a
caution at the top of its comment.

## The checks

`scripts/validate_ontology.py` checks the values and the files, and its findings appear in the QC comment of the pull
request:

- every value is an absolute `https` IRI in the module's `exampleImage` folder, and the file exists;
- the file name is the local name of the term that carries the value, then `_NN`, then a lower-case extension;
- no file is left in a folder that neither a term nor an archived release uses, and no two files differ only by case;
- every address that an archived release names (`versions/`) is still served: by a file, a rename or a takedown's
  placeholder (advisory for the first release cycle after [#154](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/154),
  then blocking: `ENFORCE_ARCHIVED_IMAGES=1`). A taken-down name is not kept as a file, and a name an archived release gives to
  another term is not reused;
- the size, the dimensions and the embedded metadata of each file, and the total size of all example images.

After each deploy, `scripts/check_prior_versions.py` fetches every example image that an archived release names and
requires an image answer, and the placeholder at a taken-down address.

Findings about values and names are advisory while the older images are migrated; the limits on files that follow the
convention (500 KB, embedded metadata, the 250 MB total) block. To run the checks locally:

```bash
uv run python scripts/validate_ontology.py
```

The ADIRO Bot also suggests an example image for every class a pull request adds without one. It is a suggestion, not
a requirement.
