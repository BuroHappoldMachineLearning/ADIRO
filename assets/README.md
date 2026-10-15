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
- An archived release never changes, so the images it names stay where they are, also when their term is removed.
  `renames.json` serves a renamed image under its old name too. `takedowns.txt` records a removal for rights reasons
  (`<path> <reason> after=<last release that showed it>`), and `removed/after-v<x.y.z>.png` is the placeholder the site
  serves at that address ([#154](https://github.com/BuroHappoldMachineLearning/ADIRO/issues/154)).

The images of every module are synthetic: drawn with fictional content by `scripts/synthetic_example_images.py`
(`uv run --with matplotlib --with pillow python scripts/synthetic_example_images.py`), so ADIRO owns them and they can be
reproduced and improved. Change the script, not the PNG, and commit both.

How to add an image, and the checks it goes through (rights, privacy, size, naming):
<https://w3id.org/adiro/contribute/example-images/>
