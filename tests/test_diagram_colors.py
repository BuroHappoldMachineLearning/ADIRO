"""Colour tests for the ontology dependency diagrams.

These guard the two things that broke before:

1. The diagram palette must be *derived from the favicon* — the brand navy,
   teal and orange are asserted to actually occur in ``docs/img/favicon.png``.
2. The node **label text must be legible** against its box fill (the regression
   where navy boxes rendered near-invisible black text). This is enforced with a
   WCAG contrast-ratio check, parametrised over the diagram's colour roles.

If the favicon is replaced, update the ``BRAND_*`` constants in
``scripts/generate_docs.py`` to match its palette and these tests will confirm
the diagrams stay legible.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import generate_docs as gd  # noqa: E402  (path set up above)

FAVICON = REPO / "docs" / "img" / "favicon.png"

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def _linear(channel: float) -> float:
    c = channel / 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb: tuple[int, int, int]) -> float:
    r, g, b = (_linear(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(a: str, b: str) -> float:
    la, lb = relative_luminance(hex_to_rgb(a)), relative_luminance(hex_to_rgb(b))
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def favicon_pixels() -> list[tuple[int, int, int]]:
    """Return the opaque pixels of the favicon (downsampled for speed)."""
    im = Image.open(FAVICON).convert("RGBA")
    im.thumbnail((160, 160))
    return [(r, g, b) for (r, g, b, a) in im.getdata() if a > 128]


def color_occurs(target_hex: str, pixels, tolerance: int = 48, min_count: int = 20) -> bool:
    """True if ``target_hex`` appears in ``pixels`` within a distance tolerance."""
    tr, tg, tb = hex_to_rgb(target_hex)
    tol_sq = tolerance * tolerance
    count = 0
    for r, g, b in pixels:
        if (r - tr) ** 2 + (g - tg) ** 2 + (b - tb) ** 2 <= tol_sq:
            count += 1
            if count >= min_count:
                return True
    return False


def diagram_for(highlight: str | None) -> str:
    ttls = gd.sort_by_dependency(gd.find_ttl_files(REPO))
    assert ttls, "no TTL ontologies discovered in src/"
    return "\n".join(gd.build_dependency_mermaid(ttls, highlight=highlight))


# --------------------------------------------------------------------------
# 1. Palette is derived from the favicon
# --------------------------------------------------------------------------


@pytest.mark.skipif(Image is None, reason="Pillow not installed")
@pytest.mark.parametrize(
    "name,color",
    [
        ("navy", gd.BRAND_NAVY),
        ("teal", gd.BRAND_TEAL),
        ("orange", gd.BRAND_ORANGE),
    ],
)
def test_brand_color_present_in_favicon(name, color):
    pixels = favicon_pixels()
    assert color_occurs(color, pixels), (
        f"brand {name} {color} not found in favicon {FAVICON.name}; "
        "update the BRAND_* constants to match the favicon palette"
    )


# --------------------------------------------------------------------------
# 2. Node labels are legible against their fills (regression guard)
# --------------------------------------------------------------------------

MIN_CONTRAST = 4.5  # WCAG AA for normal text


@pytest.mark.parametrize(
    "role,text,fill",
    [
        ("base (navy) node", gd.DIAGRAM_BASE_TEXT, gd.DIAGRAM_BASE_FILL),
        ("current (orange) node", gd.DIAGRAM_CURRENT_TEXT, gd.DIAGRAM_CURRENT_FILL),
    ],
)
def test_label_text_contrasts_with_fill(role, text, fill):
    ratio = contrast_ratio(text, fill)
    assert ratio >= MIN_CONTRAST, (
        f"{role}: text {text} on fill {fill} has contrast {ratio:.2f} "
        f"(< {MIN_CONTRAST}); labels would be hard to read"
    )


# --------------------------------------------------------------------------
# 3. The generated diagrams actually use the palette
# --------------------------------------------------------------------------


def test_subpage_diagram_uses_base_and_current_colors():
    ttls = gd.sort_by_dependency(gd.find_ttl_files(REPO))
    stem = ttls[-1].stem  # a leaf ontology, guaranteed to be the highlighted one
    md = diagram_for(highlight=stem)
    # Box fills via classDef
    assert gd.DIAGRAM_BASE_FILL in md
    assert gd.DIAGRAM_CURRENT_FILL in md
    # Label colours via themeCSS (the mechanism that actually wins in Material)
    assert "themeCSS" in md
    assert gd.DIAGRAM_BASE_TEXT in md
    assert gd.DIAGRAM_CURRENT_TEXT in md


def test_index_diagram_is_all_blue_no_orange():
    md = diagram_for(highlight=None)
    assert gd.DIAGRAM_BASE_FILL in md
    assert gd.DIAGRAM_CURRENT_FILL not in md  # no highlighted node on the index
