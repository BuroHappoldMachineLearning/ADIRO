#!/usr/bin/env python3
"""
Generate the synthetic example images of the ADIRO modules (#149, #151).

Every image is drawn by this script with fictional content ("Example Studio", "Sample Project"), so ADIRO owns it:
no third-party drawing, logo, seal or name is involved. The images follow the example-image convention (#145):
`assets/<module>/exampleImage/<LocalName>_NN.png`, small, cropped to the part they illustrate, with no embedded metadata.

    uv run --with matplotlib --with pillow python scripts/synthetic_example_images.py [ASSETS_DIR]

Each module's images go to <ASSETS_DIR>/<module>/exampleImage/ (default: assets/). The drawings are deterministic.
"""
import io
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Arc, Circle, Polygon, Rectangle  # noqa: E402
from PIL import Image, ImageChops  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import example_images  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ASSETS = ROOT / "assets"
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
    """Render, crop to the content with a margin, reduce to a small palette (32 colours) and drop every metadata field."""
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=100, facecolor="white", metadata={"Software": None})
    plt.close(fig)
    image = Image.open(io.BytesIO(buffer.getvalue())).convert("RGB")
    bbox = ImageChops.difference(image, Image.new("RGB", image.size, "white")).getbbox()
    margin = 14
    box_ = (max(bbox[0] - margin, 0), max(bbox[1] - margin, 0), min(bbox[2] + margin, image.width), min(bbox[3] + margin, image.height))
    image = image.crop(box_).quantize(colors=32, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
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


RED = "#d62728"


def poly(ax, points, fill=None, lw=1.4, hatch=None):
    ax.add_patch(Polygon(points, closed=True, fill=fill is not None, facecolor=fill or "none", edgecolor=INK, lw=lw, hatch=hatch))


def dim_h(ax, x1, x2, y, label, size=12):
    """A horizontal dimension line with oblique ticks and its value above."""
    line(ax, [x1, x2], [y, y], lw=1.0)
    for x in (x1, x2):
        line(ax, [x - 6, x + 6], [y - 6, y + 6], lw=1.6)
    text(ax, (x1 + x2) / 2, y + 16, label, size, ha="center")


def dim_v(ax, x, y1, y2, label, size=12):
    line(ax, [x, x], [y1, y2], lw=1.0)
    for y in (y1, y2):
        line(ax, [x - 6, x + 6], [y - 6, y + 6], lw=1.6)
    text(ax, x - 14, (y1 + y2) / 2, label, size, ha="center", rotation=90)


def bubble(ax, x, y, label, r=26, size=13):
    ax.add_patch(Circle((x, y), r, fill=False, edgecolor=INK, lw=1.4))
    text(ax, x, y, label, size, "bold", "center")


# --- aec_drawing_metadata: the sheet-level concepts added in #151 ---------------------------------------------------

def key_plan():
    fig, ax = canvas(560, 430)
    box(ax, 10, 10, 540, 410, lw=2.0)
    text(ax, 30, 392, "KEY PLAN", 15, "bold")
    line(ax, [10, 550], [368, 368], lw=1.2)
    poly(ax, [(90, 80), (470, 80), (470, 210), (350, 210), (350, 320), (90, 320)], lw=3.0)
    poly(ax, [(90, 80), (350, 80), (350, 320), (90, 320)], hatch="////", lw=0)
    poly(ax, [(90, 80), (470, 80), (470, 210), (350, 210), (350, 320), (90, 320)], lw=3.0)
    line(ax, [350, 350], [80, 210], lw=1.4)
    ax.add_patch(Rectangle((170, 186), 100, 28, facecolor="white", edgecolor="none", zorder=3))
    ax.text(220, 200, "THIS SHEET", fontsize=12, fontweight="bold", ha="center", va="center", color=INK, zorder=4)
    text(ax, 410, 140, "WING B", 11, "normal", "center")
    for x, label in [(90, "A"), (350, "B"), (470, "C")]:
        bubble(ax, x, 345, label, 14, 10)
        line(ax, [x, x], [331, 322], lw=0.9, ls="-.")
    ax.add_patch(Circle((505, 100), 22, fill=False, edgecolor=INK, lw=1.4))
    poly(ax, [(505, 130), (495, 90), (505, 98), (515, 90)], fill=INK)
    text(ax, 505, 150, "N", 12, "bold", "center")
    return finish(fig)


def perspective():
    fig, ax = canvas(1000, 800)
    ox, oy, W, D, H = 300, 420, 380, 260, 300

    def P(x, y, z):
        return (ox + (x - y) * 0.866, oy - (x + y) * 0.5 + z)

    def quad(a, b, c, d, fill):
        poly(ax, [P(*a), P(*b), P(*c), P(*d)], fill=fill, lw=1.6)

    quad((0, D, 0), (W, D, 0), (W, D, H), (0, D, H), "#e6e6e6")  # left face
    quad((W, 0, 0), (W, D, 0), (W, D, H), (W, 0, H), "#bdbdbd")  # right face
    quad((0, 0, H), (W, 0, H), (W, D, H), (0, D, H), "#f5f5f5")  # roof
    for row in range(3):
        for col in range(4):
            x0, z0 = 30 + col * 85, 110 + row * 62
            if row == 0 and col == 1:  # entrance
                quad((x0, D, 0), (x0 + 60, D, 0), (x0 + 60, D, 90), (x0, D, 90), "#8a8a8a")
                continue
            quad((x0, D, z0), (x0 + 60, D, z0), (x0 + 60, D, z0 + 42), (x0, D, z0 + 42), "#cfe3f0")
    for row in range(3):
        for col in range(3):
            y0, z0 = 25 + col * 80, 30 + row * 95
            quad((W, y0, z0 + 25), (W, y0 + 55, z0 + 25), (W, y0 + 55, z0 + 80), (W, y0, z0 + 80), "#cfe3f0")
    text(ax, 80, 60, "PERSPECTIVE VIEW", 17, "bold")
    text(ax, 80, 30, "Sample Project, Block A", 12)
    return finish(fig)


def layout():
    fig, ax = canvas(1100, 790)
    box(ax, 10, 10, 1080, 770, lw=2.4)
    box(ax, 30, 30, 1040, 730, lw=1.2)
    line(ax, [880, 880], [30, 760], lw=1.4)  # title block column
    text(ax, 975, 722, "EXAMPLE STUDIO", 13, "bold", "center")
    for y, label, value in [(640, "PROJECT", "Sample Project"), (560, "SHEET TITLE", "THREE LAYOUTS"), (140, "DRAWING NUMBER", "EX-A-101")]:
        line(ax, [880, 1070], [y + 38, y + 38], lw=0.9)
        text(ax, 890, y + 22, label, 8)
        text(ax, 890, y - 8, value, 11, "bold")
    regions = [("LAYOUT 1", "plan", 50, 400, 400, 340), ("LAYOUT 2", "section", 470, 400, 390, 340), ("LAYOUT 3", "detail", 50, 50, 810, 330)]
    for name, kind, x, y, w, h in regions:
        line(ax, [x, x + w, x + w, x, x], [y, y, y + h, y + h, y], lw=1.6, ls="--")
        box(ax, x, y + h - 32, 130, 32, lw=1.2, fill="#dddddd")
        text(ax, x + 65, y + h - 16, name, 11, "bold", "center")
        text(ax, x + 145, y + h - 16, kind, 11)
    box(ax, 90, 460, 320, 190, lw=3.0)  # mini plan
    line(ax, [250, 250], [460, 650], lw=2.0)
    line(ax, [90, 250], [560, 560], lw=2.0)
    for x, label in zip((90, 250, 410), "ABC"):
        bubble(ax, x, 690, label, 13, 9)
    for y in (410, 520, 630):  # mini section: slabs and walls
        box(ax, 520, y, 240, 14, fill="#bbbbbb", lw=1.2)
    for x in (520, 746):
        box(ax, x, 410, 14, 234, lw=1.2, hatch="xxx")
    box(ax, 240, 90, 140, 200, lw=1.6, hatch="..")  # mini detail
    box(ax, 380, 90, 90, 200, lw=1.4, hatch="\\\\\\\\")
    box(ax, 470, 90, 40, 200, lw=1.6, hatch="++")
    for y, label in [(250, "Facing brick"), (190, "Insulation"), (130, "Concrete wall")]:
        line(ax, [490, 560], [y, y], lw=0.9)
        text(ax, 570, y, label, 11)
    return finish(fig)


# --- aec_common_symbols --------------------------------------------------------------------------------------------

def dimension():
    fig, ax = canvas(900, 520)
    box(ax, 100, 150, 700, 200, lw=5)
    for x in (380, 600):
        line(ax, [x, x], [150, 350], lw=3)
    for x in (100, 380, 600, 800):  # extension lines
        line(ax, [x, x], [360, 450], lw=0.9)
    line(ax, [100, 100], [360, 500], lw=0.9)
    line(ax, [800, 800], [360, 500], lw=0.9)
    dim_h(ax, 100, 380, 430, "2800")
    dim_h(ax, 380, 600, 430, "2200")
    dim_h(ax, 600, 800, 430, "2000")
    dim_h(ax, 100, 800, 485, "7000")
    line(ax, [810, 880], [150, 150], lw=0.9)
    line(ax, [810, 880], [350, 350], lw=0.9)
    dim_v(ax, 860, 150, 350, "2000")
    return finish(fig)


def grid():
    fig, ax = canvas(860, 640)
    xs, ys = [160, 400, 640], [150, 400]
    for x, label in zip(xs, "ABC"):
        line(ax, [x, x], [100, 540], lw=1.0, ls="-.")
        bubble(ax, x, 570, label)
        line(ax, [x, x], [544, 544], lw=1.0)
    for y, label in zip(ys, "12"):
        line(ax, [60, 760], [y, y], lw=1.0, ls="-.")
        bubble(ax, 40, y, label)
    for x in xs:
        for y in ys:
            box(ax, x - 12, y - 12, 24, 24, fill="#bbbbbb", lw=1.4)
    dim_h(ax, 160, 400, 90, "6000")
    dim_h(ax, 400, 640, 90, "6000")
    return finish(fig)


def reference_symbol():
    fig, ax = canvas(1100, 380)

    def marker(x, y, top, bottom):
        ax.add_patch(Circle((x, y), 38, fill=False, edgecolor=INK, lw=1.6))
        line(ax, [x - 38, x + 38], [y, y], lw=1.2)
        text(ax, x, y + 18, top, 14, "bold", "center")
        text(ax, x, y - 17, bottom, 10, "normal", "center")

    marker(90, 220, "1", "A-301")  # section marker: cut line and arrow
    poly(ax, [(90, 292), (70, 258), (110, 258)], fill=INK)
    line(ax, [128, 330], [220, 220], lw=3.0, ls="-.")
    ax.add_patch(Circle((520, 220), 85, fill=False, edgecolor=INK, lw=1.6, ls="--"))  # detail marker: ringed area and bubble
    box(ax, 480, 195, 80, 50, lw=1.4, hatch="////")
    marker(740, 300, "3", "A-501")
    line(ax, [592, 702], [275, 296], lw=1.2)
    marker(960, 220, "2", "A-201")  # elevation marker: bubble and arrow
    poly(ax, [(1000, 220), (1052, 190), (1052, 250)], fill=INK)
    for x, label in [(220, "SECTION MARKER"), (630, "DETAIL MARKER"), (990, "ELEVATION MARKER")]:
        text(ax, x, 70, label, 12, "bold", "center")
    return finish(fig)


# --- aec_domain_common: section profiles --------------------------------------------------------------------------

def profile_labels(ax, height_label, width_label, x1, x2, y1, y2):
    dim_v(ax, x1 - 34, y1, y2, height_label)
    dim_h(ax, x1, x2, y1 - 40, width_label)


def i_section():
    fig, ax = canvas(560, 520)
    poly(ax, [(160, 110), (360, 110), (360, 134), (267, 134), (267, 386), (360, 386), (360, 410), (160, 410), (160, 386), (253, 386), (253, 134), (160, 134)],
         fill="#dddddd", lw=2.4)
    profile_labels(ax, "h", "b", 160, 360, 110, 410)
    text(ax, 376, 122, "tf", 13)
    text(ax, 290, 260, "tw", 13)
    return finish(fig)


def chs():
    fig, ax = canvas(560, 520)
    ax.add_patch(Circle((260, 270), 150, facecolor="#dddddd", edgecolor=INK, lw=2.4))
    ax.add_patch(Circle((260, 270), 126, facecolor="white", edgecolor=INK, lw=2.4))
    dim_h(ax, 110, 410, 80, "d")
    line(ax, [412, 440], [296, 330], lw=0.9)
    text(ax, 446, 336, "t", 13)
    return finish(fig)


def rhs():
    fig, ax = canvas(560, 520)
    box(ax, 140, 110, 240, 300, fill="#dddddd", lw=2.4)
    box(ax, 164, 134, 192, 252, fill="white", lw=2.4)
    profile_labels(ax, "h", "b", 140, 380, 110, 410)
    line(ax, [382, 410], [382, 410], lw=0.9)
    text(ax, 416, 416, "t", 13)
    return finish(fig)


def section_channel():
    fig, ax = canvas(560, 520)
    poly(ax, [(180, 110), (340, 110), (340, 132), (196, 132), (196, 388), (340, 388), (340, 410), (180, 410)], fill="#dddddd", lw=2.4)
    profile_labels(ax, "h", "b", 180, 340, 110, 410)
    text(ax, 356, 121, "tf", 13)
    text(ax, 210, 260, "tw", 13)
    return finish(fig)


def top_hat():
    fig, ax = canvas(620, 400)
    poly(ax, [(100, 110), (212, 110), (212, 238), (348, 238), (348, 110), (460, 110), (460, 122), (360, 122), (360, 250), (200, 250), (200, 122), (100, 122)],
         fill="#dddddd", lw=2.4)
    dim_v(ax, 70, 110, 250, "h")
    dim_h(ax, 200, 360, 280, "w")
    dim_h(ax, 100, 460, 70, "b")
    text(ax, 480, 116, "t", 13)
    return finish(fig)


# --- aec_facade_domain: curtain-wall details with one term highlighted -------------------------------------------

def curtain_wall_section(hl, name):
    """A vertical section through a unitised curtain wall at a floor-slab edge; the term `hl` is filled red."""
    fig, ax = canvas(820, 800)
    ax.set_ylim(170, 800)

    def tone(kind, default):
        return RED if kind == hl else default

    box(ax, 40, 400, 280, 90, hatch="..", lw=1.6)  # floor slab
    text(ax, 60, 515, "INTERIOR", 10)
    text(ax, 540, 600, "EXTERIOR", 10)
    box(ax, 320, 400, 136, 40, fill=tone("Firestop", "#bbbbbb"), hatch="xx", lw=1.4)
    for y0, h in [(312, 88), (440, 80)]:
        box(ax, 340, y0, 116, h, fill=tone("MineralWool", None), hatch="\\\\\\\\", lw=1.4)
    poly(ax, [(322, 300), (380, 300), (380, 312), (334, 312), (334, 400), (322, 400)], fill=tone("ShelfAngle", "#888888"), lw=1.4)
    poly(ax, [(296, 490), (296, 544), (410, 544), (410, 530), (310, 530), (310, 490)], fill=tone("Bracket", "#888888"), lw=1.4)
    for y0, h in [(520, 70), (250, 50)]:  # transoms
        box(ax, 410, y0, 100, h, fill=tone("Transom", "#dddddd"), lw=1.6)
        box(ax, 424, y0 + 14, 72, h - 28, fill="white", lw=1.2)
    box(ax, 460, 300, 8, 220, fill="#bbbbbb", lw=1.2)  # spandrel pane
    for x in (440, 472):  # double glazing unit
        box(ax, x, 596, 8, 170, fill=tone("DGU", "#cfe3f0"), lw=1.2)
    box(ax, 448, 596, 24, 8, fill=tone("DGU", "#666666"), lw=1.0)
    for x in (430, 480):
        box(ax, x, 590, 10, 14, fill=tone("Gasket", INK), lw=1.0)
    poly(ax, [(490, 590), (508, 590), (490, 614)], fill=tone("Sealant", "#444444"), lw=1.0)
    line(ax, [430, 445, 455, 465, 475, 490], [766, 774, 760, 774, 760, 768], lw=1.4)  # break line
    text(ax, 40, 222, "CURTAIN WALL SECTION AT SLAB EDGE", 12, "bold")
    box(ax, 40, 182, 16, 16, fill=RED, lw=1.0)
    text(ax, 66, 190, name, 12)
    return finish(fig)


def mullion_plan():
    fig, ax = canvas(820, 520)
    box(ax, 340, 190, 120, 200, fill=RED, lw=1.6)
    box(ax, 356, 206, 88, 168, fill="white", lw=1.2)
    box(ax, 372, 390, 56, 10, fill="#888888", lw=1.2)
    box(ax, 364, 400, 72, 12, fill="#888888", lw=1.2)
    for side in (-1, 1):  # a glazing unit each side of the mullion
        x0 = 340 - 280 if side < 0 else 460
        for y in (330, 362):
            box(ax, x0, y, 280, 8, fill="#cfe3f0", lw=1.2)
        sx = 316 if side < 0 else 460
        box(ax, sx, 338, 24, 24, fill="#666666", lw=1.0)
        gx = 330 if side < 0 else 460
        box(ax, gx, 322, 10, 24, fill=INK, lw=1.0)
        box(ax, gx, 354, 10, 24, fill=INK, lw=1.0)
    text(ax, 60, 470, "EXTERIOR", 10)
    text(ax, 60, 150, "INTERIOR", 10)
    text(ax, 60, 100, "CURTAIN WALL PLAN AT MULLION", 14, "bold")
    box(ax, 60, 52, 16, 16, fill=RED, lw=1.0)
    text(ax, 86, 60, "Mullion", 12)
    return finish(fig)


def removed_placeholder(version):
    """The notice served at the address of a taken-down image: an old release shows it in place of the image (#154)."""
    fig, ax = canvas(640, 300)
    ax.add_patch(Rectangle((10, 10), 620, 280, fill=False, edgecolor=INK, lw=2.0, ls="--"))
    box(ax, 50, 120, 120, 130, lw=2.0)  # an image frame, crossed out
    line(ax, [50, 170], [120, 250], lw=1.6)
    line(ax, [50, 170], [250, 120], lw=1.6)
    text(ax, 200, 225, "IMAGE REMOVED", 21, "bold")
    text(ax, 200, 180, f"Removed after v{version}.", 14)
    text(ax, 200, 145, "No replacement image is available.", 14)
    text(ax, 50, 60, "This example image was taken down.", 11)
    return finish(fig)


# --- drawings, sheets and layouts (#177) --------------------------------------------------------------------------
def _mini(ax, kind, x, y, w, h):
    """A small drawing of `kind` ('plan', 'section' or 'detail'), fitted into the region and centred in it."""
    s = min(w / 480, h / 300)
    ox, oy = x + (w - 480 * s) / 2, y + (h - 300 * s) / 2

    def X(v):
        return ox + v * s

    def Y(v):
        return oy + v * s

    def lw(v):
        return max(0.8, v * s)

    if kind == "plan":
        box(ax, X(70), Y(30), 320 * s, 190 * s, lw=lw(3.0))
        line(ax, [X(230), X(230)], [Y(30), Y(220)], lw=lw(2.0))
        line(ax, [X(70), X(230)], [Y(130), Y(130)], lw=lw(2.0))
        for xx, label in zip((70, 230, 390), "ABC"):
            bubble(ax, X(xx), Y(262), label, 13 * s, max(6, 9 * s))
    elif kind == "section":
        for yy in (30, 140, 250):  # slabs
            box(ax, X(110), Y(yy), 240 * s, 14 * s, fill="#bbbbbb", lw=lw(1.2))
        for xx in (110, 336):  # walls
            box(ax, X(xx), Y(30), 14 * s, 234 * s, lw=lw(1.2), hatch="xxx")
    else:
        box(ax, X(20), Y(30), 140 * s, 200 * s, lw=lw(1.6), hatch="..")
        box(ax, X(160), Y(30), 90 * s, 200 * s, lw=lw(1.4), hatch="\\\\\\\\")
        box(ax, X(250), Y(30), 40 * s, 200 * s, lw=lw(1.6), hatch="++")
        for yy, label in [(190, "Facing brick"), (130, "Insulation"), (70, "Concrete wall")]:
            line(ax, [X(270), X(340)], [Y(yy), Y(yy)], lw=lw(0.9))
            text(ax, X(350), Y(yy), label, max(6, 11 * s))


def _layout_region(ax, name, kind, x, y, w, h):
    """One layout: a dashed region with its name tag, holding a drawing of `kind`."""
    line(ax, [x, x + w, x + w, x, x], [y, y, y + h, y + h, y], lw=1.6, ls="--")
    box(ax, x, y + h - 32, 130, 32, lw=1.2, fill="#dddddd")
    text(ax, x + 65, y + h - 16, name, 11, "bold", "center")
    text(ax, x + 145, y + h - 16, kind, 11)
    _mini(ax, kind, x, y, w, h - 40)


def _sheet(title, number):
    """A drawing sheet with its border and title-block column; the layouts are drawn by the caller."""
    fig, ax = canvas(1100, 790)
    box(ax, 10, 10, 1080, 770, lw=2.4)
    box(ax, 30, 30, 1040, 730, lw=1.2)
    line(ax, [880, 880], [30, 760], lw=1.4)  # title block column
    text(ax, 975, 722, "EXAMPLE STUDIO", 13, "bold", "center")
    for y, label, value in [(640, "PROJECT", "Sample Project"), (560, "SHEET TITLE", title), (140, "DRAWING NUMBER", number)]:
        line(ax, [880, 1070], [y + 38, y + 38], lw=0.9)
        text(ax, 890, y + 22, label, 8)
        text(ax, 890, y - 8, value, 11, "bold")
    return fig, ax


def sheet_one_layout():
    fig, ax = _sheet("ONE LAYOUT", "EX-A-100")
    _layout_region(ax, "LAYOUT 1", "plan", 50, 50, 810, 710)
    return finish(fig)


def sheet_six_layouts():
    fig, ax = _sheet("SIX LAYOUTS", "EX-A-103")
    for name, kind, x, y, w, h in [
        ("LAYOUT 1", "plan", 50, 420, 500, 340), ("LAYOUT 2", "section", 570, 420, 290, 340),
        ("LAYOUT 3", "detail", 50, 50, 250, 350), ("LAYOUT 4", "detail", 320, 50, 250, 350),
        ("LAYOUT 5", "plan", 590, 230, 270, 170), ("LAYOUT 6", "detail", 590, 50, 270, 160),
    ]:
        _layout_region(ax, name, kind, x, y, w, h)
    return finish(fig)


def _single_layout(number, kind):
    fig, ax = canvas(600, 420)
    _layout_region(ax, f"LAYOUT {number}", kind, 20, 20, 560, 380)
    return finish(fig)


def layout_plan():
    return _single_layout(1, "plan")


def layout_section():
    return _single_layout(2, "section")


def layout_detail():
    return _single_layout(3, "detail")


# --- reference expressions and their occurrences (#164) ------------------------------------------------------------
MONO = "DejaVu Sans Mono"


def _expression(note, marked, caption):
    """A drawing note in a fixed-width face with dashed boxes round the parts `marked` ((start, length) in characters)."""
    size = 24
    cw = size * 100 / 72 * 0.602  # one character, in drawing units: points to pixels at 100 dpi, times the face's advance
    x0, y0 = 40, 140
    fig, ax = canvas(900, 240)
    text(ax, x0, y0, note, size, family=MONO)
    for start, length in marked:
        ax.add_patch(Rectangle((x0 + start * cw - 2, y0 - 26), length * cw + 4, 52, fill=False, edgecolor=INK, lw=1.8, ls="--"))
    text(ax, x0, 60, caption, 15, "bold")
    return finish(fig)


NOTE = "SEE 1, 3, 5 & 7/S601 FOR TYPICAL DETAIL"
EXPRESSION = NOTE.index("1, 3, 5")


def inline_layout_sheet_reference():
    return _expression(NOTE, [(EXPRESSION, len("1, 3, 5 & 7/S601"))], "Inline layout and sheet reference")


def standalone_sheet_reference():
    return _expression("SEE S601 FOR TYPICAL DETAIL", [(4, len("S601"))], "Standalone sheet reference")


def drawing_identifier_mention():
    return _expression(NOTE, [(NOTE.index("S601"), len("S601"))], "Drawing identifier mention")


def layout_identifier_mention():
    return _expression(NOTE, [(NOTE.index(n, EXPRESSION), 1) for n in ("1", "3", "5", "7")], "Layout identifier mention")


METADATA = {
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
    "KeyPlan_01.png": key_plan,
    "Perspective_01.png": perspective,
    "Layout_02.png": layout_plan,
    "Layout_03.png": layout_section,
    "Layout_04.png": layout_detail,
    "DrawingSheet_01.png": sheet_one_layout,
    "DrawingSheet_02.png": layout,  # the sheet with three layouts, which Layout_01.png has always shown
    "DrawingSheet_03.png": sheet_six_layouts,
    "InlineLayoutSheetReference_01.png": inline_layout_sheet_reference,
    "StandaloneSheetReference_01.png": standalone_sheet_reference,
    "DrawingIdentifierMention_01.png": drawing_identifier_mention,
    "LayoutIdentifierMention_01.png": layout_identifier_mention,
}

# Images that no current term links but that an earlier release names, so their address must keep answering with
# the same picture ("a released version never changes", docs/contribute/example-images.md). Still drawn, so a
# regeneration reproduces them.
ARCHIVED = {  # module -> {file name -> function returning the PNG bytes}
    "aec_drawing_metadata": {"Layout_01.png": layout},
}

COMMON_SYMBOLS = {
    "Dimension_01.png": dimension,
    "Grid_01.png": grid,
    "ReferenceSymbol_01.png": reference_symbol,
}

DOMAIN_COMMON = {
    "ISection_01.png": i_section,
    "CHS_01.png": chs,
    "RHS_01.png": rhs,
    "SectionChannel_01.png": section_channel,
    "TopHat_01.png": top_hat,
}

FACADE = {
    "DGU_01.png": lambda: curtain_wall_section("DGU", "Double glazing unit (DGU)"),
    "MineralWool_01.png": lambda: curtain_wall_section("MineralWool", "Mineral wool insulation"),
    "Transom_01.png": lambda: curtain_wall_section("Transom", "Transom"),
    "Gasket_01.png": lambda: curtain_wall_section("Gasket", "Gasket"),
    "Sealant_01.png": lambda: curtain_wall_section("Sealant", "Sealant"),
    "Bracket_01.png": lambda: curtain_wall_section("Bracket", "Bracket"),
    "ShelfAngle_01.png": lambda: curtain_wall_section("ShelfAngle", "Shelf angle"),
    "Firestop_01.png": lambda: curtain_wall_section("Firestop", "Firestop"),
    "Mullion_01.png": mullion_plan,
}

DRAWINGS = {  # module -> {file name -> function returning the PNG bytes}
    "aec_drawing_metadata": METADATA,
    "aec_common_symbols": COMMON_SYMBOLS,
    "aec_domain_common": DOMAIN_COMMON,
    "aec_facade_domain": FACADE,
}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    assets = Path(argv[0]) if argv else DEFAULT_ASSETS
    for module, drawings in DRAWINGS.items():
        out = assets / module / "exampleImage"
        out.mkdir(parents=True, exist_ok=True)
        for name, draw in {**drawings, **ARCHIVED.get(module, {})}.items():
            data = draw()
            (out / name).write_bytes(data)
            print(f"wrote {module}/{name} ({len(data) // 1024} KB)")
        versions = sorted({v for _, v in example_images.load_takedown_entries(out).values() if v})
        for version in versions:  # one placeholder per removal version, published at each taken-down address
            holder = example_images.placeholder_file(out, version)
            holder.parent.mkdir(parents=True, exist_ok=True)
            holder.write_bytes(removed_placeholder(version))
            print(f"wrote {module}/{holder.relative_to(assets / module).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
