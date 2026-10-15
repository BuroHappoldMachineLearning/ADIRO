#!/usr/bin/env python3
"""
Generate the synthetic example images of aec_drawing_metadata (#149).

Every image is drawn by this script with fictional content ("Example Studio", "Sample Project"), so ADIRO owns it:
no third-party drawing, logo, seal or name is involved. The images follow the example-image convention (#145):
`assets/<module>/exampleImage/<LocalName>_NN.png`, small, cropped to the part they illustrate, with no embedded metadata.

    uv run --with matplotlib --with pillow python scripts/synthetic_example_images.py [OUTPUT_DIR]

The default output is assets/aec_drawing_metadata/exampleImage/. The drawings are deterministic.
"""
import io
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Arc, Circle, Polygon, Rectangle  # noqa: E402
from PIL import Image, ImageChops  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "assets" / "aec_drawing_metadata" / "exampleImage"
INK = "#111111"


def canvas(width, height):
    """A white drawing area of `width` x `height` drawing units, one unit per pixel, y pointing up."""
    fig = plt.figure(figsize=(width / 100, height / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    ax.axis("off")
    return fig, ax


def line(ax, xs, ys, lw=1.4, ls="-"):
    ax.plot(xs, ys, color=INK, lw=lw, ls=ls, solid_capstyle="butt")


def box(ax, x, y, w, h, lw=1.4, fill=None, hatch=None):
    ax.add_patch(Rectangle((x, y), w, h, fill=fill is not None, facecolor=fill or "none", edgecolor=INK, lw=lw, hatch=hatch))


def text(ax, x, y, s, size=11, weight="normal", ha="left", va="center", rotation=0, family="DejaVu Sans"):
    ax.text(x, y, s, fontsize=size, fontweight=weight, ha=ha, va=va, color=INK, rotation=rotation, family=family)


def finish(fig):
    """Render, crop to the content with a margin, reduce to a small palette and drop every metadata field."""
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=100, facecolor="white", metadata={"Software": None})
    plt.close(fig)
    image = Image.open(io.BytesIO(buffer.getvalue())).convert("RGB")
    bbox = ImageChops.difference(image, Image.new("RGB", image.size, "white")).getbbox()
    margin = 14
    box_ = (max(bbox[0] - margin, 0), max(bbox[1] - margin, 0), min(bbox[2] + margin, image.width), min(bbox[3] + margin, image.height))
    image = image.crop(box_).quantize(colors=16, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    out = io.BytesIO()
    image.save(out, format="PNG", optimize=True)  # no pnginfo: nothing but pixels is written
    return out.getvalue()


# --- the drawings -----------------------------------------------------------------------------------------------

def titleblock_side():
    fig, ax = canvas(430, 940)
    box(ax, 10, 10, 410, 920, lw=2.2)
    y = 930
    cells = [("", 110, None), ("PROJECT", 120, ["Sample Project", "Block A, Example Street"]), ("CLIENT", 80, ["Sample Client Ltd"]),
             ("REVISIONS", 190, None), ("SEAL", 130, None), ("SHEET TITLE", 90, ["GROUND FLOOR PLAN"])]
    for label, height, lines in cells:
        line(ax, [10, 420], [y, y], lw=1.4)
        if label == "":
            text(ax, 215, y - 40, "EXAMPLE", 20, "bold", "center")
            text(ax, 215, y - 70, "STUDIO", 13, "normal", "center")
        else:
            text(ax, 22, y - 16, label, 8.5)
        for i, content in enumerate(lines or []):
            text(ax, 22, y - 46 - 26 * i, content, 13.5 if label != "SHEET TITLE" else 15, "bold" if label == "SHEET TITLE" else "normal")
        if label == "REVISIONS":
            for i, row in enumerate([("REV", "DATE", "DESCRIPTION"), ("A", "15.01.26", "First issue"), ("B", "12.02.26", "Updated layout")]):
                yy = y - 48 - 34 * i
                line(ax, [10, 420], [yy - 17, yy - 17], lw=0.8)
                for x, value in zip((22, 80, 175), row):
                    text(ax, x, yy, value, 9.5, "bold" if i == 0 else "normal")
            line(ax, [66, 66], [y - 31, y - 150], lw=0.8)
            line(ax, [160, 160], [y - 31, y - 150], lw=0.8)
        if label == "SEAL":
            ax.add_patch(Circle((215, y - 75), 42, fill=False, edgecolor=INK, lw=1.0, ls="--"))
            text(ax, 215, y - 75, "SEAL", 10, ha="center")
        y -= height
    line(ax, [10, 420], [y, y], lw=1.4)
    rows = [("SCALE", "1:100"), ("DATE", "15.01.2026"), ("DRAWN", "AB"), ("CHECKED", "CD"), ("JOB NO.", "25-001")]
    for label, value in rows:
        text(ax, 22, y - 17, label, 8.5)
        text(ax, 130, y - 17, value, 12, "bold")
        y -= 34
        line(ax, [10, 420], [y, y], lw=0.8)
    line(ax, [10, 420], [y, y], lw=1.4)
    text(ax, 22, y - 17, "DRAWING NUMBER", 8.5)
    text(ax, 215, y - 58, "EX-A-101", 26, "bold", "center")
    text(ax, 360, y - 17, "REV", 8.5)
    text(ax, 385, y - 58, "B", 22, "bold", "center")
    return finish(fig)


def titleblock_strip():
    fig, ax = canvas(1500, 230)
    box(ax, 10, 10, 1480, 210, lw=2.2)
    xs = [10, 330, 880, 1060, 1180, 1490]
    for x in xs[1:-1]:
        line(ax, [x, x], [10, 220])
    text(ax, 22, 197, "EXAMPLE STUDIO", 17, "bold")
    text(ax, 22, 160, "architecture", 11)
    text(ax, 22, 40, "1 Example Street, Sampletown", 9)
    text(ax, 340, 197, "PROJECT", 8.5)
    text(ax, 340, 160, "Sample Project", 20, "bold")
    text(ax, 340, 128, "Block A", 13)
    line(ax, [330, 880], [100, 100], lw=0.8)
    text(ax, 340, 80, "DRAWING TITLE", 8.5)
    text(ax, 340, 45, "SECOND FLOOR PLAN", 20, "bold")
    for x, label, value in [(890, "SCALE", "1:100"), (1070, "DATE", "15.01.26"), (1190, "DRAWING NUMBER", "")]:
        text(ax, x, 197, label, 8.5)
    text(ax, 890, 160, "1:100", 16, "bold")
    text(ax, 1070, 160, "15.01.26", 16, "bold")
    line(ax, [880, 1180], [110, 110], lw=0.8)
    for x, label, value in [(890, "DRAWN", "AB"), (1070, "CHECKED", "CD")]:
        text(ax, x, 90, label, 8.5)
        text(ax, x, 50, value, 16, "bold")
    text(ax, 1335, 150, "EX-A-102", 30, "bold", "center")
    line(ax, [1180, 1490], [110, 110], lw=0.8)
    text(ax, 1190, 90, "REVISION", 8.5)
    text(ax, 1190, 50, "B", 18, "bold")
    return finish(fig)


def revision_table():
    fig, ax = canvas(980, 290)
    columns = [(10, 80, "REV"), (90, 190, "DATE"), (280, 560, "DESCRIPTION"), (840, 70, "BY"), (910, 70, "CHK")]
    box(ax, 10, 38, 970, 282, lw=2.0)
    rows = [("D", "28.03.2026", "Door positions coordinated with the structural engineer", "AB", "CD"),
            ("C", "02.03.2026", "Stair core widened; fire strategy comments incorporated", "AB", "CD"),
            ("B", "12.02.2026", "Ground floor layout updated after client review", "AB", "EF"),
            ("A", "15.01.2026", "First issue for coordination", "AB", "EF")]
    for x, w, label in columns:
        text(ax, x + w / 2 if label in ("REV", "BY", "CHK") else x + 12, 292, label, 11, "bold", "center" if label in ("REV", "BY", "CHK") else "left")
    for x in (90, 280, 840, 910):
        line(ax, [x, x], [38, 320], lw=1.0)
    line(ax, [10, 980], [270, 270], lw=1.6)
    for i, row in enumerate(rows):
        y = 240 - 58 * i
        for (x, w, label), value in zip(columns, row):
            text(ax, x + w / 2 if label in ("REV", "BY", "CHK") else x + 12, y, value, 12.5, "bold" if label == "REV" else "normal",
                 "center" if label in ("REV", "BY", "CHK") else "left")
        line(ax, [10, 980], [y - 29, y - 29], lw=0.8)
    return finish(fig)


def legend():
    fig, ax = canvas(760, 520)
    box(ax, 10, 10, 740, 500, lw=2.0)
    text(ax, 30, 480, "LEGEND", 17, "bold")
    line(ax, [10, 750], [455, 455], lw=1.4)
    rows = ["Existing wall to remain", "New wall", "Door with swing", "Window", "Section marker", "Grid line", "Level marker"]
    for i, label in enumerate(rows):
        y = 415 - 56 * i
        text(ax, 190, y, label, 13)
        if i == 0:
            box(ax, 30, y - 12, 130, 24, fill="#cccccc", lw=1.2)
        elif i == 1:
            box(ax, 30, y - 12, 130, 24, hatch="////", lw=1.2)
        elif i == 2:
            line(ax, [30, 30], [y - 22, y + 4], lw=2.2)
            ax.add_patch(Arc((30, y - 22), 52, 52, theta1=0, theta2=90, edgecolor=INK, lw=1.2))
            line(ax, [30, 82], [y - 22, y - 22], lw=1.2)
        elif i == 3:
            for dy in (-6, 0, 6):
                line(ax, [30, 160], [y + dy, y + dy], lw=1.2)
        elif i == 4:
            ax.add_patch(Circle((60, y), 17, fill=False, edgecolor=INK, lw=1.4))
            text(ax, 60, y, "A", 12, "bold", "center")
            ax.add_patch(Polygon([[84, y], [112, y + 8], [112, y - 8]], closed=True, facecolor=INK))
        elif i == 5:
            line(ax, [30, 160], [y, y], lw=1.2, ls="-.")
        else:
            ax.add_patch(Polygon([[60, y - 13], [44, y + 11], [76, y + 11]], closed=True, fill=False, edgecolor=INK, lw=1.4))
            line(ax, [30, 100], [y - 13, y - 13], lw=1.2)
    return finish(fig)


def plan():
    fig, ax = canvas(1280, 920)
    w0, h0 = 90, 150
    outer_w, outer_h = 1000, 640
    box(ax, w0, h0, outer_w, outer_h, lw=6)
    inner = [((w0 + 380, h0), (w0 + 380, h0 + 400)), ((w0, h0 + 400), (w0 + 640, h0 + 400)), ((w0 + 640, h0 + 220), (w0 + 640, h0 + outer_h)),
             ((w0 + 640, h0 + 220), (w0 + outer_w, h0 + 220)), ((w0 + 220, h0 + 400), (w0 + 220, h0 + outer_h))]
    for (x1, y1), (x2, y2) in inner:
        line(ax, [x1, x2], [y1, y2], lw=4)
    for x, y, rot, flip in [(w0 + 380, h0 + 90, 90, 0), (w0 + 150, h0 + 400, 0, 0), (w0 + 640, h0 + 480, 90, 0), (w0 + 760, h0 + 220, 0, 0)]:
        if rot == 90:
            ax.add_patch(Rectangle((x - 3, y), 6, 80, facecolor="white", edgecolor="none", zorder=3))
            ax.add_patch(Arc((x, y), 160, 160, theta1=0, theta2=90, edgecolor=INK, lw=1.2, zorder=4))
            line(ax, [x, x + 80], [y, y], lw=1.2)
        else:
            ax.add_patch(Rectangle((x, y - 3), 80, 6, facecolor="white", edgecolor="none", zorder=3))
            ax.add_patch(Arc((x, y), 160, 160, theta1=0, theta2=90, edgecolor=INK, lw=1.2, zorder=4))
            line(ax, [x, x], [y, y + 80], lw=1.2)
    for x in (w0 + 110, w0 + 440, w0 + 780):  # windows in the south wall
        ax.add_patch(Rectangle((x, h0 - 4), 140, 8, facecolor="white", edgecolor=INK, lw=1.4, zorder=3))
    for label, x, y in [("LIVING", w0 + 190, h0 + 200), ("KITCHEN", w0 + 510, h0 + 200), ("BEDROOM", w0 + 320, h0 + 520), ("BATH", w0 + 110, h0 + 520),
                        ("HALL", w0 + 820, h0 + 120), ("OFFICE", w0 + 820, h0 + 440)]:
        text(ax, x, y, label, 13, "bold", "center")
    for i, label in enumerate("1234"):
        x = w0 + [0, 380, 640, outer_w][i]
        ax.add_patch(Circle((x, h0 + outer_h + 70), 22, fill=False, edgecolor=INK, lw=1.4))
        text(ax, x, h0 + outer_h + 70, label, 13, "bold", "center")
        line(ax, [x, x], [h0 + outer_h + 92, h0 + outer_h + 28], lw=0.9, ls="-.")
    line(ax, [w0, w0 + outer_w], [h0 - 50, h0 - 50], lw=1.2)
    for x in (w0, w0 + 380, w0 + 640, w0 + outer_w):
        line(ax, [x - 8, x + 8], [h0 - 58, h0 - 42], lw=1.6)
    for x, label in [(w0 + 190, "3800"), (w0 + 510, "2600"), (w0 + 820, "3600")]:
        text(ax, x, h0 - 74, label, 11, ha="center")
    ax.add_patch(Circle((1190, 740), 30, fill=False, edgecolor=INK, lw=1.4))
    ax.add_patch(Polygon([[1190, 775], [1178, 725], [1190, 735], [1202, 725]], closed=True, facecolor=INK))
    text(ax, 1190, 800, "N", 13, "bold", "center")
    text(ax, w0, 40, "GROUND FLOOR PLAN", 17, "bold")
    text(ax, w0 + 300, 40, "1:100", 12)
    return finish(fig)


def section():
    fig, ax = canvas(900, 900)
    levels = [(150, "+0.00 GROUND"), (390, "+3.50 FIRST"), (630, "+7.00 SECOND"), (800, "+9.50 ROOF")]
    ax.add_patch(Rectangle((60, 60), 740, 90, facecolor="none", edgecolor=INK, hatch="///", lw=0))
    line(ax, [40, 840], [150, 150], lw=2.4)
    for y in (150, 390, 630):  # slabs
        box(ax, 150, y, 520, 22, fill="#bbbbbb", lw=1.6)
    box(ax, 150, 800 - 12, 520, 22, fill="#bbbbbb", lw=1.6)
    for x in (150, 648):  # walls
        box(ax, x, 172, 22, 640, lw=1.6, hatch="xxx")
    box(ax, 400, 172, 14, 218, lw=1.4, hatch="///")  # stair core wall
    for y0, y1 in [(172, 390), (394, 630), (652, 800)]:  # glazing
        if y1 - y0 > 100:
            line(ax, [640, 640], [y0 + 40, y1 - 40], lw=1.2)
    for y, label in levels:
        line(ax, [700, 800], [y, y], lw=1.2, ls="-.")
        ax.add_patch(Polygon([[748, y - 3], [736, y + 15], [760, y + 15]], closed=True, fill=False, edgecolor=INK, lw=1.2))
        text(ax, 770, y + 28, label, 10.5)
    line(ax, [100, 100], [150, 800], lw=1.2)
    for y in (150, 390, 630, 800):
        line(ax, [92, 108], [y - 8, y + 8], lw=1.6)
    for y, label in [(270, "3500"), (510, "3500"), (715, "2500")]:
        text(ax, 86, y, label, 10.5, ha="right", rotation=90, va="center")
    ax.add_patch(Circle((60, 860), 22, fill=False, edgecolor=INK, lw=1.4))
    text(ax, 60, 860, "A", 13, "bold", "center")
    text(ax, 100, 860, "SECTION A-A", 16, "bold")
    text(ax, 290, 860, "1:100", 12)
    return finish(fig)


def elevation():
    fig, ax = canvas(1220, 760)
    base, height, width = 120, 520, 900
    line(ax, [40, 1060], [base, base], lw=2.6)
    box(ax, 100, base, width, height, lw=2.0)
    for y in (base + 170, base + 340):
        line(ax, [100, 100 + width], [y, y], lw=1.0)
    for row in range(3):
        for col in range(6):
            x = 140 + col * 140
            y = base + 40 + row * 170
            if row == 0 and col == 2:  # entrance
                box(ax, x, base, 100, 150, lw=1.6, fill="#dddddd")
                continue
            box(ax, x, y, 100, 110, lw=1.4)
            line(ax, [x + 50, x + 50], [y, y + 110], lw=0.9)
            line(ax, [x, x + 100], [y + 55, y + 55], lw=0.9)
    line(ax, [100, 100 + width], [base + height + 12, base + height + 12], lw=2.0)
    for y, label in [(base, "+0.00"), (base + 170, "+3.50"), (base + 340, "+7.00"), (base + height, "+10.50")]:
        line(ax, [1010, 1060], [y, y], lw=1.0, ls="--")
        text(ax, 1068, y, label, 10.5)
    text(ax, 100, 60, "SOUTH ELEVATION", 17, "bold")
    text(ax, 360, 60, "1:100", 12)
    return finish(fig)


def detail():
    fig, ax = canvas(1100, 760)
    box(ax, 330, 120, 70, 520, lw=1.6, hatch="..")  # concrete wall
    box(ax, 400, 120, 110, 520, lw=1.4, hatch="\\\\\\\\")  # insulation
    box(ax, 510, 120, 20, 520, lw=1.4)  # air gap line
    box(ax, 530, 120, 70, 520, lw=1.6, hatch="++")  # brick
    box(ax, 150, 600, 250, 40, lw=1.6, hatch="..")  # slab
    box(ax, 150, 640, 250, 14, lw=1.2)
    for tx, y, label in [(565, 560, "Facing brick 102 mm"), (520, 470, "Ventilated cavity 25 mm"), (455, 380, "Mineral wool insulation 100 mm"),
                         (365, 290, "Reinforced concrete wall 200 mm")]:
        line(ax, [tx, 690], [y, y], lw=0.9)
        text(ax, 700, y, label, 12.5)
    line(ax, [200, 200], [620, 690], lw=0.9)
    text(ax, 150, 705, "Screed and floor finish", 12.5)
    text(ax, 330, 60, "TYPICAL WALL DETAIL", 17, "bold")
    text(ax, 720, 60, "1:5", 12)
    return finish(fig)


def table():
    fig, ax = canvas(1160, 460)
    headers = ["MARK", "TYPE", "WIDTH", "HEIGHT", "MATERIAL", "FIRE", "REMARKS"]
    widths = [90, 90, 100, 100, 190, 90, 400]
    rows = [("D01", "A", "900", "2100", "Timber", "FD30", "Main entrance, double leaf"), ("D02", "B", "800", "2100", "Timber", "-", "Bedroom"),
            ("D03", "B", "800", "2100", "Timber", "-", "Bedroom"), ("D04", "C", "700", "2100", "Timber", "-", "Bathroom, outward opening"),
            ("D05", "D", "1000", "2100", "Steel", "FD60", "Plant room"), ("D06", "A", "900", "2100", "Glass", "FD30", "Lobby")]
    x0, y0 = 10, 430
    box(ax, x0, 28, sum(widths), 402, lw=2.0)
    x = x0
    for header, w in zip(headers, widths):
        text(ax, x + 10, y0 - 25, header, 11.5, "bold")
        x += w
        if x < x0 + sum(widths):
            line(ax, [x, x], [28, 430], lw=1.0)
    line(ax, [x0, x0 + sum(widths)], [y0 - 50, y0 - 50], lw=1.8)
    for i, row in enumerate(rows):
        y = y0 - 80 - 58 * i
        x = x0
        for value, w in zip(row, widths):
            text(ax, x + 10, y, value, 12.5)
            x += w
        line(ax, [x0, x0 + sum(widths)], [y - 29, y - 29], lw=0.8)
    return finish(fig)


def textual_note():
    fig, ax = canvas(900, 560)
    box(ax, 10, 10, 880, 540, lw=2.0)
    text(ax, 30, 520, "GENERAL NOTES", 17, "bold")
    line(ax, [10, 890], [495, 495], lw=1.4)
    notes = ["All dimensions are in millimetres unless noted otherwise.",
             "Do not scale from this drawing; check dimensions on site.",
             "Levels are in metres above the project datum.",
             "Refer to the structural drawings for all structural members.",
             "Fire-rated walls and doors are shown on the fire strategy sheet.",
             "Report any discrepancy to the architect before proceeding."]
    for i, note in enumerate(notes):
        y = 455 - 66 * i
        text(ax, 30, y, f"{i + 1}.", 13, "bold")
        text(ax, 70, y, note, 13)
    return finish(fig)


DRAWINGS = {
    "Titleblock_01.png": titleblock_side,
    "Titleblock_02.png": titleblock_strip,
    "RevisionTable_01.png": revision_table,
    "Legend_01.png": legend,
    "Plan_01.png": plan,
    "Section_01.png": section,
    "Elevation_01.png": elevation,
    "Detail_01.png": detail,
    "Table_01.png": table,
    "TextualNote_01.png": textual_note,
}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    out = Path(argv[0]) if argv else DEFAULT_OUT
    out.mkdir(parents=True, exist_ok=True)
    for name, draw in DRAWINGS.items():
        data = draw()
        (out / name).write_bytes(data)
        print(f"wrote {name} ({len(data) // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
