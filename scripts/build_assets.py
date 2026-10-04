"""Generate the static SVG assets for the snowyarch profile README.

Run from the repository root:

    python3 scripts/build_assets.py

Every asset is plain, hand-built SVG: no scripts, no external fonts,
no embedded images, no metadata. All text that appears in an asset is
written literally in this file, so this file is the full public surface
of the artwork.
"""

import math
import random
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent.parent / "assets"

# Palette
VOID = "#070A10"
PANEL = "#101724"
RAISED = "#172235"
BLUE = "#2D8CFF"
PINK = "#FF4FCB"
GREEN = "#C6FF3A"
WHITE = "#EDF5FF"
ICE = "#A7B8CE"
LINE = "#30435E"

W = 720  # every asset shares one width so they scale together on mobile

FONT = ("ui-monospace, 'SF Mono', SFMono-Regular, Menlo, Consolas, "
        "'DejaVu Sans Mono', 'Liberation Mono', monospace")


# ---------------------------------------------------------------- helpers

def svg(h, body, w=W, bg=True):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" fill="none">\n'
        f'<style>text{{font-family:{FONT};}}</style>\n'
        f'{DEFS}\n'
        + (f'<rect width="{w}" height="{h}" fill="{VOID}"/>\n' if bg else "")
        + f'{body}\n</svg>\n'
    )


DEFS = f"""<defs>
<pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse">
<path d="M24 0H0V24" stroke="{LINE}" stroke-width="0.6" opacity="0.45"/>
</pattern>
<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">
<rect width="4" height="1" fill="{WHITE}" opacity="0.025"/>
</pattern>
<filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
<feGaussianBlur stdDeviation="3" result="b"/>
<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>
<linearGradient id="fadeR" x1="0" x2="1" y1="0" y2="0">
<stop offset="0" stop-color="{BLUE}" stop-opacity="0.9"/>
<stop offset="1" stop-color="{BLUE}" stop-opacity="0"/>
</linearGradient>
<linearGradient id="fadeP" x1="0" x2="1" y1="0" y2="0">
<stop offset="0" stop-color="{PINK}" stop-opacity="0"/>
<stop offset="0.5" stop-color="{PINK}" stop-opacity="0.9"/>
<stop offset="1" stop-color="{PINK}" stop-opacity="0"/>
</linearGradient>
<linearGradient id="reflect" x1="0" x2="0" y1="0" y2="1">
<stop offset="0" stop-color="{PINK}" stop-opacity="0.28"/>
<stop offset="1" stop-color="{PINK}" stop-opacity="0"/>
</linearGradient>
<linearGradient id="sky" x1="0" x2="0" y1="0" y2="1">
<stop offset="0" stop-color="{VOID}"/>
<stop offset="1" stop-color="#0E1830"/>
</linearGradient>
</defs>"""


def t(x, y, s, size=22, fill=WHITE, weight="normal", anchor="start",
      spacing=0, opacity=1, extra=""):
    """A single line of text."""
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    op = f' opacity="{opacity}"' if opacity != 1 else ""
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}"{ls}{op}{extra}>'
            f'{escape(s)}</text>')


def rect(x, y, w, h, fill="none", stroke=None, sw=1.5, rx=0, opacity=1,
         extra=""):
    st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    op = f' opacity="{opacity}"' if opacity != 1 else ""
    r = f' rx="{rx}"' if rx else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"'
            f'{st}{r}{op}{extra}/>')


