"""
render_heatmap_svg.py
Reads data/contributions.json and renders a GitHub-style contribution
heatmap SVG matching the AVIVASHISHTA29 reference aesthetic:

  - Transparent background
  - 13x13 cells, rx=2.5, step=16px, 53 weeks x 7 days
  - CSS pop + flash animations (fill-mode: both)
  - @media prefers-reduced-motion fallback (opacity:1, no animation)
  - Diagonal stagger: delay = week*0.065 + day*0.036
  - Active cells (.g): pop + brightness flash
  - Empty cells (.e):  pop only (no flash)
  - 5-level GitHub palette (uses data-level 0-4 from JSON)
  - Bold total contributions text at bottom
  - Width 888px, Height 158px
"""

import json
import pathlib
import sys
from datetime import datetime, timedelta

ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "data" / "contributions.json"
OUT  = ROOT / "contrib-heatmap.svg"

# ── Palette (level 0-4, matching GitHub) ─────────────────────────────────
PALETTE = {
    0: "#161b22",   # no contribution
    1: "#0e4429",
    2: "#006d32",
    3: "#26a641",
    4: "#39d353",
}

# ── Grid geometry ─────────────────────────────────────────────────────────
WEEKS     = 53
DAYS      = 7
CELL      = 13      # px
GAP       = 3       # px
STEP      = CELL + GAP   # 16px
CORNER_R  = 2.5
PAD_LEFT  = 34      # x of first cell column
PAD_TOP   = 24      # y of first cell row
SVG_W     = 888
SVG_H     = 158

# ── Animation ─────────────────────────────────────────────────────────────
ANIM_DUR  = 0.55    # s — matches avi-ascii wipe duration
FLASH_DUR = 0.70    # s
W_STEP    = 0.065   # s per week column
D_STEP    = 0.036   # s per day row

# ── Labels ────────────────────────────────────────────────────────────────
DAY_LABELS   = {1: "Mon", 3: "Wed", 5: "Fri"}   # row index → label
MONTH_ABBREV = ["Jan","Feb","Mar","Apr","May","Jun",
                "Jul","Aug","Sep","Oct","Nov","Dec"]


# ── Helpers ───────────────────────────────────────────────────────────────
def build_week_grid(days_list: list[dict]) -> list[list[dict | None]]:
    """
    53 cols (weeks) x 7 rows (days, Sun=0).
    Each cell: {date, count, level} or None for out-of-range padding.
    """
    if not days_list:
        return [[None]*DAYS for _ in range(WEEKS)]

    first = datetime.strptime(days_list[0]["date"], "%Y-%m-%d")
    # Roll back to the Sunday on or before the first day
    start = first - timedelta(days=(first.weekday() + 1) % 7)

    by_date = {d["date"]: d for d in days_list}
    grid = []
    cur = start
    for _ in range(WEEKS):
        col = []
        for _ in range(DAYS):
            ds = cur.strftime("%Y-%m-%d")
            col.append(by_date.get(ds))   # None if outside range
            cur += timedelta(days=1)
        grid.append(col)
    return grid


def month_labels(grid: list[list[dict | None]]) -> list[tuple[int, str]]:
    """(x_pixel, month_abbrev) for the first week each month appears."""
    seen: set[str] = set()
    result = []
    for w, col in enumerate(grid):
        for cell in col:
            if cell is None:
                continue
            m = cell["date"][5:7]
            if m not in seen:
                seen.add(m)
                result.append((PAD_LEFT + w * STEP, MONTH_ABBREV[int(m) - 1]))
            break
    return result


