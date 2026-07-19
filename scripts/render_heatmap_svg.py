#!/usr/bin/env python3
"""
render_heatmap_svg.py — Read data/contributions.json and render an animated
contribution heatmap SVG.

The heatmap is a 53-week × 7-day grid of rounded colored boxes with a
diagonal slide-down reveal animation (CSS keyframes, plays once then freezes).

Usage:
    python scripts/render_heatmap_svg.py
"""

import json
import pathlib
from datetime import datetime, timedelta

ROOT = pathlib.Path(__file__).resolve().parent.parent
INPUT = ROOT / "data" / "contributions.json"
OUTPUT = ROOT / "contrib-heatmap.svg"

# ── Color palette (GitHub-ish green ramp) ────────────────────────────
PALETTE = [
    "#161b22",  # level 0 — none
    "#0e4429",  # level 1
    "#006d32",  # level 2
    "#26a641",  # level 3
    "#39d353",  # level 4
    "#69f0a0",  # level 5 — neon top end (extra bright)
]

BG = "#0d1117"
TEXT_COLOR = "#8b949e"
BORDER_COLOR = "#30363d"
FONT = "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
MONO = "'Courier New', Courier, monospace"

# ── Grid geometry ────────────────────────────────────────────────────
BOX_SIZE = 11
BOX_GAP = 3
BOX_R = 2           # border radius
GRID_LEFT = 40      # space for day labels
GRID_TOP = 30       # space for month labels
PAD = 20

WEEKS = 53
DAYS = 7

GRID_W = WEEKS * (BOX_SIZE + BOX_GAP)
GRID_H = DAYS * (BOX_SIZE + BOX_GAP)

SVG_W = GRID_LEFT + GRID_W + PAD * 2
SVG_H = GRID_TOP + GRID_H + 70  # extra for legend + stats

# ── Month labels ─────────────────────────────────────────────────────
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DAY_LABELS = ["", "Mon", "", "Wed", "", "Fri", ""]


def load_data() -> dict:
    """Load contributions JSON."""
    if not INPUT.exists():
        print(f"[!] {INPUT} not found. Run fetch_contributions.py first.")
        # Generate empty placeholder
        return {"days": [], "stats": {"total_contributions": 0}, "username": "mohitexe999-create"}
    return json.loads(INPUT.read_text(encoding="utf-8"))


def build_grid(days: list[dict]) -> list[list[dict]]:
    """
    Organize days into a 53×7 grid (weeks × days-of-week).
    Returns grid[week][day_of_week] = {date, count, level}.
    """
    # Build a date lookup
    lookup = {d["date"]: d for d in days}

    # Find the date range
    if not days:
        today = datetime.utcnow().date()
        start = today - timedelta(days=364)
    else:
        end_date = datetime.strptime(days[-1]["date"], "%Y-%m-%d").date()
        start_date = datetime.strptime(days[0]["date"], "%Y-%m-%d").date()
        # Align to Sunday
        start = start_date - timedelta(days=start_date.weekday() + 1 if start_date.weekday() != 6 else 0)

    grid = []
    current = start
    # Align to Sunday
    while current.weekday() != 6:
        current -= timedelta(days=1)

    for w in range(WEEKS):
        week = []
        for d in range(DAYS):
            date_str = current.strftime("%Y-%m-%d")
            if date_str in lookup:
                week.append(lookup[date_str])
            else:
                week.append({"date": date_str, "count": 0, "level": 0})
            current += timedelta(days=1)
        grid.append(week)

    return grid


