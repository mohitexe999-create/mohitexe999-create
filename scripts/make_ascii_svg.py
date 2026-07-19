#!/usr/bin/env python3
"""
make_ascii_svg.py — Convert a prepped grayscale image into an animated,
monochrome ASCII-art SVG that "types" itself in row by row.

The SVG uses SMIL animations so it plays inside GitHub READMEs.
Each row is revealed left-to-right via an animated clip-rect,
staggered top-to-bottom.  Plays once, then freezes.

Usage:
    python scripts/make_ascii_svg.py
"""

import pathlib
import xml.etree.ElementTree as ET
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
INPUT = ROOT / "source-prepped.png"
OUTPUT = ROOT / "mohit-ascii.svg"

# ── Tuning knobs ─────────────────────────────────────────────────────────
COLS = 100          # characters per row
ROWS = 53           # rows
FONT_SIZE = 7       # px  (monospace)
CHAR_W = 4.2        # px per character (at this font size)
LINE_H = 7.5        # px per row
FG_COLOR = "#b0b0b0" # monochrome fill
BG_COLOR = "#0d1117" # dark terminal background
CURSOR_COLOR = "#58a6ff"

# Bright (sparse) → dark (dense)
RAMP = " .`:-=+*cs#%@"

# Animation timing
ROW_DUR = 0.45      # seconds per row reveal
ROW_STAGGER = 0.06  # seconds between row starts
CURSOR_W = CHAR_W   # cursor block width


def image_to_ascii(img_path: pathlib.Path) -> list[str]:
    """Downsample image to COLS×ROWS and map brightness → ASCII."""
    img = Image.open(img_path).convert("L")
    img = img.resize((COLS, ROWS), Image.LANCZOS)

    lines = []
    for y in range(ROWS):
        row = []
        for x in range(COLS):
            brightness = img.getpixel((x, y))          # 0 = black, 255 = white
            idx = int(brightness / 255 * (len(RAMP) - 1))
            row.append(RAMP[idx])
        lines.append("".join(row))
    return lines


def build_svg(lines: list[str]) -> str:
    """Build an SVG string with SMIL row-wipe + cursor animation."""
    svg_w = COLS * CHAR_W + 20       # 10 px padding each side
    svg_h = ROWS * LINE_H + 20

    ns = "http://www.w3.org/2000/svg"
    ET.register_namespace("", ns)
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

    svg = ET.Element("svg", {
        "xmlns": ns,
        "viewBox": f"0 0 {svg_w:.1f} {svg_h:.1f}",
        "width": str(int(svg_w)),
        "height": str(int(svg_h)),
        "style": f"background:{BG_COLOR}",
    })

    # ── Defs: one clipPath per row ───────────────────────────────────
    defs = ET.SubElement(svg, "defs")
    for i in range(len(lines)):
        cp = ET.SubElement(defs, "clipPath", {"id": f"r{i}"})
        rect = ET.SubElement(cp, "rect", {
            "x": "10",
            "y": str(10 + i * LINE_H),
            "width": "0",
            "height": str(LINE_H + 1),
        })
        begin = f"{i * ROW_STAGGER:.2f}s"
        ET.SubElement(rect, "animate", {
            "attributeName": "width",
            "from": "0",
            "to": str(COLS * CHAR_W + 2),
            "begin": begin,
            "dur": f"{ROW_DUR}s",
            "fill": "freeze",
        })

    # ── Style (monospace font) ───────────────────────────────────────
    style = ET.SubElement(svg, "style")
    style.text = (
        f"text {{ font-family: 'Courier New', Courier, monospace; "
        f"font-size: {FONT_SIZE}px; fill: {FG_COLOR}; "
        f"dominant-baseline: hanging; white-space: pre; }}"
    )

    # ── Text rows, each clipped ──────────────────────────────────────
    for i, line in enumerate(lines):
        g = ET.SubElement(svg, "g", {"clip-path": f"url(#r{i})"})
        # Escape special XML characters
        safe = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        t = ET.SubElement(g, "text", {
            "x": "10",
            "y": str(10 + i * LINE_H + 1),
        })
        t.text = safe

    # ── Cursor blocks (one per row) ──────────────────────────────────
    for i in range(len(lines)):
        cursor = ET.SubElement(svg, "rect", {
            "x": "10",
            "y": str(10 + i * LINE_H),
            "width": str(CURSOR_W),
            "height": str(LINE_H),
            "fill": CURSOR_COLOR,
            "opacity": "0.85",
        })
        begin = f"{i * ROW_STAGGER:.2f}s"
        end_time = i * ROW_STAGGER + ROW_DUR
        # Slide cursor across the row
        ET.SubElement(cursor, "animate", {
            "attributeName": "x",
            "from": "10",
            "to": str(10 + COLS * CHAR_W),
            "begin": begin,
            "dur": f"{ROW_DUR}s",
            "fill": "freeze",
        })
        # Then hide it
        ET.SubElement(cursor, "animate", {
            "attributeName": "opacity",
            "from": "0.85",
            "to": "0",
            "begin": f"{end_time:.2f}s",
            "dur": "0.15s",
            "fill": "freeze",
        })

    return ET.tostring(svg, encoding="unicode", xml_declaration=True)


def main():
    if not INPUT.exists():
        print(f"[!] Prepped image not found: {INPUT}")
        print("    Run  python scripts/prep_photo.py  first.")

        # Fallback: generate a simple gradient test pattern
        print("[~] Generating a placeholder ASCII pattern instead ...")
        lines = []
        for y in range(ROWS):
            row = []
            for x in range(COLS):
                # Create a circular gradient pattern
                cx, cy = COLS / 2, ROWS / 2
                dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                max_dist = (cx ** 2 + cy ** 2) ** 0.5
                brightness = min(1.0, dist / (max_dist * 0.6))
                idx = int(brightness * (len(RAMP) - 1))
                row.append(RAMP[idx])
            lines.append("".join(row))
    else:
        print(f"[1/2] Converting {INPUT.name} to ASCII grid ({COLS}×{ROWS}) ...")
        lines = image_to_ascii(INPUT)

    print("[2/2] Building animated SVG ...")
    svg_str = build_svg(lines)

    OUTPUT.write_text(svg_str, encoding="utf-8")
    print(f"[OK] Saved {OUTPUT}")


if __name__ == "__main__":
    main()
