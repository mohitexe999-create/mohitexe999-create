#!/usr/bin/env python3
"""
make_info_card.py — Generate a neofetch-style info card as an animated SVG.

Each line fades and slides in on a short stagger so the panel looks
like it's printing next to the ASCII portrait.

Set env STATIC=1 to emit a frozen frame (no animation).

Usage:
    python scripts/make_info_card.py
    STATIC=1 python scripts/make_info_card.py
"""

import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "info-card.svg"
STATIC = os.environ.get("STATIC", "0") == "1"

# ── Card content ─────────────────────────────────────────────────────
USERNAME = "mohitexe999-create"
HOST = "github"

INFO_LINES = [
    ("Now",        "Building cool things"),
    ("Prev",       "Learning & Experimenting"),
    ("Stack",      "Python · JavaScript · React · Node.js"),
    ("Highlights", "Open Source Contributor"),
    ("Editor",     "VS Code"),
    ("OS",         "Windows 11"),
]

# ── Design tokens ────────────────────────────────────────────────────
BG = "#0d1117"
BORDER = "#30363d"
TITLE_COLOR = "#58a6ff"
SEPARATOR_COLOR = "#8b949e"
KEY_COLORS = ["#ff7b72", "#ffa657", "#d2a8ff", "#79c0ff", "#7ee787", "#f0883e"]
VALUE_COLOR = "#c9d1d9"
FONT = "'Courier New', Courier, monospace"
FONT_SIZE = 14
LINE_H = 24
PAD_X = 24
PAD_Y = 20

# ── Dimensions ───────────────────────────────────────────────────────
CARD_W = 470
# title + separator + lines + bottom pad
CARD_H = PAD_Y + LINE_H + 8 + LINE_H + len(INFO_LINES) * LINE_H + PAD_Y + 10

# ── Animation timing ─────────────────────────────────────────────────
STAGGER = 0.18   # seconds between lines
SLIDE_PX = 14    # px slide-in distance
DUR = 0.35       # seconds per line animation


def build_svg() -> str:
    lines_out = []

    # SVG open
    lines_out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {CARD_W} {CARD_H}" '
        f'width="{CARD_W}" height="{CARD_H}" '
        f'style="background:{BG}">'
    )

    # ── CSS animations ───────────────────────────────────────────────
    if not STATIC:
        css_parts = [
            f"""
            @keyframes fadeSlide {{
                from {{ opacity: 0; transform: translateX({SLIDE_PX}px); }}
                to   {{ opacity: 1; transform: translateX(0); }}
            }}
            .line {{
                opacity: 0;
                animation: fadeSlide {DUR}s ease-out forwards;
            }}
            """
        ]
        # Per-line stagger
        total = 2 + len(INFO_LINES)  # title + separator + info rows
        for i in range(total):
            css_parts.append(f".line-{i} {{ animation-delay: {i * STAGGER:.2f}s; }}")

        lines_out.append(f"<style>{' '.join(css_parts)}</style>")
    else:
        lines_out.append(f'<style>.line {{ opacity: 1; }}</style>')

    # ── Border rectangle ─────────────────────────────────────────────
    lines_out.append(
        f'<rect x="1" y="1" width="{CARD_W - 2}" height="{CARD_H - 2}" '
        f'rx="8" fill="{BG}" stroke="{BORDER}" stroke-width="1.5"/>'
    )

    idx = 0
    y = PAD_Y

    # ── Title line: user@host ────────────────────────────────────────
    cls = f'class="line line-{idx}"' if not STATIC else 'class="line"'
    lines_out.append(
        f'<text x="{PAD_X}" y="{y + FONT_SIZE}" {cls} '
        f'font-family="{FONT}" font-size="{FONT_SIZE}px">'
        f'<tspan fill="{TITLE_COLOR}">{USERNAME}</tspan>'
        f'<tspan fill="{VALUE_COLOR}">@</tspan>'
        f'<tspan fill="{TITLE_COLOR}">{HOST}</tspan>'
        f'</text>'
    )
    idx += 1
    y += LINE_H

    # ── Separator dashes ─────────────────────────────────────────────
    sep_len = len(f"{USERNAME}@{HOST}")
    sep = "─" * sep_len
    cls = f'class="line line-{idx}"' if not STATIC else 'class="line"'
    lines_out.append(
        f'<text x="{PAD_X}" y="{y + FONT_SIZE}" {cls} '
        f'font-family="{FONT}" font-size="{FONT_SIZE}px" fill="{SEPARATOR_COLOR}">'
        f'{sep}</text>'
    )
    idx += 1
    y += LINE_H + 4

    # ── Info lines ───────────────────────────────────────────────────
    for i, (key, val) in enumerate(INFO_LINES):
        color = KEY_COLORS[i % len(KEY_COLORS)]
        cls = f'class="line line-{idx}"' if not STATIC else 'class="line"'
        # Escape any special chars
        safe_val = val.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        lines_out.append(
            f'<text x="{PAD_X}" y="{y + FONT_SIZE}" {cls} '
            f'font-family="{FONT}" font-size="{FONT_SIZE}px">'
            f'<tspan fill="{color}" font-weight="bold">{key}</tspan>'
            f'<tspan fill="{SEPARATOR_COLOR}"> ~ </tspan>'
            f'<tspan fill="{VALUE_COLOR}">{safe_val}</tspan>'
            f'</text>'
        )
        idx += 1
        y += LINE_H

    # ── Color blocks (neofetch-style) ────────────────────────────────
    y += 12
    block_w = 18
    block_h = 18
    gap = 6
    cls = f'class="line line-{idx}"' if not STATIC else 'class="line"'
    palette = ["#ff7b72", "#ffa657", "#e3b341", "#7ee787", "#79c0ff", "#d2a8ff", "#f0883e", "#8b949e"]
    lines_out.append(f'<g {cls}>')
    for j, c in enumerate(palette):
        bx = PAD_X + j * (block_w + gap)
        lines_out.append(
            f'<rect x="{bx}" y="{y}" width="{block_w}" height="{block_h}" '
            f'rx="3" fill="{c}"/>'
        )
    lines_out.append('</g>')

    lines_out.append("</svg>")
    return "\n".join(lines_out)


def main():
    mode = "static" if STATIC else "animated"
    print(f"[1/1] Generating {mode} info card ...")
    svg_str = build_svg()
    OUTPUT.write_text(svg_str, encoding="utf-8")
    print(f"[OK] Saved {OUTPUT}")


if __name__ == "__main__":
    main()
