"""
fetch_contributions.py
Scrapes https://github.com/users/Sahil0591/contributions (no API token).
Parses the contribution calendar SVG via BeautifulSoup, extracts per-day
counts and summary stats, and writes data/contributions.json.
"""

import json
import pathlib
import sys
from datetime import datetime

import requests
from bs4 import BeautifulSoup

ROOT    = pathlib.Path(__file__).parent.parent
OUT_DIR = ROOT / "data"
OUT     = OUT_DIR / "contributions.json"

URL     = "https://github.com/users/Sahil0591/contributions"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://github.com/Sahil0591",
}


def fetch_html() -> str:
    print(f"Fetching {URL} ...")
    resp = requests.get(URL, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    print(f"  HTTP {resp.status_code}  ({len(resp.text):,} chars)")
    return resp.text


def parse_contributions(html: str) -> list[dict]:
    """
    Extract contribution days from the GitHub contribution calendar.

    GitHub no longer includes data-count on <td> elements; instead the count
    lives in the text of a matching <tool-tip> element:
      "No contributions on July 20th."
      "3 contributions on July 21st."

    Strategy:
      1. Build a map  td_id -> count  by parsing every <tool-tip for="…"> text.
      2. Walk each <td data-date> and look up its id in the map.
      3. Fall back to data-level (0-4) if no tooltip is found.
    """
    import re
    soup = BeautifulSoup(html, "html.parser")

    # Build tooltip map: element-id -> int count
    tip_map: dict[str, int] = {}
    for tip in soup.find_all("tool-tip"):
        target_id = tip.get("for", "").strip()
        if not target_id:
            continue
        text = tip.get_text(" ", strip=True)
        m = re.match(r"(\d+)\s+contribution", text, re.IGNORECASE)
        if m:
            tip_map[target_id] = int(m.group(1))
        else:
            tip_map[target_id] = 0   # "No contributions …"

    # Walk contribution cells
    days = []
    for el in soup.find_all("td", attrs={"data-date": True}):
        date  = el.get("data-date", "").strip()
        level = int(el.get("data-level", "0") or 0)
        el_id = el.get("id", "").strip()

        # Prefer tooltip count; fall back to deriving a pseudo-count from level
        if el_id in tip_map:
            count = tip_map[el_id]
        else:
            # level 0→0, 1→1, 2→3, 3→6, 4→10  (rough approximation)
            count = [0, 1, 3, 6, 10][min(level, 4)]

        if not date:
            continue
        days.append({"date": date, "count": count, "level": level})

    days.sort(key=lambda d: d["date"])
    return days


def compute_stats(days: list[dict]) -> dict:
    counts = [d["count"] for d in days]
    total  = sum(counts)
    max_c  = max(counts, default=0)
    # longest streak
    streak = cur = 0
    for c in counts:
        if c > 0:
            cur += 1
            streak = max(streak, cur)
        else:
            cur = 0
    return {
        "total_contributions": total,
        "max_single_day":      max_c,
        "longest_streak_days": streak,
        "days_with_activity":  sum(1 for c in counts if c > 0),
        "total_days":          len(days),
    }


def main():
    html = fetch_html()
    days = parse_contributions(html)

    if not days:
        print("ERROR: No contribution data found. GitHub may have changed its markup.", file=sys.stderr)
        print("  Saving raw HTML sample for inspection -> data/contributions_debug.html")
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / "contributions_debug.html").write_text(html[:8000], encoding="utf-8")
        sys.exit(1)

    stats = compute_stats(days)
    print(f"  Parsed {len(days)} days  |  total contributions: {stats['total_contributions']}")
    print(f"  Max single day: {stats['max_single_day']}  |  longest streak: {stats['longest_streak_days']} days")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "stats":      stats,
        "days":       days,
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Saved -> {OUT}  ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