def line(x1, y1, x2, y2, stroke=LINE, sw=1, opacity=1, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    op = f' opacity="{opacity}"' if opacity != 1 else ""
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{stroke}" stroke-width="{sw}"{d}{op}/>')


def corners(x, y, w, h, color=ICE, n=14, sw=2):
    """HUD-style corner brackets around a box."""
    p = []
    for cx, cy, dx, dy in ((x, y, 1, 1), (x + w, y, -1, 1),
                           (x, y + h, 1, -1), (x + w, y + h, -1, -1)):
        p.append(f'<path d="M{cx} {cy + dy * n}V{cy}H{cx + dx * n}" '
                 f'stroke="{color}" stroke-width="{sw}"/>')
    return "\n".join(p)


def window(x, y, w, h, color, title, right="", fill=PANEL, bar=RAISED):
    """Terminal window chrome: frame, title bar, three drawn dots."""
    out = [
        rect(x, y, w, h, fill=fill),
        rect(x, y, w, h, fill="url(#scan)"),
        rect(x, y, w, 38, fill=bar),
        line(x, y + 38, x + w, y + 38, stroke=color, sw=1.2, opacity=0.7),
        rect(x, y, w, h, stroke=color, sw=1.6, opacity=0.55,
             extra=' filter="url(#glow)"'),
        rect(x, y, w, h, stroke=color, sw=1.2),
    ]
    for i in range(3):
        out.append(f'<circle cx="{x + 22 + i * 20}" cy="{y + 19}" r="5.5" '
                   f'stroke="{color}" stroke-width="1.6"'
                   f'{" fill=" + chr(34) + color + chr(34) if i == 0 else ""}/>')
    out.append(t(x + 86, y + 27, title, 22, ICE))
    if right:
        out.append(t(x + w - 16, y + 27, right, 22, color, anchor="end"))
    return "\n".join(out)


def tag(x, y, label, color=GREEN, size=20, pad=10, h=32):
    """Outlined status label. The word carries the meaning; color is extra."""
    w = int(len(label) * size * 0.62 + pad * 2)
    return "\n".join([
        rect(x, y, w, h, fill=VOID, stroke=color, sw=1.4),
        t(x + pad, y + h / 2 + size * 0.36, label, size, color, "bold"),
    ]), w


def lock(cx, cy, s=1.0, color=ICE):
    """Abstract padlock glyph."""
    return (f'<g transform="translate({cx} {cy}) scale({s})">'
            f'<path d="M-16 -4V-18A16 16 0 0 1 16 -18V-4" stroke="{color}" '
            f'stroke-width="5" fill="none"/>'
            f'<rect x="-26" y="-6" width="52" height="40" rx="4" '
            f'stroke="{color}" stroke-width="4" fill="{RAISED}"/>'
            f'<rect x="-3" y="6" width="6" height="14" fill="{color}"/>'
            f'</g>')


def rail(y, x0=0, x1=W, color=BLUE, nodes=(), opacity=1):
    out = [line(x0, y, x1, y, stroke=color, sw=1.5, opacity=0.6 * opacity)]
    for nx in nodes:
        out.append(rect(nx - 5, y - 5, 10, 10, fill=VOID, stroke=color,
                        sw=1.5, opacity=opacity))
    return "\n".join(out)


def write(name, content):
    (OUT / name).write_text(content, encoding="utf-8")


# ---------------------------------------------------------------- assets

def header():
    rnd = random.Random(7)
    h = 440
    horizon = 330
    b = [rect(0, 0, W, horizon, fill="url(#sky)")]

    # rain: short diagonal strokes, very quiet
    for _ in range(90):
        x = rnd.uniform(0, W)
        y = rnd.uniform(0, horizon - 20)
        ln = rnd.uniform(8, 22)
        b.append(line(round(x, 1), round(y, 1), round(x - ln * 0.25, 1),
                      round(y + ln, 1), stroke=ICE, sw=0.8,
                      opacity=round(rnd.uniform(0.08, 0.22), 2)))

    # striped cold moon
    b.append('<clipPath id="moonclip">' + "".join(
        f'<rect x="540" y="{36 + i * 9}" width="140" height="{9 - min(i, 6)}"/>'
        for i in range(12)) + '</clipPath>')
    b.append(f'<circle cx="610" cy="96" r="54" fill="{PINK}" opacity="0.85" '
             f'clip-path="url(#moonclip)"/>')
    b.append(f'<circle cx="610" cy="96" r="62" stroke="{PINK}" '
             f'stroke-width="1" opacity="0.35"/>')

    # skyline with lit windows
    x = -4
    while x < W:
        bw = rnd.choice([34, 42, 50, 58, 66])
        bh = rnd.randint(60, 170)
        if 470 < x < 690:
            bh = rnd.randint(50, 120)  # keep the moon visible
        top = horizon - bh
        b.append(rect(x, top, bw - 4, bh, fill="#0B1220", stroke=LINE, sw=1))
        if rnd.random() < 0.3:
            b.append(line(x + bw / 2 - 2, top, x + bw / 2 - 2, top - 14,
                          stroke=LINE, sw=1.2))
        for wy in range(top + 8, horizon - 8, 11):
            for wx in range(x + 6, x + bw - 10, 9):
                r = rnd.random()
                if r < 0.10:
                    c = rnd.choice([PINK, BLUE, ICE, ICE, GREEN])
                    b.append(rect(wx, wy, 4, 5, fill=c,
                                  opacity=round(rnd.uniform(0.35, 0.8), 2)))
        x += bw

    # horizon line, reflection, perspective grid
    b.append(rect(0, horizon, W, h - horizon, fill="url(#reflect)"))
    b.append(line(0, horizon, W, horizon, stroke=PINK, sw=1.6,
                  opacity=0.9))
    b.append(line(0, horizon, W, horizon, stroke=PINK, sw=5, opacity=0.25))
    vx = W / 2
    for i in range(-14, 15):
        b.append(line(vx + i * 18, horizon, vx + i * 90, h, stroke=BLUE,
                      sw=0.8, opacity=0.35))
    yy, step = horizon + 6, 6
    while yy < h:
        b.append(line(0, round(yy, 1), W, round(yy, 1), stroke=BLUE, sw=0.8,
                      opacity=0.35))
        step *= 1.38
        yy += step

    # boot terminal
    b.append(window(24, 24, 410, 156, PINK, "session", "01"))
    b.append(t(44, 92, "> connection established", 24, PINK))
    b.append(t(44, 124, "> public node online", 24, WHITE))
    b.append(t(44, 156, "> session initialized", 24, GREEN))
    b.append(rect(362, 137, 13, 23, fill=GREEN))

    # wordmark with a small static glitch split
    wm = dict(size=104, weight="bold",
              extra=' textLength="520" lengthAdjust="spacingAndGlyphs"')
    b.append(t(37, 271, "snowyarch", fill=BLUE, opacity=0.8, **wm))
    b.append(t(43, 267, "snowyarch", fill=PINK, opacity=0.8, **wm))
    b.append(t(40, 269, "snowyarch", fill=WHITE,
               size=104, weight="bold",
               extra=' textLength="520" lengthAdjust="spacingAndGlyphs" '
                     f'stroke="{VOID}" stroke-width="2" paint-order="stroke"'))
    for gx, gy, gw, gc in ((572, 214, 34, PINK), (584, 222, 18, BLUE),
                           (566, 252, 26, BLUE)):
        b.append(rect(gx, gy, gw, 3, fill=gc, opacity=0.8))

    # identity line under the wordmark
    b.append(rect(28, 284, 664, 40, fill=VOID, opacity=0.82))
    b.append(t(42, 313, "ZÜRICH // CH", 28, PINK, "bold", spacing=1))
    b.append(t(680, 312, "AFTERHOURS / PERSONAL NODE", 24, ICE,
               anchor="end"))

    # HUD footer
    b.append(rect(0, h - 38, W, 38, fill=VOID, opacity=0.86))
    b.append(t(24, h - 12, "NODE ZH-01", 22, BLUE, "bold"))
    b.append(t(W / 2, h - 12, "public surface", 22, ICE, anchor="middle"))
    for i in range(5):
        hh = 6 + i * 4
        b.append(rect(650 + i * 9, h - 12 - hh, 5, hh,
                      fill=GREEN if i < 4 else LINE))
    b.append(corners(8, 8, W - 16, h - 16, ICE, 18, 1.5))
    write("header.svg", svg(h, "\n".join(b)))


def operator_note():
    h = 258
    b = [window(16, 16, W - 32, h - 32, PINK, "operator.note",
                "AFTERHOURS")]
    b.append(t(40, 94, "> whoami", 26, PINK))
    b.append(t(40, 136, "builder · researcher · markets obsessive", 25,
               WHITE))
    b.append(t(40, 172, "philosophy nerd · systems explorer", 25, WHITE))
    b.append(t(40, 208, "internet-native learner", 25, WHITE))
    b.append(rect(402, 189, 13, 24, fill=PINK))
    b.append(t(W - 40, 208, "still learning", 22, GREEN, anchor="end"))
    write("operator-note.svg", svg(h, "\n".join(b)))


INDEX_ROWS = [
    ("01", "DEBTWATCH", "macro / credit research", BLUE),
    ("02", "AI BUBBLEWATCH", "ai economics research", BLUE),
    ("03", "CULTURE / LEGITIMACY", "documentary · causal question open", PINK),
    ("04", "ECIS", "PRIVATE R&D SYSTEM · ACCESS RESTRICTED", ICE),
    ("05", "GEN_ALPHA.dat", "ongoing research", GREEN),
    ("06", "AUTONOMOUS SYSTEMS SECURITY", "discovery / adversarial review",
     BLUE),
]


def research_index():
    row_h = 74
    top = 116
    h = top + row_h * len(INDEX_ROWS) + 40
    b = [rect(0, 0, W, h, fill="url(#grid)")]
    b.append(t(56, 56, "RESEARCH INDEX", 34, WHITE, "bold", spacing=2))
    b.append(t(56, 88, "research files · public node", 22, ICE))
    b.append(t(W - 24, 56, "06", 34, BLUE, "bold", anchor="end"))
    b.append(line(24, 24, 24, h - 24, stroke=BLUE, sw=2, opacity=0.8))
    for i, (num, name, status, color) in enumerate(INDEX_ROWS):
        y = top + i * row_h
        b.append(line(56, y, W - 24, y, stroke=LINE, sw=1))
        b.append(rect(19, y + 30, 10, 10, fill=VOID, stroke=color, sw=2))
        b.append(line(29, y + 35, 50, y + 35, stroke=color, sw=1.2,
                      opacity=0.7))
        b.append(t(56, y + 43, num, 24, GREEN, "bold"))
        b.append(t(104, y + 33, name, 26, WHITE, "bold"))
        b.append(t(104, y + 61, status, 22, ICE))
        if name == "ECIS":
            b.append(lock(W - 52, y + 34, 0.55, ICE))
        else:
            b.append(f'<path d="M{W - 64} {y + 26}h16l8 8v18h-24z" '
                     f'stroke="{color}" stroke-width="1.6"/>')
    y = top + row_h * len(INDEX_ROWS)
    b.append(line(56, y, W - 24, y, stroke=LINE, sw=1))
    b.append(corners(8, 8, W - 16, h - 16, LINE, 14, 1.5))
    write("research-index.svg", svg(h, "\n".join(b)))


def debtwatch():
    h = 668
    x0, w0 = 16, W - 32
    b = [window(x0, 16, w0, h - 32, BLUE, "debtwatch :: credit console",
                "2026-10-02")]
    b.append(t(40, 106, "DEBTWATCH", 48, WHITE, "bold", spacing=3))
    b.append(t(40, 142, "CREDIT TRANSMISSION CONSOLE", 22, BLUE, spacing=1))
    b.append(t(40, 186, "When does expensive credit", 26, PINK))
    b.append(t(40, 218, "become unavailable credit?", 26, PINK))

    # transmission path: macro -> pricing -> refinancing -> company
    y = 252
    nodes = [("MACRO", 112), ("PRICING", 138), ("REFINANCING", 186),
             ("COMPANY", 138)]
    gap = 22
    total = sum(wd for _, wd in nodes) + gap * 3
    b.append(line(40, y + 28, 40 + total, y + 28, stroke=BLUE, sw=1.4,
                  dash="4 6", opacity=0.8))
    nx = 40
    for i, (n, bw) in enumerate(nodes):
        b.append(rect(nx, y, bw, 56, fill=RAISED, stroke=BLUE, sw=1.4))
        b.append(t(nx + bw / 2, y + 36, n, 22, WHITE, "bold",
                   anchor="middle"))
        if i < 3:
            ax = nx + bw + 5
            b.append(f'<path d="M{ax} {y + 22}l12 6-12 6z" fill="{BLUE}"/>')
        nx += bw + gap
    b.append(t(40, y + 90, "conceptual path · not automatic", 22, ICE))

    # three different observations, kept apart
    bands = [("PRICE", "what borrowing costs"),
             ("TERMS", "security · restrictions"),
             ("ACCESS", "can it be obtained?")]
    by = 380
    for i, (k, v) in enumerate(bands):
        yy = by + i * 60
        b.append(rect(40, yy, w0 - 48, 48, fill=PANEL, stroke=LINE, sw=1))
        b.append(rect(40, yy, 124, 48, fill=RAISED))
        b.append(rect(40, yy, 4, 48, fill=GREEN))
        b.append(t(58, yy + 32, k, 23, GREEN, "bold", spacing=1))
        b.append(t(182, yy + 32, v, 23, WHITE))
        for j in range(5):
            b.append(rect(W - 64 - j * 12, yy + 15, 6, 18, fill=BLUE,
                          opacity=round(0.2 + 0.12 * (4 - j), 2)))
    b.append(line(40, h - 98, W - 40, h - 98, stroke=LINE))
    b.append(t(40, h - 60, "> result may be:", 24, ICE))
    b.append(t(300, h - 60, "NOT YET", 24, GREEN, "bold", spacing=2))
    b.append(t(40, h - 30, "not a crash predictor", 22, ICE))
    write("section-debtwatch.svg", svg(h, "\n".join(b)))


def ai_bubblewatch():
    h = 720
    b = [rect(0, 0, W, h, fill="url(#grid)")]
    b.append(window(16, 16, W - 32, h - 32, PINK,
                    "ai-bubblewatch :: observatory", "2026-09-21",
                    fill=PANEL))
    b.append(t(40, 106, "AI BUBBLEWATCH", 46, WHITE, "bold", spacing=2))
    b.append(t(W - 44, 140, "?", 88, PINK, "bold", anchor="end",
               extra=' filter="url(#glow)"'))
    b.append(t(40, 142, "AI CAPITAL OBSERVATORY", 22, BLUE, spacing=1))
    b.append(t(40, 182, "the name is a question,", 25, PINK))
    b.append(t(40, 212, "not a verdict", 25, PINK))

    quads = [("INVESTMENT", "built, paid,", "committed?"),
             ("UTILIZATION", "used by whom,", "on what terms?"),
             ("RETURNS", "cash left after", "all costs?"),
             ("FINANCING", "who supplies it,", "who bears risk?")]
    qx, qy, qw, qh, g = 40, 236, 310, 164, 20
    for i, (k, l1, l2) in enumerate(quads):
        cx = qx + (i % 2) * (qw + g)
        cy = qy + (i // 2) * (qh + g)
        b.append(rect(cx, cy, qw, qh, fill=RAISED, stroke=BLUE, sw=1.3))
        b.append(corners(cx + 6, cy + 6, qw - 12, qh - 12, BLUE, 10, 1.4))
        b.append(t(cx + 20, cy + 42, f"0{i + 1}", 22, GREEN, "bold"))
        b.append(t(cx + 20, cy + 78, k, 25, WHITE, "bold", spacing=1))
        b.append(t(cx + 20, cy + 112, l1, 22, ICE))
        b.append(t(cx + 20, cy + 140, l2, 22, ICE))
    # obligations sits in the middle, touching all four fields
    mx, my = qx + qw + g / 2, qy + qh + g / 2
    b.append(f'<path d="M{mx} {my - 44}L{mx + 88} {my}L{mx} {my + 44}'
             f'L{mx - 88} {my}Z" fill="{VOID}" stroke="{PINK}" '
             f'stroke-width="1.8"/>')
    b.append(t(mx, my + 6, "OBLIGATIONS", 18, PINK, "bold", anchor="middle"))

    y = qy + 2 * qh + g + 44
    b.append(t(40, y, "16 deliberately selected entities", 22, WHITE))
    b.append(t(40, y + 30, "not a representative sample", 22, ICE))
    tg, tw = tag(40, y + 48, "NO BUBBLE VERDICT", GREEN, 22, 10, 34)
    b.append(tg)
    write("section-ai-bubblewatch.svg", svg(h, "\n".join(b)))


def culture():
    h = 820
    b = []
    # dossier folder with a pink tab
    b.append(f'<path d="M16 66H330L358 36H16Z" fill="{RAISED}" '
             f'stroke="{PINK}" stroke-width="1.6"/>')
    b.append(t(34, 59, "CULTURE / LEGITIMACY", 22, PINK, "bold"))
    b.append(rect(16, 66, W - 32, h - 82, fill=PANEL, stroke=PINK, sw=1.6))
    b.append(rect(16, 66, W - 32, h - 82, fill="url(#scan)"))
    b.append(t(40, 124, "CULTURAL SIGNAL DOSSIER", 22, BLUE, spacing=1))
    b.append(t(40, 174, "Tastewashing →", 36, WHITE, "bold"))
    b.append(t(40, 218, "Cultural Legitimacy", 36, WHITE, "bold"))
    b.append(t(40, 262, "Embedding", 36, WHITE, "bold"))
    b.append(t(40, 298, "(working title)", 24, ICE))

    x = 40
    for s in ("DOCUMENTARY", "PRE-EXPERIMENTAL"):
        tg, tw = tag(x, 322, s, GREEN, 20, 9, 34)
        b.append(tg)
        x += tw + 12
    tg, tw = tag(40, 366, "CAUSAL QUESTION OPEN", PINK, 20, 9, 34)
    b.append(tg)

    cards = [("01", "PRODUCTION", "what companies make", BLUE),
             ("02", "RECEPTION", "how people read it", BLUE),
             ("03", "CAUSAL QUESTION", "does affinity change", PINK)]
    extra = {"03": "legitimacy?"}
    cy = 424
    for i, (n, k, l1, c) in enumerate(cards):
        y = cy + i * 98
        x = 40 + i * 8
        b.append(rect(x, y, W - 96 - i * 8, 86, fill=RAISED, stroke=c,
                      sw=1.3))
        b.append(rect(x, y, 6, 86, fill=c))
        b.append(t(x + 24, y + 34, n, 22, GREEN, "bold"))
        b.append(t(x + 72, y + 34, k, 24, WHITE, "bold", spacing=1))
        b.append(t(x + 72, y + 66, l1 + (" " + extra[n] if n in extra
                                          else ""), 22, ICE))
        b.append(rect(W - 40, y + 22, 24, 42, fill=c, opacity=0.85))
        b.append(t(W - 28, y + 50, n[1], 20, VOID, "bold", anchor="middle"))
    b.append(line(40, h - 106, W - 56, h - 106, stroke=LINE))
    b.append(t(40, h - 70, "reports · ES · 10 + 13 pages", 22, WHITE))
    b.append(t(40, h - 38, "research cutoff 2026-08-12", 22, ICE))
    write("section-culture.svg", svg(h, "\n".join(b)))


def restricted_panel():
    # Only the approved public words appear in this asset.
    h = 380
    b = [rect(24, 24, W - 48, h - 48, fill=PANEL, stroke=LINE, sw=1.5),
         rect(36, 36, W - 72, h - 72, stroke=LINE, sw=1, opacity=0.6),
         corners(24, 24, W - 48, h - 48, ICE, 22, 2.5)]
    b.append(lock(120, 176, 1.5, ICE))
    b.append(t(212, 140, "ECIS", 68, WHITE, "bold", spacing=10))
    b.append(t(214, 178, "PRIVATE R&D SYSTEM", 24, ICE, spacing=2))
    b.append(line(214, 202, W - 72, 202, stroke=LINE, sw=1))
    rows = [("STATUS", "ACTIVE", GREEN), ("ACCESS", "RESTRICTED", PINK),
            ("DETAILS", "UNDISCLOSED", ICE)]
    for i, (k, v, c) in enumerate(rows):
        y = 242 + i * 38
        b.append(t(214, y, k, 24, ICE))
        b.append(t(370, y, v, 24, c, "bold", spacing=1))
    write("restricted-panel.svg", svg(h, "\n".join(b)))


def mind_cache():
    h = 262
    b = [window(16, 16, W - 32, h - 32, GREEN, "mind.cache", "05 entries",
                fill=PANEL)]
    b.append(line(84, 56, 84, h - 26, stroke=PINK, sw=1, opacity=0.6))
    for i in range(5):
        y = 86 + i * 32
        b.append(t(40, y + 6, f"0{i + 1}", 20, ICE))
    b.append(t(104, 116, "MIND CACHE", 48, WHITE, "bold", spacing=3))
    b.append(t(104, 158, "[ questions still open ]", 24, GREEN))
    b.append(t(104, 204, "> fragments, not answers", 24, ICE))
    b.append(rect(476, 185, 13, 24, fill=PINK))
    write("mind-cache.svg", svg(h, "\n".join(b)))


def gen_alpha():
    h = 724
    b = [window(16, 16, W - 32, h - 32, GREEN, "GEN_ALPHA.dat",
                "research note")]
    b.append(t(40, 106, "GEN_ALPHA.dat", 46, WHITE, "bold", spacing=2))
    b.append(t(40, 142, "COHORT / COGNITION ARCHIVE", 22, GREEN, spacing=1))
    b.append(t(40, 182, "what changes between generations,", 24, PINK))
    b.append(t(40, 212, "and what changes in the comparison?", 24, PINK))
    rows = [("EDUCATION ≠ COGNITION", "a test is not general ability"),
            ("POPULATION · AGE · TASK", "which group, measure, when?"),
            ("SCHOOL CONDITIONS", "instruction · attendance"),
            ("SCREENS / FEEDS / AI", "separate causal evidence"),
            ("THE OBSERVER", "memory flatters the past")]
    y0 = 240
    for i, (k, v) in enumerate(rows):
        y = y0 + i * 74
        b.append(rect(40, y, W - 80, 64, fill=RAISED if i % 2 == 0 else PANEL,
                      stroke=LINE, sw=1))
        b.append(t(54, y + 27, f"0x0{i + 1}", 20, GREEN))
        b.append(t(136, y + 27, k, 23, WHITE, "bold"))
        b.append(t(136, y + 54, v, 22, ICE))
    y = y0 + 5 * 74 + 20
    tg, tw = tag(40, y, "CAUSALITY UNRESOLVED", PINK, 22, 10, 34)
    b.append(tg)
    b.append(t(40, y + 70, "snapshot 2026-08-16", 22, ICE))
    write("section-gen-alpha.svg", svg(h, "\n".join(b)))


def security():
    h = 384
    b = [window(16, 16, W - 32, h - 32, BLUE, "adversarial-review",
                fill=VOID)]
    tg, tw = tag(W - 48 - 138, 62, "DISCOVERY", GREEN, 22, 10, 34)
    b.append(tg)
    b.append(t(40, 88, "AUTONOMOUS SYSTEMS", 32, WHITE, "bold", spacing=1))
    b.append(t(40, 124, "SECURITY", 32, WHITE, "bold", spacing=1))
    b.append(t(40, 172, "> compare · falsify · review", 25, PINK))
    rows = [("validated primitive", "none"), ("product", "none"),
            ("startup thesis", "none")]
    for i, (k, v) in enumerate(rows):
        y = 218 + i * 36
        dots = "." * (24 - len(k))
        b.append(t(40, y, f"{k} {dots}", 23, ICE))
        b.append(t(430, y, v, 23, WHITE, "bold"))
    b.append(t(40, h - 38, "research before claims", 23, BLUE))
    write("section-security.svg", svg(h, "\n".join(b)))


def market_frequencies():
    h = 436
    b = [rect(0, 0, W, h, fill="url(#grid)")]
    b.append(t(32, 62, "MARKET FREQUENCIES", 38, WHITE, "bold", spacing=2))
    b.append(t(32, 96, "interests and questions · no prices", 22, ICE))
    # three decorative waves, deliberately not data-shaped
    for k, (c, amp, per) in enumerate(((PINK, 14, 90), (BLUE, 10, 60),
                                       (GREEN, 6, 140))):
        pts = []
        for xi in range(0, W + 1, 6):
            yv = 146 + amp * math.sin(xi / per * 2 * math.pi + k)
            pts.append(f"{xi},{yv:.1f}")
        b.append(f'<polyline points="{" ".join(pts)}" stroke="{c}" '
                 f'stroke-width="1.6" opacity="0.75"/>')
    bands = [("CH-A", "BITCOIN · SOLANA · MEMECOINS", PINK),
             ("CH-B", "EQUITIES · BANKS · SOFTWARE", BLUE),
             ("CH-C", "AI · DEFENSE-TECH · FINANCING", BLUE),
             ("CH-D", "CREDIT · LIQUIDITY · STRUCTURE", GREEN),
             ("CH-E", "NARRATIVE ↔ PRICE", PINK)]
    for i, (ch, lab, c) in enumerate(bands):
        y = 200 + i * 40
        b.append(rect(32, y - 24, 70, 32, fill=VOID, stroke=c, sw=1.2))
        b.append(t(67, y - 1, ch, 19, c, "bold", anchor="middle"))
        b.append(t(118, y, lab, 23, WHITE))
    b.append(t(32, h - 18, "no wallets · no positions · not advice", 22,
               ICE))
    write("market-frequencies.svg", svg(h, "\n".join(b)))


def library():
    h = 500
    rnd = random.Random(11)
    b = [t(32, 58, "LIBRARY // CULTURE NODE", 34, WHITE, "bold", spacing=1),
         t(32, 92, "an orbit of works, not a reading log", 22, ICE)]
    spines = ["DUNE", "LEVIATHAN", "1984", "FAHRENHEIT 451",
              "BRAVE NEW WORLD", "THE ROAD", "CADÁVER EXQUISITO", "MONSTER",
              "EDGERUNNERS", "ANGEL BEATS!", "CHARLOTTE", "NORSE MYTHS"]
    colors = [PINK, BLUE, GREEN, ICE]
    shelf = h - 56
    x = 32
    sw = 50
    for i, s in enumerate(spines):
        ht = max(len(s) * 13.6 + 52, rnd.randint(200, 300))
        ht = min(ht, shelf - 116)
        c = colors[i % 4] if i < 7 else (PINK if i % 2 else BLUE)
        b.append(rect(x, shelf - ht, sw - 6, ht, fill=RAISED, stroke=c,
                      sw=1.3))
        b.append(line(x + 4, shelf - ht + 12, x + sw - 10, shelf - ht + 12,
                      stroke=c, sw=1, opacity=0.7))
        b.append(line(x + 4, shelf - 14, x + sw - 10, shelf - 14,
                      stroke=c, sw=1, opacity=0.7))
        cx, cy = x + (sw - 6) / 2 + 8, shelf - 24
        b.append(f'<text x="{cx}" y="{cy}" font-size="21" fill="{WHITE}" '
                 f'font-weight="bold" transform="rotate(-90 {cx} {cy})">'
                 f'{escape(s)}</text>')
        x += sw + (14 if i == 6 else 4)
    b.append(rect(20, shelf, W - 40, 6, fill=LINE))
    b.append(line(20, shelf + 6, W - 20, shelf + 6, stroke=PINK, sw=1,
                  opacity=0.6))
    b.append(t(32, h - 18, "books", 22, ICE))
    b.append(t(420, h - 18, "fiction · myth", 22, ICE))
    write("library-node.svg", svg(h, "\n".join(b)))


def environment():
    h = 460
    b = [t(32, 58, "OPERATOR ENVIRONMENT", 34, WHITE, "bold", spacing=1),
         t(32, 92, "grouped by use · no mastery bars", 22, ICE)]
    groups = [("BUILD & ITERATE", ["Claude Code · Git", "VS Code · Python"],
               PINK),
              ("RESEARCH & COMPARE", ["ChatGPT", "source reading"], BLUE),
              ("MARKET SCREENS", ["TradingView", "Reuters · CoinGlass"],
               BLUE),
              ("CRYPTO TOOLS", ["Axiom", "Phantom"], GREEN)]
    gw, gh, g = 318, 150, 20
    for i, (k, rows, c) in enumerate(groups):
        x = 32 + (i % 2) * (gw + g)
        y = 120 + (i // 2) * (gh + g)
        b.append(rect(x, y, gw, gh, fill=PANEL, stroke=c, sw=1.3))
        b.append(rect(x, y, gw, 38, fill=RAISED))
        b.append(line(x, y + 38, x + gw, y + 38, stroke=c, sw=1))
        b.append(t(x + 14, y + 27, "> " + k, 21, c, "bold"))
        for j, r in enumerate(rows):
            b.append(t(x + 14, y + 80 + j * 36, r, 24, WHITE))
    write("operator-environment.svg", svg(h, "\n".join(b)))


def side_frequencies():
    h = 240
    rnd = random.Random(3)
    b = []
    # blocky terrain, an original pixel motif
    size = 16
    heights = []
    hv = 5
    for i in range(W // size + 1):
        hv = max(3, min(8, hv + rnd.choice([-1, 0, 0, 1])))
        heights.append(hv)
    for i, hv in enumerate(heights):
        for j in range(hv):
            y = h - (j + 1) * size
            top = j == hv - 1
            c = GREEN if top else (RAISED if j < hv - 2 else PANEL)
            op = 0.85 if top else 1
            b.append(rect(i * size, y, size - 1, size - 1, fill=c,
                          opacity=op))
            if not top and rnd.random() < 0.06:
                b.append(rect(i * size + 5, y + 5, 5, 5,
                              fill=rnd.choice([PINK, BLUE])))
    b.append(rect(24, 20, 500, 124, fill=VOID, stroke=PINK, sw=1.4))
    b.append(t(44, 64, "SIDE FREQUENCIES", 32, PINK, "bold", spacing=2))
    b.append(t(44, 100, "minecraft · terraria · weird", 23, WHITE))
    b.append(t(44, 128, "corners of the internet", 23, WHITE))
    write("side-frequencies.svg", svg(h, "\n".join(b)))


def divider():
    h = 44
    b = [line(0, 22, W, 22, stroke=BLUE, sw=1.2, opacity=0.5),
         rect(0, 21, 240, 2, fill="url(#fadeR)")]
    for x in (120, 360, 600):
        b.append(rect(x - 6, 16, 12, 12, fill=VOID, stroke=BLUE, sw=1.6))
    b.append(rect(354, 16, 12, 12, fill=PINK))
    for i in range(6):
        b.append(rect(560 + i * 6, 30, 3, 6, fill=ICE, opacity=0.5))
    write("divider.svg", svg(h, "\n".join(b), bg=False))


def footer():
    h = 270
    rnd = random.Random(5)
    b = []
    # low skyline reprise
    x = 0
    while x < W:
        bw = rnd.choice([30, 40, 52])
        bh = rnd.randint(20, 64)
        b.append(rect(x, h - bh, bw - 3, bh, fill="#0B1220", stroke=LINE,
                      sw=1))
        x += bw
    b.append(rect(0, h - 2, W, 2, fill="url(#fadeP)"))
    # fading signal bars
    for i in range(36):
        hh = 4 + abs(math.sin(i * 0.55)) * 26 * (1 - i / 40)
        b.append(rect(32 + i * 18, 60 - hh / 2, 8, round(hh, 1), fill=PINK,
                      opacity=round(max(0.08, 0.9 - i * 0.025), 2)))
    b.append(t(W / 2, 124, "session closed.", 28, WHITE, anchor="middle"))
    b.append(t(W / 2, 158, "questions still open.", 28, WHITE,
               anchor="middle"))
    b.append(t(W / 2, 194, "snowyarch // ZÜRICH NODE", 22, PINK, "bold",
               anchor="middle", spacing=1))
    write("footer-signal.svg", svg(h, "\n".join(b)))


def main():
    OUT.mkdir(exist_ok=True)
    for fn in (header, operator_note, research_index, debtwatch,
               ai_bubblewatch, culture, restricted_panel, mind_cache,
               gen_alpha, security, market_frequencies, library,
               environment, side_frequencies, divider, footer):
        fn()
    for p in sorted(OUT.glob("*.svg")):
        print(f"{p.name:32} {p.stat().st_size:>7} bytes")


if __name__ == "__main__":
    main()