def render(data: dict) -> str:
    """Render the contribution heatmap as an SVG string."""
    days = data.get("days", [])
    stats = data.get("stats", {})
    total = stats.get("total_contributions", 0)
    username = data.get("username", "user")

    grid = build_grid(days)

    parts = []

    # SVG open
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {SVG_W} {SVG_H}" '
        f'width="{SVG_W}" height="{SVG_H}" '
        f'style="background:{BG}">'
    )

    # ── CSS animations ───────────────────────────────────────────────
    anim_css = []
    anim_css.append("""
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(5px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        .box {
            opacity: 0;
            animation: slideIn 0.25s ease-out forwards;
        }
        .label { opacity: 0; animation: slideIn 0.3s ease-out forwards; }
    """)

    # Stagger each box by diagonal index (week + day)
    max_diag = WEEKS + DAYS
    for diag in range(max_diag):
        delay = diag * 0.025
        anim_css.append(f".d{diag} {{ animation-delay: {delay:.3f}s; }}")

    parts.append(f'<style>{"".join(anim_css)}</style>')

    # ── Border ───────────────────────────────────────────────────────
    parts.append(
        f'<rect x="1" y="1" width="{SVG_W - 2}" height="{SVG_H - 2}" '
        f'rx="8" fill="{BG}" stroke="{BORDER_COLOR}" stroke-width="1"/>'
    )

    # ── Month labels ─────────────────────────────────────────────────
    placed_months = set()
    for w in range(WEEKS):
        # Check first day of this week
        date_str = grid[w][0]["date"]
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            continue
        month = dt.month - 1
        # Place label if it's roughly the start of the month (day <= 7)
        if dt.day <= 7 and month not in placed_months:
            placed_months.add(month)
            x = PAD + GRID_LEFT + w * (BOX_SIZE + BOX_GAP)
            parts.append(
                f'<text x="{x}" y="{PAD + 12}" '
                f'font-family="{FONT}" font-size="10" fill="{TEXT_COLOR}" '
                f'class="label d{w}">'
                f'{MONTH_NAMES[month]}</text>'
            )

    # ── Day labels ───────────────────────────────────────────────────
    for d in range(DAYS):
        if DAY_LABELS[d]:
            y = PAD + GRID_TOP + d * (BOX_SIZE + BOX_GAP) + BOX_SIZE - 1
            parts.append(
                f'<text x="{PAD + 4}" y="{y}" '
                f'font-family="{FONT}" font-size="10" fill="{TEXT_COLOR}" '
                f'class="label d{d}">'
                f'{DAY_LABELS[d]}</text>'
            )

    # ── Day boxes ────────────────────────────────────────────────────
    for w in range(WEEKS):
        for d in range(DAYS):
            cell = grid[w][d]
            level = min(cell["level"], len(PALETTE) - 1)
            color = PALETTE[level]
            x = PAD + GRID_LEFT + w * (BOX_SIZE + BOX_GAP)
            y = PAD + GRID_TOP + d * (BOX_SIZE + BOX_GAP)
            diag = w + d
            parts.append(
                f'<rect x="{x}" y="{y}" width="{BOX_SIZE}" height="{BOX_SIZE}" '
                f'rx="{BOX_R}" fill="{color}" class="box d{diag}">'
                f'<title>{cell["date"]}: {cell["count"]} contributions</title>'
                f'</rect>'
            )

    # ── Legend (Less → More) ─────────────────────────────────────────
    legend_y = PAD + GRID_TOP + GRID_H + 16
    legend_x = SVG_W - PAD - len(PALETTE) * (BOX_SIZE + BOX_GAP) - 50

    parts.append(
        f'<text x="{legend_x}" y="{legend_y + BOX_SIZE - 1}" '
        f'font-family="{FONT}" font-size="10" fill="{TEXT_COLOR}" '
        f'class="label d{max_diag - 2}">Less</text>'
    )

    for i, color in enumerate(PALETTE):
        bx = legend_x + 30 + i * (BOX_SIZE + BOX_GAP)
        parts.append(
            f'<rect x="{bx}" y="{legend_y}" width="{BOX_SIZE}" height="{BOX_SIZE}" '
            f'rx="{BOX_R}" fill="{color}" class="box d{max_diag - 1}"/>'
        )

    more_x = legend_x + 30 + len(PALETTE) * (BOX_SIZE + BOX_GAP) + 4
    parts.append(
        f'<text x="{more_x}" y="{legend_y + BOX_SIZE - 1}" '
        f'font-family="{FONT}" font-size="10" fill="{TEXT_COLOR}" '
        f'class="label d{max_diag - 1}">More</text>'
    )

    # ── Stats footer ─────────────────────────────────────────────────
    stats_y = legend_y + BOX_SIZE + 20
    parts.append(
        f'<text x="{PAD + GRID_LEFT}" y="{stats_y}" '
        f'font-family="{MONO}" font-size="12" fill="{TEXT_COLOR}" '
        f'class="label d{max_diag}">'
        f'{total:,} contributions in the last year</text>'
    )

    # Streak info on the right
    streak = stats.get("current_streak", 0)
    longest = stats.get("longest_streak", 0)
    parts.append(
        f'<text x="{SVG_W - PAD - 10}" y="{stats_y}" text-anchor="end" '
        f'font-family="{MONO}" font-size="12" fill="{TEXT_COLOR}" '
        f'class="label d{max_diag}">'
        f'🔥 {streak}d streak  ·  🏆 {longest}d longest</text>'
    )

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    print("[1/2] Loading contribution data ...")
    data = load_data()

    print("[2/2] Rendering heatmap SVG ...")
    svg_str = render(data)
    OUTPUT.write_text(svg_str, encoding="utf-8")

    total = data.get("stats", {}).get("total_contributions", 0)
    print(f"[OK] Saved {OUTPUT}  ({total:,} contributions)")


if __name__ == "__main__":
    main()