def build_svg(grid: list[list[dict | None]], stats: dict) -> str:
    parts: list[str] = []

    # ── Header ──────────────────────────────────────────────────────────
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{SVG_W}" height="{SVG_H}" '
        f'viewBox="0 0 {SVG_W} {SVG_H}" '
        f'font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">'
    )

    # ── CSS ──────────────────────────────────────────────────────────────
    parts.append('<style>')
    parts.append('  text.lbl { fill:#7d8590; font-size:13px; font-weight:600; }')
    parts.append('  text.total { fill:#e6edf3; font-size:15px; font-weight:700; }')
    parts.append(f'  .c {{ transform-box:fill-box; transform-origin:center; opacity:0;'
                 f' animation:pop {ANIM_DUR}s ease-out both; }}')
    parts.append(f'  .g {{ animation:pop {ANIM_DUR}s ease-out both,'
                 f' flash {FLASH_DUR}s ease-out both; }}')
    parts.append(
        '  @keyframes pop '
        '{ 0%{opacity:0;transform:scale(.2)} '
        '60%{opacity:1;transform:scale(1.1)} '
        '100%{opacity:1;transform:scale(1)} }'
    )
    parts.append(
        '  @keyframes flash '
        '{ 0%{filter:brightness(2.4)} '
        '45%{filter:brightness(2.4)} '
        '100%{filter:brightness(1)} }'
    )
    parts.append('  @media (prefers-reduced-motion: reduce) '
                 '{ .c { opacity:1 !important; animation:none !important; } }')
    parts.append('</style>')

    # Transparent background
    parts.append(f'<rect width="{SVG_W}" height="{SVG_H}" fill="none"/>')

    # ── Month labels ─────────────────────────────────────────────────────
    for x, month in month_labels(grid):
        parts.append(f'<text class="lbl" x="{x}" y="16">{month}</text>')

    # ── Day labels ───────────────────────────────────────────────────────
    for d, label in DAY_LABELS.items():
        y = PAD_TOP + d * STEP + CELL - 1
        parts.append(f'<text class="lbl" x="2" y="{y}">{label}</text>')

    # ── Cells ────────────────────────────────────────────────────────────
    for w, col in enumerate(grid):
        for d, cell in enumerate(col):
            cx    = PAD_LEFT + w * STEP
            cy    = PAD_TOP  + d * STEP
            delay = f"{w * W_STEP + d * D_STEP:.3f}s"

            if cell is None:
                color  = PALETTE[0]
                cls    = "c e"
                title  = ""
            elif cell["level"] == 0:
                color  = PALETTE[0]
                cls    = "c e"
                title  = f'No contributions on {cell["date"]}.'
            else:
                level  = min(cell["level"], 4)
                color  = PALETTE[level]
                cls    = "c g"
                n      = cell["count"]
                title  = f'{n} contribution{"s" if n != 1 else ""} on {cell["date"]}.'

            rect = (
                f'<rect class="{cls}" x="{cx}" y="{cy}" '
                f'width="{CELL}" height="{CELL}" '
                f'rx="{CORNER_R}" fill="{color}" '
                f'style="animation-delay:{delay}"/>'
            )
            if title:
                parts.append(f'<rect class="{cls}" x="{cx}" y="{cy}" '
                              f'width="{CELL}" height="{CELL}" '
                              f'rx="{CORNER_R}" fill="{color}" '
                              f'style="animation-delay:{delay}">'
                              f'<title>{title}</title></rect>')
            else:
                parts.append(rect)

    # ── Total text ───────────────────────────────────────────────────────
    total  = stats.get("total_contributions", 0)
    parts.append(
        f'<text class="total" x="{PAD_LEFT}" y="152">'
        f'{total:,} contributions in the last year</text>'
    )

    parts.append('</svg>')
    return "\n".join(parts)


def main():
    if not SRC.exists():
        print(f"ERROR: {SRC} not found. Run fetch_contributions.py first.", file=sys.stderr)
        sys.exit(1)

    print(f"Loading {SRC} ...")
    payload = json.loads(SRC.read_text(encoding="utf-8"))
    days    = payload["days"]
    stats   = payload["stats"]
    print(f"  {len(days)} days | total: {stats['total_contributions']} | max/day: {stats['max_single_day']}")

    print("Building grid ...")
    grid = build_week_grid(days)

    print("Rendering SVG ...")
    svg = build_svg(grid, stats)

    OUT.write_text(svg, encoding="utf-8")
    print(f"Saved -> {OUT}  ({OUT.stat().st_size:,} bytes)  [{SVG_W}x{SVG_H}px]")


if __name__ == "__main__":
    main()
