"""
make_info_card.py
"System Panel" — premium info card for Sahil0591's GitHub profile.

Design language:
  - Sharp-cornered outer card (no border-radius) — architectural feel
  - 3px left accent stripe with green gradient (matches heatmap palette)
  - Name rendered with SVG feGaussianBlur glow (green tint)
  - Colour-coded inline stack badges: blue/purple/orange per category
  - Gradient separator lines (solid → transparent)
  - SMIL animate + animateTransform per group (works in <img> tags)
  - Width 490px, Height 308px
"""

import pathlib

ROOT = pathlib.Path(__file__).parent.parent
OUT  = ROOT / "info-card.svg"

FONT  = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
W     = 490
H     = 308
PX    = 22        # content left padding (after 3px accent stripe)
ANIM_DUR = 0.38

# Palette
BG         = "#0d1117"
BG_BAR     = "#111720"
BORDER     = "#21262d"
ACCENT_LO  = "#006d32"
ACCENT_HI  = "#39d353"
COL_NAME   = "#e6edf3"
COL_ROLE   = "#8b949e"
COL_MUTED  = "#484f58"
COL_SEC    = "#58a6ff"   # section labels
COL_BAR    = "#6e7681"   # title bar text

# Badge colour sets  (fill, stroke, text)
BADGE_LANG  = ("#0d1117", "#1f4b8e", "#58a6ff")   # blue
BADGE_AI    = ("#0d1117", "#3d1f6e", "#bc8cff")   # purple
BADGE_CLOUD = ("#0d1117", "#6e3a0d", "#ffa657")   # orange

# ── Badge geometry helpers ────────────────────────────────────────────────
# Pre-calculated widths for each token (monospace 11px ≈ 6.6px/char + 16px pad)
BADGE_W = {
    "Python": 62, "Java": 48, "TypeScript": 90,
    "PyTorch": 70, "TensorFlow": 90,
    "AWS": 42, "Docker": 62, "Apache Kafka": 105,
}
BADGE_H      = 20
BADGE_R      = 4
BADGE_GAP    = 6
BADGE_FS     = 11
CAT_LABEL_W  = 72   # px column reserved for category label before badges


def esc(s: str) -> str:
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;"))


def badge(x: float, y: float, label: str, colors: tuple) -> tuple[str, float]:
    """Render one badge. Returns (svg_string, next_x)."""
    fill, stroke, text_col = colors
    bw = BADGE_W[label]
    tx = x + bw / 2
    ty = y + BADGE_H / 2 + BADGE_FS * 0.35   # approx baseline
    s = (
        f'<rect x="{x:.1f}" y="{y}" width="{bw}" height="{BADGE_H}" '
        f'rx="{BADGE_R}" fill="{fill}" stroke="{stroke}" stroke-width="1"/>'
        f'<text x="{tx:.1f}" y="{ty:.1f}" font-family="{FONT}" '
        f'font-size="{BADGE_FS}" fill="{text_col}" text-anchor="middle">'
        f'{esc(label)}</text>'
    )
    return s, x + bw + BADGE_GAP


def badge_row(y: float, category: str, items: list[tuple[str, tuple]]) -> list[str]:
    """Render a category label + badges on one row."""
    parts = []
    # Category label, vertically centred within the badge row
    label_y = y + BADGE_H / 2 + 9 * 0.38
    parts.append(
        f'<text x="{PX}" y="{label_y:.1f}" fill="{COL_MUTED}" '
        f'font-size="9" font-weight="600" letter-spacing="0.8">{esc(category)}</text>'
    )
    # Badges start after the reserved label column
    x = float(PX + CAT_LABEL_W)
    for label, colors in items:
        s, x = badge(x, y, label, colors)
        parts.append(s)
    return parts


def smil(begin: float, content: list[str]) -> list[str]:
    b = f"{begin:.2f}s"
    return [
        f'<g opacity="0" transform="translate(0,6)">',
        *[f'  {c}' for c in content],
        f'  <animate attributeName="opacity" from="0" to="1"'
        f' begin="{b}" dur="{ANIM_DUR}s" fill="freeze"/>',
        f'  <animateTransform attributeName="transform" type="translate"'
        f' from="0 6" to="0 0" begin="{b}" dur="{ANIM_DUR}s"'
        f' fill="freeze" calcMode="spline" keySplines="0.2 0.8 0.2 1"/>',
        '</g>',
    ]


def grad_line(x1: float, y: float, w: float = 340) -> str:
    """Horizontal line that fades from ACCENT_LO to transparent."""
    gid = f"gl{int(y)}"
    return (
        f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{ACCENT_LO}" stop-opacity="0.8"/>'
        f'<stop offset="1" stop-color="{ACCENT_LO}" stop-opacity="0"/>'
        f'</linearGradient></defs>'
        f'<line x1="{x1}" y1="{y}" x2="{x1+w}" y2="{y}"'
        f' stroke="url(#{gid})" stroke-width="1"/>'
    )


