"""
make_ascii_svg.py
- Reads source-prepped.png from the repo root
- Converts to a 100x60 ASCII character grid using density ramp " .`:-=+*cs#%@"
- ROWS=60 chosen so that COLS*CELL_W == ROWS*CELL_H (420==420), preserving the
  1:1 aspect ratio of the square source photo in the final SVG output.
- Renders each row as an SVG <text> element in light gray
- Each row is wrapped in a clipPath that wipes left-to-right, staggered top-to-bottom
  using SVG SMIL <animate> on a rect inside each clipPath
- Outputs avi-ascii.svg in the repo root
"""

import pathlib
import sys
import textwrap
from PIL import Image

ROOT = pathlib.Path(__file__).parent.parent
SRC = ROOT / "source-prepped.png"
OUT = ROOT / "avi-ascii.svg"

# ASCII parameters
# CELL_W:CELL_H = 4.2:7.0 — monospace chars are taller than wide.
# To preserve a 1:1 source aspect ratio: ROWS = COLS * CELL_W / CELL_H
#   = 100 * 4.2 / 7.0 = 60  →  SVG is 420×420 px (perfect square).
COLS = 100
ROWS = 60
DENSITY = ' .`:-=+*cs#%@'   # light → dark (13 chars)
FONT_SIZE = 7                # px — monospace cell approx 4.2 × 7 px
CELL_W = 4.2
CELL_H = 7.0

# Visual dimensions of the SVG
SVG_W = COLS * CELL_W
SVG_H = ROWS * CELL_H

# Animation
TOTAL_DURATION = 2.8         # seconds for full wipe to finish
ROW_STAGGER = TOTAL_DURATION / ROWS  # stagger between rows
WIPE_DURATION = 0.55         # how long each individual row's wipe lasts


def image_to_ascii(img: Image.Image) -> list[str]:
    """Resize image to COLS×ROWS, grayscale, map pixels to density ramp."""
    img = img.convert("L").resize((COLS, ROWS), Image.LANCZOS)
    pixels = list(img.getdata())
    rows: list[str] = []
    for r in range(ROWS):
        row_pixels = pixels[r * COLS:(r + 1) * COLS]
        chars = "".join(DENSITY[int(p / 255 * (len(DENSITY) - 1))] for p in row_pixels)
        rows.append(chars)
    return rows


def escape_xml(s: str) -> str:
    return (s
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def build_svg(ascii_rows: list[str]) -> str:
    lines: list[str] = []

    lines.append(textwrap.dedent(f"""\
        <svg xmlns="http://www.w3.org/2000/svg"
             width="{SVG_W:.1f}" height="{SVG_H:.1f}"
             viewBox="0 0 {SVG_W:.1f} {SVG_H:.1f}">
          <rect width="100%" height="100%" fill="#0d1117"/>
          <defs>
            <style>
              .ac {{ font-family: 'Courier New', Courier, monospace;
                     font-size: {FONT_SIZE}px;
                     fill: #8b949e;
                     white-space: pre; }}
            </style>
    """))

    # One clipPath per row
    for r in range(ROWS):
        clip_id = f"cr{r}"
        y_top = r * CELL_H
        begin = f"{r * ROW_STAGGER:.3f}s"
        end_val = f"{r * ROW_STAGGER + WIPE_DURATION:.3f}s"

        lines.append(f'    <clipPath id="{clip_id}">')
        lines.append(f'      <rect x="0" y="{y_top:.1f}" width="0" height="{CELL_H:.1f}">')
        lines.append(f'        <animate attributeName="width"')
        lines.append(f'                 from="0" to="{SVG_W:.1f}"')
        lines.append(f'                 begin="{begin}" dur="{WIPE_DURATION}s"')
        lines.append(f'                 fill="freeze" calcMode="spline"')
        lines.append(f'                 keySplines="0.25 0.1 0.25 1"/>')
        lines.append( '      </rect>')
        lines.append( '    </clipPath>')

    lines.append("  </defs>")

    # One <text> per row, clipped
    for r, row_chars in enumerate(ascii_rows):
        clip_id = f"cr{r}"
        x = 0
        y = r * CELL_H + FONT_SIZE  # baseline = top + font-size
        safe = escape_xml(row_chars)
        lines.append(
            f'  <text x="{x}" y="{y:.1f}" class="ac"'
            f' clip-path="url(#{clip_id})">{safe}</text>'
        )

    lines.append("</svg>")
    return "\n".join(lines)


def main():
    if not SRC.exists():
        print(f"ERROR: {SRC} not found. Run prep_photo.py first.", file=sys.stderr)
        sys.exit(1)

    print(f"Loading {SRC} …")
    img = Image.open(SRC)

    print(f"Converting to {COLS}×{ROWS} ASCII grid …")
    ascii_rows = image_to_ascii(img)

    print("Building SVG …")
    svg_content = build_svg(ascii_rows)

    OUT.write_text(svg_content, encoding="utf-8")
    print(f"Saved -> {OUT}  ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
