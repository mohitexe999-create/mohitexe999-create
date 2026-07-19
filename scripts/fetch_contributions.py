#!/usr/bin/env python3
"""
fetch_contributions.py — Scrape the public GitHub contribution calendar
for a user and write data/contributions.json.

No personal access token needed — GitHub serves the contribution calendar
as public HTML at https://github.com/users/<username>/contributions.

Usage:
    python scripts/fetch_contributions.py
"""

import json
import pathlib
from datetime import datetime, timedelta, timezone
from collections import defaultdict

import requests
from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data" / "contributions.json"

USERNAME = "mohitexe999-create"
URL = f"https://github.com/users/{USERNAME}/contributions"


def fetch_and_parse() -> dict:
    """Fetch the contributions page and parse day cells."""
    print(f"[1/3] Fetching {URL} ...")
    resp = requests.get(URL, headers={"Accept": "text/html"}, timeout=30)
    resp.raise_for_status()

    print("[2/3] Parsing contribution cells ...")
    soup = BeautifulSoup(resp.text, "html.parser")

    days = []
    cells = soup.select("td.ContributionCalendar-day")

    for td in cells:
        date_str = td.get("data-date")
        level = td.get("data-level", "0")
        if not date_str:
            continue

        # Extract count from tooltip text
        tooltip_id = td.get("id", "")
        tooltip = soup.find("tool-tip", attrs={"for": tooltip_id})
        count = 0
        if tooltip:
            text = tooltip.get_text(strip=True)
            # Parse "X contributions on ..." or "No contributions on ..."
            if text.startswith("No"):
                count = 0
            else:
                try:
                    count = int(text.split()[0].replace(",", ""))
                except (ValueError, IndexError):
                    count = 0

        days.append({
            "date": date_str,
            "count": count,
            "level": int(level),
        })

    # Sort by date
    days.sort(key=lambda d: d["date"])
    return days


def compute_stats(days: list[dict]) -> dict:
    """Derive stats from the day list."""
    total = sum(d["count"] for d in days)
    best_day = max(days, key=lambda d: d["count"]) if days else {"date": "", "count": 0}

    # Current streak (consecutive days with count > 0 ending at the last day or today)
    current_streak = 0
    for d in reversed(days):
        if d["count"] > 0:
            current_streak += 1
        else:
            break

    # Longest streak
    longest = 0
    streak = 0
    for d in days:
        if d["count"] > 0:
            streak += 1
            longest = max(longest, streak)
        else:
            streak = 0

    # Monthly totals
    monthly = defaultdict(int)
    for d in days:
        month = d["date"][:7]  # "YYYY-MM"
        monthly[month] += d["count"]

    return {
        "total_contributions": total,
        "current_streak": current_streak,
        "longest_streak": longest,
        "best_day": {"date": best_day["date"], "count": best_day["count"]},
        "monthly_totals": dict(sorted(monthly.items())),
    }


def main():
    days = fetch_and_parse()
    stats = compute_stats(days)

    data = {
        "username": USERNAME,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "days": days,
        "stats": stats,
    }

    print(f"[3/3] Writing {OUTPUT} ...")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"[OK] {stats['total_contributions']} contributions, "
          f"streak: {stats['current_streak']}d, "
          f"longest: {stats['longest_streak']}d, "
          f"best: {stats['best_day']['count']} on {stats['best_day']['date']}")


if __name__ == "__main__":
    main()