def build_svg() -> str:
    parts: list[str] = []

    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg"'
        f' width="{W}" height="{H}"'
        f' viewBox="0 0 {W} {H}"'
        f' font-family="{FONT}">'
    )

    # ── Defs: gradients + glow filter ────────────────────────────────────
    parts.append('<defs>')

    # Background gradient (barely perceptible — deep blue-black to pure dark)
    parts.append(
        f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="#0f1923"/>'
        f'<stop offset="1" stop-color="{BG}"/>'
        f'</linearGradient>'
    )

    # Left accent stripe gradient
    parts.append(
        f'<linearGradient id="acc" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0"   stop-color="{ACCENT_LO}"/>'
        f'<stop offset="0.5" stop-color="{ACCENT_HI}"/>'
        f'<stop offset="1"   stop-color="{ACCENT_LO}"/>'
        f'</linearGradient>'
    )

    # Name glow filter
    parts.append(
        '<filter id="glow" x="-20%" y="-40%" width="140%" height="180%">'
        '<feGaussianBlur stdDeviation="3" result="blur"/>'
        '<feFlood flood-color="#39d353" flood-opacity="0.25" result="color"/>'
        '<feComposite in="color" in2="blur" operator="in" result="glow"/>'
        '<feMerge><feMergeNode in="glow"/><feMergeNode in="SourceGraphic"/></feMerge>'
        '</filter>'
    )

    parts.append('</defs>')

    # ── Background + border ───────────────────────────────────────────────
    parts.append(f'<rect width="{W}" height="{H}" fill="url(#bg)"/>')
    parts.append(
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}"'
        f' fill="none" stroke="{BORDER}" stroke-width="1"/>'
    )

    # ── Title bar (Windows CMD style) ────────────────────────────────────
    parts.append(f'<rect x="0" y="0" width="{W}" height="32" fill="{BG_BAR}"/>')
    parts.append(f'<line x1="0" y1="32" x2="{W}" y2="32" stroke="{BORDER}"/>')

    # Left: CMD-style >_ prompt symbol (no box)
    parts.append(
        f'<text x="14" y="21" fill="{ACCENT_HI}" font-size="11" '
        f'font-weight="700" text-anchor="middle">&gt;_</text>'
    )

    # Center: title text
    parts.append(
        f'<text x="{W//2}" y="21" fill="{COL_BAR}" font-size="11.5"'
        f' text-anchor="middle">sahil@github: ~/profile</text>'
    )

    # Right: three rectangular buttons — minimize ─, maximise □, close ×
    # Same palette colours, Windows layout (right side, rectangular, symbols)
    BTN_W = 36
    for i, (symbol, color) in enumerate([
        ("\u2013", "#27c93f"),   # – minimize  (green)
        ("\u25a1", "#ffbd2e"),   # □ maximise  (amber)
        ("\u00d7", "#ff5f56"),   # × close     (red)
    ]):
        bx = W - BTN_W * (3 - i)
        parts.append(f'<line x1="{bx}" y1="0" x2="{bx}" y2="32" stroke="{BORDER}"/>')
        parts.append(
            f'<text x="{bx + BTN_W // 2}" y="21" fill="{color}" '
            f'font-size="14" text-anchor="middle">{symbol}</text>'
        )

    # ── Left accent stripe ────────────────────────────────────────────────
    parts.append(f'<rect x="0" y="32" width="3" height="{H-32}" fill="url(#acc)"/>')

    # ── Content rows (SMIL animated) ─────────────────────────────────────
    t = 0.12   # stagger timer

    # — Name + role --------------------------------------------------------
    parts.extend(smil(t, [
        f'<text x="{PX}" y="72" fill="{COL_NAME}" font-size="20"'
        f' font-weight="700" filter="url(#glow)">sahil0591</text>',
    ])); t += 0.08

    parts.extend(smil(t, [
        f'<text x="{PX}" y="92" fill="{COL_ROLE}" font-size="12">'
        f'AI / ML Engineer\u2002\u00b7\u2002CS Undergrad</text>',
    ])); t += 0.10

    # — Separator ----------------------------------------------------------
    parts.extend(smil(t, [grad_line(PX, 107)])); t += 0.08

    # — STACK section ------------------------------------------------------
    parts.extend(smil(t, [
        f'<text x="{PX}" y="128" fill="{COL_SEC}" font-size="10"'
        f' font-weight="700" letter-spacing="1.5">STACK</text>',
    ])); t += 0.07

    # Languages row
    parts.extend(smil(t, badge_row(136, "LANGUAGES", [
        ("Python",     BADGE_LANG),
        ("Java",       BADGE_LANG),
        ("TypeScript", BADGE_LANG),
    ]))); t += 0.06

    # AI/ML row
    parts.extend(smil(t, badge_row(163, "AI / ML", [
        ("PyTorch",    BADGE_AI),
        ("TensorFlow", BADGE_AI),
    ]))); t += 0.06

    # Cloud row
    parts.extend(smil(t, badge_row(190, "CLOUD", [
        ("AWS",          BADGE_CLOUD),
        ("Docker",       BADGE_CLOUD),
        ("Apache Kafka", BADGE_CLOUD),
    ]))); t += 0.10

    # — Separator ----------------------------------------------------------
    parts.extend(smil(t, [grad_line(PX, 222)])); t += 0.08

    # — Links --------------------------------------------------------------
    parts.extend(smil(t, [
        f'<text x="{PX}" y="243" fill="{COL_SEC}" font-size="10"'
        f' font-weight="700" letter-spacing="1.5">LINKS</text>',
    ])); t += 0.07

    parts.extend(smil(t, [
        # Arrow glyph
        f'<text x="{PX}" y="263" fill="{ACCENT_HI}" font-size="12">\u2192</text>',
        f'<text x="{PX+14}" y="263" fill="{COL_ROLE}" font-size="12">'
        f'sahilshindgikar.vercel.app</text>',
    ])); t += 0.06

    parts.extend(smil(t, [
        f'<text x="{PX}" y="283" fill="{ACCENT_HI}" font-size="12">\u2192</text>',
        f'<text x="{PX+14}" y="283" fill="{COL_ROLE}" font-size="12">'
        f'linkedin.com/in/sahilshindgikar</text>',
    ]))

    parts.append('</svg>')
    return "\n".join(parts)


def main():
    svg = build_svg()
    OUT.write_text(svg, encoding="utf-8")
    print(f"Saved -> {OUT}  ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
