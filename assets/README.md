# Assets of the ontologies

Files that belong to an ontology and that the ontology points at. They are not code, not text, and not documentation.

```
assets/<module>/exampleImage/<LocalName>_NN.<ext>
```

- **`exampleImage/`** holds the images that the `exampleImage` annotation property links to. The folder is named like the
  property. Each image is named after the class or relationship it shows, then a two-digit number (`Titleblock_01.png`).
- The images are published at `https://w3id.org/adiro/<module>/exampleImage/<LocalName>_NN.<ext>`, and that URI is what
  the ontology holds and what downstream tools (annotation tools, machine-learning workflows) read. The documentation
  site builds a copy of this folder into `docs/<module>/exampleImage/` (git-ignored), so each image is committed once.
- `renames.json`, `takedowns.txt` and the `deletedAfterV<x.y.z>/` folders in each `exampleImage/` folder keep the images
  of renamed and removed terms available, and record a removal for rights reasons.

The images of `aec_drawing_metadata` are synthetic: drawn with fictional content by `scripts/synthetic_example_images.py`
(`uv run --with matplotlib --with pillow python scripts/synthetic_example_images.py`), so ADIRO owns them and they can be
reproduced and improved. Change the script, not the PNG, and commit both.

How to add an image, and the checks it goes through (rights, privacy, size, naming):
<https://w3id.org/adiro/contribute/example-images/>
