"""Generate the SVG assets for the snowyarch profile README.

Run from the repository root:

    python3 scripts/build_assets.py

Every section is a framed terminal scene built like the header: a
typed command, an ASCII emblem beside a neofetch-style info column,
decorated sub-sections and a closing prompt with rotating lines. The
README keeps a collapsed plain-text copy of each module for reading
without images. The restricted panel is static and carries only its
approved lines.

Every asset is hand-built SVG: no scripts, no external fonts, no
embedded images, no metadata. Typing effects use SMIL, and every
animation only hides things for a while, so a renderer that ignores
animation still shows the finished terminal. All visible text is
written literally in this file.
"""

import math
import textwrap
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
<filter id="soft" x="-10%" y="-10%" width="120%" height="120%">
<feGaussianBlur stdDeviation="4"/>
</filter>
<radialGradient id="vig" cx="0.5" cy="0.45" r="0.75">
<stop offset="0.6" stop-color="{VOID}" stop-opacity="0"/>
<stop offset="1" stop-color="#000000" stop-opacity="0.55"/>
</radialGradient>
<linearGradient id="sweep" x1="0" x2="0" y1="0" y2="1">
<stop offset="0" stop-color="{WHITE}" stop-opacity="0"/>
<stop offset="0.5" stop-color="{WHITE}" stop-opacity="0.045"/>
<stop offset="1" stop-color="{WHITE}" stop-opacity="0"/>
</linearGradient>
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


def window(x, y, w, h, color, title, right="", fill=PANEL, lamps=True):
    """A TUI pane: flat frame with the title cut into the top border, a
    soft neon glow behind the border and three status lamps."""
    out = [rect(x, y, w, h, fill=fill),
           rect(x, y, w, h, stroke=color, sw=3, opacity=0.35,
                extra=' filter="url(#soft)"'),
           rect(x, y, w, h, stroke=color, sw=1.4)]
    label = f"[ {title} ]"
    lw = len(label) * 20 * CW + 12
    out.append(rect(x + 16, y - 13, lw + (52 if lamps else 0), 26,
                    fill=VOID))
    out.append(t(x + 22, y + 7, label, 20, color, "bold"))
    if lamps:
        lx = x + 16 + lw + 10
        for i, (c, dur) in enumerate(((GREEN, "2.6s"), (color, "3.4s"),
                                      (LINE, None))):
            anim = (f'<animate attributeName="opacity" values="1;0.35;1" '
                    f'dur="{dur}" begin="{0.4 * i}s" '
                    f'repeatCount="indefinite"/>' if dur else "")
            out.append(f'<circle cx="{_f(lx + i * 13)}" cy="{y}" r="3.6" '
                       f'fill="{c}">{anim}</circle>')
    if right:
        rl = f"[ {right} ]"
        rw = len(rl) * 20 * CW + 12
        out.append(rect(x + w - 16 - rw, y - 13, rw, 26, fill=VOID))
        out.append(t(x + w - 22, y + 7, rl, 20, ICE, anchor="end"))
    return "\n".join(out)


def chrome(h, color, bars=True, ruler=True):
    """Atmosphere shared by every framed scene. Returns (under, over):
    `under` goes right after the frame, `over` on top of everything."""
    under = [rect(17, 17, W - 34, h - 34, fill="url(#vig)")]
    if ruler:
        for y in range(64, int(h) - 40, 24):
            major = (y - 64) % 96 == 0
            ln = 7 if major else 4
            under.append(line(18, y, 18 + ln, y, stroke=color if major
                              else LINE, sw=1, opacity=0.8))
            under.append(line(W - 18, y, W - 18 - ln, y, stroke=color
                              if major else LINE, sw=1, opacity=0.8))
    if bars:
        # a small, slow activity meter in the top-right corner
        for i, (vals, dur) in enumerate((("4;9;5;4", "2.2s"),
                                         ("7;4;10;7", "1.8s"),
                                         ("5;11;6;5", "2.6s"),
                                         ("9;5;8;9", "2.0s"),
                                         ("3;7;4;3", "2.4s"))):
            x = W - 92 + i * 7
            under.append(
                f'<rect x="{x}" y="34" width="4" height="6" fill="{color}" '
                f'opacity="0.75"><animate attributeName="height" '
                f'values="{vals}" dur="{dur}" repeatCount="indefinite"/>'
                f'</rect>')
        under.append(line(W - 94, 46, W - 56, 46, stroke=LINE, sw=1))
    cid = uid()
    over = [f'<clipPath id="{cid}"><rect x="17" y="17" width="{W - 34}" '
            f'height="{_f(h - 34)}"/></clipPath>'
            f'<g clip-path="url(#{cid})"><rect x="17" y="-120" '
            f'width="{W - 34}" height="120" fill="url(#sweep)">'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="0 0;0 {_f(h + 120)}" dur="{_f(max(7, h / 120))}s" '
            f'repeatCount="indefinite"/></rect></g>']
    return under, over


def crosshair(x, y, color=LINE, n=5):
    return (line(x - n, y, x + n, y, stroke=color, sw=1) +
            line(x, y - n, x, y + n, stroke=color, sw=1))


def glitch(x, y, s, size, weight="bold", seed=0):
    """Two offset copies of an existing heading that flash for a moment
    every few seconds. Hidden unless the animation runs."""
    out = []
    for dx, c, k in ((-2, BLUE, 0.00), (2, GREEN, 0.012)):
        a = 0.91 + k
        out.append(
            f'<text x="{_f(x + dx)}" y="{y}" font-size="{size}" fill="{c}" '
            f'font-weight="{weight}" opacity="0">{escape(s)}'
            f'<animate attributeName="opacity" '
            f'values="0;0;0.7;0;0" keyTimes="0;{a:.3f};{a + 0.008:.3f};'
            f'{a + 0.02:.3f};1" dur="{9 + seed % 4}s" '
            f'begin="{1.5 + seed % 3}s" repeatCount="indefinite"/></text>')
    return "".join(out)


def flicker(x, y, w, h, seed=0):
    """A faint dimming pass over an ASCII emblem, now and then."""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{VOID}" '
            f'opacity="0"><animate attributeName="opacity" '
            f'values="0;0;0.28;0;0.18;0;0" '
            f'keyTimes="0;0.86;0.87;0.88;0.89;0.9;1" dur="{7 + seed % 5}s" '
            f'repeatCount="indefinite"/></rect>')


def shimmer(x, y, n=9, step=22, size=16):
    """A thin outline that walks across a swatch row, then rests."""
    xs = ";".join(_f(x - 2 + i * step) for i in range(n)) + f";{_f(x - 2)}"
    kt = ";".join(_f(i / (n + 4)) for i in range(n)) + ";1"
    return (f'<rect x="{_f(x - 2)}" y="{_f(y - 2)}" width="{size + 4}" '
            f'height="{size + 4}" fill="none" stroke="{WHITE}" '
            f'stroke-width="1.2" opacity="0.7"><animate attributeName="x" '
            f'values="{xs}" keyTimes="{kt}" calcMode="discrete" dur="5s" '
            f'repeatCount="indefinite"/></rect>')


def write(name, content):
    (OUT / name).write_text(content, encoding="utf-8")


# ---------------------------------------------------------------- typing
# Typing effects use SMIL <set>/<animate>, which browsers run inside an
# <img>. Every animation only hides things for a while: a renderer that
# ignores animation still shows the finished terminal.

CW = 0.6  # monospace advance width as a fraction of the font size
_ids = [0]


def uid():
    _ids[0] += 1
    return f"k{_ids[0]}"


def _f(v):
    return f"{v:.4f}".rstrip("0").rstrip(".")


def typed(x, y, s, size, fill, start, cps=24, weight="normal",
          cursor=GREEN):
    """Text that types itself in from `start` seconds. Returns (svg, end)."""
    n = len(s)
    cw = size * CW
    full = n * cw
    dt = 1 / cps
    end = start + n * dt
    dur = end + dt
    kt = [0] + [(start + i * dt) / dur for i in range(n + 1)]
    widths = [0] + [i * cw for i in range(n + 1)]
    keys = ";".join(_f(k) for k in kt)
    cid = uid()
    out = [
        f'<clipPath id="{cid}"><rect x="{x}" y="{y - size}" '
        f'width="{_f(full)}" height="{size * 1.4}">'
        f'<animate attributeName="width" dur="{_f(dur)}s" calcMode="discrete" '
        f'keyTimes="{keys}" values="{";".join(_f(v) for v in widths)}"/>'
        f'</rect></clipPath>',
        f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" '
        f'font-weight="{weight}" textLength="{_f(full)}" '
        f'lengthAdjust="spacing" clip-path="url(#{cid})">{escape(s)}</text>',
    ]
    if cursor:
        xs = ";".join(_f(x + v) for v in widths)
        out.append(
            f'<rect x="{x}" y="{y - size * 0.8}" width="{_f(cw * 0.9)}" '
            f'height="{size}" fill="{cursor}" opacity="0">'
            f'<animate attributeName="x" dur="{_f(dur)}s" calcMode="discrete" '
            f'keyTimes="{keys}" values="{xs}"/>'
            f'<animate attributeName="opacity" dur="{_f(dur)}s" '
            f'calcMode="discrete" keyTimes="0;{_f(start / dur)}" '
            f'values="0;1"/></rect>')
    return "\n".join(out), end


def appear(fragment, at):
    """Hide a fragment until `at` seconds."""
    return (f'<g><set attributeName="opacity" to="0" begin="0s" '
            f'dur="{_f(at)}s"/>{fragment}</g>')


def blink(x, y, size, color, at, times="indefinite"):
    """Block cursor that shows up at `at` seconds and blinks."""
    return (f'<rect x="{_f(x)}" y="{_f(y - size * 0.8)}" '
            f'width="{_f(size * CW * 0.9)}" height="{size}" fill="{color}">'
            f'<set attributeName="opacity" to="0" begin="0s" dur="{_f(at)}s"/>'
            f'<animate attributeName="opacity" values="1;0" dur="1.1s" '
            f'begin="{_f(at)}s" calcMode="discrete" repeatCount="{times}"/>'
            f'</rect>')


def rotating(x, y, phrases, size, fill, start, cps=18, hold=2.6, gap=0.5):
    """Phrases that type, pause, delete and loop forever, after `start`."""
    cw = size * CW
    dt = 1 / cps
    slots, tcur = [], 0.0
    for p in phrases:
        slots.append((tcur, len(p)))
        tcur += len(p) * dt * 1.5 + hold + gap
    cycle = tcur
    tracks = []
    for s0, n in slots:
        ev = {0.0: 0.0}
        for i in range(1, n + 1):
            ev[s0 + i * dt] = i * cw
        d0 = s0 + n * dt + hold
        for i in range(1, n + 1):
            ev[d0 + i * dt * 0.5] = (n - i) * cw
        tracks.append(ev)

    def width_at(ev, tt):
        return ev[max(k for k in ev if k <= tt)]

    out = []
    for idx, ev in enumerate(tracks):
        times = sorted(ev)
        n = slots[idx][1]
        cid = uid()
        base = n * cw if idx == 0 else 0
        out.append(
            f'<clipPath id="{cid}"><rect x="{x}" y="{y - size}" '
            f'width="{_f(base)}" height="{size * 1.4}">'
            f'<animate attributeName="width" begin="{_f(start)}s" '
            f'dur="{_f(cycle)}s" repeatCount="indefinite" calcMode="discrete" '
            f'keyTimes="{";".join(_f(k / cycle) for k in times)}" '
            f'values="{";".join(_f(ev[k]) for k in times)}"/></rect>'
            f'</clipPath>'
            f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" '
            f'textLength="{_f(n * cw)}" lengthAdjust="spacing" '
            f'clip-path="url(#{cid})">{escape(phrases[idx])}</text>')
    # one cursor follows whichever phrase is on screen
    times = sorted(set(k for ev in tracks for k in ev))
    xs = [x + sum(width_at(ev, k) for ev in tracks) for k in times]
    out.append(
        f'<rect x="{_f(x + slots[0][1] * cw)}" y="{_f(y - size * 0.8)}" '
        f'width="{_f(cw * 0.9)}" height="{size}" fill="{fill}">'
        f'<animate attributeName="x" begin="{_f(start)}s" dur="{_f(cycle)}s" '
        f'repeatCount="indefinite" calcMode="discrete" '
        f'keyTimes="{";".join(_f(k / cycle) for k in times)}" '
        f'values="{";".join(_f(v) for v in xs)}"/>'
        f'<animate attributeName="opacity" values="1;1;0.25;1" '
        f'keyTimes="0;0.55;0.75;1" dur="1.3s" repeatCount="indefinite"/>'
        f'</rect>')
    return appear("\n".join(out), start)


# ---------------------------------------------------------------- assets

ASCII_CITY = r"""
  .    . .                .
  .     '    '        ooo  .
       `             o@@@o
         ^      ^     ooo
  .   ' /|\    /|\      '
    '   |#|  . |#|
        |#|   '|#| .
        |o|    |o|  .
      ` |#|    |#|
        |#|    |#|_____
        |:|====|:|| : |
________|#|####|#||:  |
|  :  :||#|####|#||  :|_____
| :  : ||:|#[]#|:|| : ||  :|
|:  :  ||#|####|#||:  || : |
|  :  :||#|####|#||  :||:  |
| :  : ||:|####|:|| : ||  :|
============================
~-~-~-~-~-~-~-~-~-~-~-~-~-~-
""".strip("\n").split("\n")


def header():
    h = 600
    under, over = chrome(h, PINK)
    b = [window(16, 16, W - 32, h - 32, PINK, "snowyarch@zurich-node: ~",
                "AFTERHOURS", fill=VOID)] + under
    # the boot command
    prompt = "snowyarch@zurich-node:~$"
    b.append(t(36, 70, prompt, 21, GREEN, "bold"))
    cmd, t0 = typed(36 + (len(prompt) + 1) * 21 * CW, 70, "neofetch", 21,
                    WHITE, 0.8, cps=12)
    b.append(cmd)
    t0 += 0.35

    # original ascii skyline: twin towers, moon, snow, river
    fs, lh = 13.5, 16.5
    rows = []
    shades = [PINK, PINK, PINK, "#E35FD6", "#C46DE0", "#A47BEA", "#857FF2",
              "#6687F8", BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE,
              BLUE, ICE, BLUE]
    for i, row in enumerate(ASCII_CITY):
        rows.append(appear(
            f'<text x="36" y="{_f(112 + i * lh)}" font-size="{fs}" '
            f'fill="{shades[i]}" xml:space="preserve">{escape(row)}</text>',
            t0 + i * 0.04))
    b += rows

    # palette swatches under the art
    pal = [VOID, PANEL, RAISED, LINE, BLUE, PINK, GREEN, ICE, WHITE]
    sw = [appear(rect(36 + i * 26, 440, 22, 22, fill=c, stroke=LINE, sw=1),
                 t0 + 0.9 + i * 0.05) for i, c in enumerate(pal)]
    b += sw
    b.append(appear(shimmer(36, 440, 9, 26, 22), t0 + 1.4))
    b.append(appear(flicker(32, 96, 246, 330, 3), t0 + 1.0))

    # neofetch-style info column
    x0 = 286
    fs2, lh2 = 19, 29
    b.append(appear(t(x0, 112, "snowyarch@zurich-node", 22, PINK, "bold"),
                    t0 + 0.1))
    b.append(appear(glitch(x0, 112, "snowyarch@zurich-node", 22, seed=1),
                    t0 + 0.1))
    b.append(crosshair(W - 40, 98))
    b.append(appear(t(x0, 134, "-" * 21, 22, LINE), t0 + 0.15))
    info = [("node", "afterhours / personal"),
            ("loc", "zürich // ch"),
            ("role", "builder · researcher"),
            ("focus", "markets · ai · philosophy"),
            ("research", "5 public · 1 restricted"),
            ("tools", "python · git · claude code"),
            ("markets", "btc · sol · credit"),
            ("library", "dune · leviathan · 1984"),
            ("side", "minecraft · terraria"),
            ("status", "still learning")]
    for i, (k, v) in enumerate(info):
        y = 168 + i * lh2
        frag = (t(x0, y, f"{k}:", fs2, BLUE, "bold") +
                t(x0 + 10 * fs2 * CW, y, v, fs2,
                  GREEN if k == "status" else WHITE))
        b.append(appear(frag, t0 + 0.25 + i * 0.09))

    # kali-style prompt with rotating thoughts
    t1 = t0 + 0.25 + len(info) * 0.09 + 0.4
    b.append(appear(line(36, 488, W - 36, 488, stroke=LINE, sw=1), t1))
    b.append(appear(
        t(36, 522, "┌──(", 21, BLUE) +
        t(36 + 4 * 21 * CW, 522, "snowyarch@zurich", 21, PINK, "bold") +
        t(36 + 20 * 21 * CW, 522, ")-[~/research]", 21, BLUE), t1))
    b.append(appear(t(36, 556, "└─$", 21, BLUE), t1))
    b.append(rotating(36 + 4 * 21 * CW, 556,
                      ["build things to understand them",
                       "why do markets believe what they believe?",
                       '"not yet" is a valid result',
                       "questions > answers"],
                      21, GREEN, t1 + 0.3))
    b += over
    write("header.svg", svg(h, "\n".join(b)))


# ---------------------------------------------------------------- modules
# Every section after the header is built like the header: a framed
# terminal scene with a typed command, an ASCII emblem beside a
# neofetch-style info column, decorated sub-sections, and a closing
# prompt that cycles through a few lines from the module itself.

FS, LH = 19, 28        # body text size and line height
X0, X1 = 36, 684       # content edges inside the frame
INFO_X = 286           # info column, same as the header


def mix(c1, c2, k):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02X%02X%02X" % tuple(round(a[j] + (b[j] - a[j]) * k)
                                   for j in range(3))


def segs(x, y, parts, size=FS):
    """A run of (text, color[, weight]) parts on monospace columns."""
    out, c = [], 0
    for p in parts:
        s, color = p[0], p[1]
        weight = p[2] if len(p) > 2 else "normal"
        if s.strip():
            out.append(t(_f(x + c * size * CW), y, s, size, color, weight,
                         extra=' xml:space="preserve"'))
        c += len(s)
    return "".join(out)


def hud(x, y, w, h, color, n=12, sw=1.4, opacity=0.8):
    """Corner brackets."""
    out = []
    for cx, cy, dx, dy in ((x, y, 1, 1), (x + w, y, -1, 1),
                           (x, y + h, 1, -1), (x + w, y + h, -1, -1)):
        out.append(f'<path d="M{cx} {cy + dy * n}V{cy}H{cx + dx * n}" '
                   f'stroke="{color}" stroke-width="{sw}" '
                   f'opacity="{opacity}"/>')
    return "".join(out)


class Module:
    def __init__(self, name, color, title, right, path, cmd):
        self.name, self.color = name, color
        self.title, self.right, self.path, self.cmd = title, right, path, cmd
        self.head = []      # emblem rows and info rows, streamed first
        self.items = []     # body fragments, streamed in order
        self.y = 0

    # --- the neofetch-style head -------------------------------------
    def neofetch(self, emblem, colors, ident, info, kcol=10):
        y0 = 116
        kcol = max(kcol, max(len(k) for k, _, _ in info) + 2)
        for i, row in enumerate(emblem):
            k = i / max(1, len(emblem) - 1)
            c = mix(colors[0], colors[1], k)
            self.head.append(
                f'<text x="{X0}" y="{_f(y0 + i * 16.5)}" font-size="13.5" '
                f'fill="{c}" xml:space="preserve">{escape(row)}</text>')
        ey = y0 + len(emblem) * 16.5 + 8
        for i in range(9):
            c = mix(colors[0], colors[1], i / 8)
            self.head.append(rect(X0 + i * 22, ey, 16, 16, fill=c,
                                  stroke=LINE, sw=1,
                                  opacity=round(0.35 + 0.07 * i, 2)))
        seed = len(self.name)
        self.head.append(flicker(X0 - 4, y0 - 14, INFO_X - X0 - 8,
                                 len(emblem) * 16.5 + 8, seed))
        self.head.append(shimmer(X0, ey))
        self.head.append(t(INFO_X, y0, ident, 22, PINK, "bold"))
        self.head.append(glitch(INFO_X, y0, ident, 22, seed=seed))
        self.head.append(t(INFO_X, y0 + 22, "-" * len(ident), 22, LINE))
        for i, (k, v, c) in enumerate(info):
            y = y0 + 56 + i * 28
            self.head.append(t(INFO_X, y, f"{k}:", FS, BLUE, "bold") +
                             t(_f(INFO_X + kcol * FS * CW), y, v, FS, c,
                               "bold" if c != WHITE else "normal"))
        iy = y0 + 56 + (len(info) - 1) * 28
        self.y = max(ey + 16, iy) + 46

    # --- body helpers ------------------------------------------------
    def section(self, label, color=None):
        c = color or self.color
        self.y += 6
        y = self.y
        lx = X0 + 20 + len(label) * FS * CW + 14
        frag = (rect(X0, y - 12, 10, 10, fill=c) +
                t(X0 + 20, y, label, FS, c, "bold") +
                line(_f(lx), y - 6, X1 - 52, y - 6, stroke=LINE, sw=1))
        for i in range(3):
            o = round(0.9 - 0.3 * i, 2)
            frag += (f'<rect x="{X1 - 44 + i * 15}" y="{y - 12}" width="10" '
                     f'height="10" fill="{c}" opacity="{o}">'
                     f'<animate attributeName="opacity" '
                     f'values="{o};0.12;{o}" dur="3.2s" begin="{0.45 * i}s" '
                     f'repeatCount="indefinite"/></rect>')
        self.items.append(frag)
        self.y += 36

    def line(self, *parts, size=FS, gap=LH, x=X0):
        self.items.append(segs(x, self.y, parts, size))
        self.y += gap

    def wrap(self, text, color=WHITE, prefix="", cont="", width=54,
             pcolor=None, size=FS):
        lines = textwrap.wrap(text, width - len(prefix))
        for i, ln in enumerate(lines):
            p = prefix if i == 0 else (cont or " " * len(prefix))
            self.line((p, pcolor or self.color, "bold"), (ln, color),
                      size=size)

    def gap(self, h=12):
        self.y += h

    def raw(self, frag, height):
        self.items.append(frag)
        self.y += height

    # --- assemble ----------------------------------------------------
    def build(self, phrases):
        y = self.y + 4
        tail = [line(X0, y, X1, y, stroke=LINE, sw=1),
                t(X0, y + 36, "┌──(", 21, BLUE) +
                t(_f(X0 + 4 * 21 * CW), y + 36, "snowyarch@zurich", 21, PINK,
                  "bold") +
                t(_f(X0 + 20 * 21 * CW), y + 36, f")-[{self.path}]", 21, BLUE),
                t(X0, y + 70, "└─$", 21, BLUE)]
        h = math.ceil(y + 70 + 40)
        under, over = chrome(h, self.color)
        out = [window(16, 16, W - 32, h - 32, self.color, self.title,
                      self.right, fill=VOID)] + under + [
               hud(26, 30, W - 52, h - 52, LINE, 10, 1.2, 0.9),
               crosshair(X1 - 4, 98), crosshair(X1 - 4, y - 14)]
        prompt = f"snowyarch@zurich:{self.path}$"
        ps = min(21, (X1 - X0) / ((len(prompt) + 1 + len(self.cmd)) * CW))
        out.append(t(X0, 70, prompt, _f(ps), GREEN, "bold"))
        cmd, t0 = typed((X0 + (len(prompt) + 1) * ps * CW), 70, self.cmd,
                        ps, WHITE, 0.6, cps=16)
        out.append(cmd)
        tt = t0 + 0.3
        for i, frag in enumerate(self.head):
            out.append(appear(frag, tt + i * 0.025))
        tt += len(self.head) * 0.025 + 0.15
        for i, frag in enumerate(self.items):
            out.append(appear(frag, tt + i * 0.04))
        tt += len(self.items) * 0.04 + 0.2
        out.append(appear("".join(tail), tt))
        out.append(rotating((X0 + 4 * 21 * CW), y + 70, phrases, 21, GREEN,
                            tt + 0.3))
        out += over
        write(self.name, svg(h, "\n".join(out)))


def kv(m, key, value, color=WHITE, w=12, size=FS, gap=LH):
    """A terse interface field: KEY padded, then its value."""
    m.line((f"{key:<{w}}", BLUE, "bold"), (value, color), size=size, gap=gap)


EMBLEMS = {
    "index": r"""
        .--------.
        | zh-01  |
        '---++---'
            ||
   .--------++--------.
   |        ||        |
 [01]  [02] || [03]  [04]
   |        ||        |
 [05]------[##]------[06]
            ||
         ~~~~~~~~
""",
    "operator": r"""
           .   *   .
        \   \  |  /   /
         \   \ | /   /
     ---- \___\|/___/ ----
   ------ ==== * ==== ------
     ---- /```/|\```\ ----
         /   / | \   \
        /   /  |  \   \
           '   *   '
""",
    "debtwatch": r"""
          _________
    _____/ CREDIT  \_____
   /_____________________\
     ||   ||   ||   ||
     ||   ||   ||   ||
     ||   ||   ||   ||
     ||   ||   ||   ||
     ||   ||   ||   ||
   __||___||___||___||__
  |_____________________|
  =======================
""",
    "ai": r"""
           .    *    .
        .-~~~~~~~~~~~-.
      .'   o     .     '.
     /   .    ( ? )   o   \
    |  o    O       .      |
    |     .     o      O   |
     \   O   .     o     /
      '.     o   .     .'
        '-.__________.-'
            |      |
         ___|______|___
""",
    "culture": r"""
   .---------------------.
   | .-----------------. |
   | |  PRODUCTION     | |
   | '-------o---------' |
   | .-----------------. |
   | |  RECEPTION      | |
   | '-------o---------' |
   | .-----------------. |
   | |  CAUSAL   ?     | |
   | '-------o---------' |
   '---------------------'
      ||             ||
""",
    "lock": r"""
        .---------.
       /  .-----.  \
       | |       | |
       | |       | |
    .--'-'-------'-'--.
    |                 |
    |      .---.      |
    |      |   |      |
    |      '-.-'      |
    |        |        |
    '-----------------'
""",
    "mind": r"""
      _|_|_|_|_|_|_|_|_
     |                 |
   --|   M I N D       |--
   --|      . C A C H E|--
   --|                 |--
   --|   ?  ?  ?  ?  ? |--
     |_________________|
       | | | | | | | |
""",
    "gen": r"""
      .-~~~~~~~~~~~~-.
     (   GEN_ALPHA    )
     |'-~~~~~~~~~~~~-'|
     |  edu ≠ cog     |
     |'-~~~~~~~~~~~~-'|
     |  cohort · age  |
     |'-~~~~~~~~~~~~-'|
     |  observer  ?   |
     |'-~~~~~~~~~~~~-'|
      '-~~~~~~~~~~~~-'
""",
    "shield": r"""
     .---------------.
     |  .---------.  |
     |  |    ?    |  |
     |  '---------'  |
     |   . . . . .   |
      \             /
       \   -----   /
        \         /
         '.     .'
           '---'
""",
    "antenna": r"""
            |
           /|\        )))
          / | \      ))
         /  |  \    )
        /---+---\
       /    |    \
      /     |     \
     /------+------\
    /       |       \
   '========'========'
""",
    "library": r"""
  .--.---.--.----.---.--.
  |D |   |19|    |   |  |
  |U |LEV|84|FAHR|BNW|TR|
  |N |   |  |451 |   |  |
  |E |   |  |    |   |  |
  |__|___|__|____|___|__|
  .---.---.---.----.--.
  |MON|EDG|ANG|CHAR|NO|
  |   |   |BTS|    |RS|
  |___|___|___|____|__|
  =======================
""",
    "env": r"""
    .--------------------.
    | $ claude           |
    | $ git status       |
    | $ python3 _        |
    |                    |
    '---------.----------'
        ______|______
       /=============\
      /_______________\
""",
    "side": r"""
           ###
          #####
         #######
           |||        .-.
     ______|||_______(   )
    |##|##|##|##|##|##|##|
    |__|__|__|__|__|__|__|
""",
}


def emblem(key):
    return EMBLEMS[key].strip("\n").split("\n")


# ---------------------------------------------------------------- content
# Module text is taken from the approved public notes in public/.

def mod_index():
    m = Module("mod-index.svg", BLUE, "research.index", "06 modules",
               "~/research", "tree -L 1")
    m.neofetch(emblem("index"), (BLUE, PINK), "research@zurich-node",
               [("modules", "6", WHITE), ("public", "5", WHITE),
                ("restricted", "1", PINK), ("dates", "research cutoffs", WHITE),
                ("status", "open", GREEN)],
               kcol=11)
    m.section("~/research")
    rows = [("├──", "01", "debtwatch/", "credit-console", BLUE),
            ("├──", "02", "ai-bubblewatch/", "observatory", PINK),
            ("├──", "03", "culture-legitimacy/", "dossier", PINK),
            ("├──", "04", "ECIS", "RESTRICTED", ICE),
            ("├──", "05", "GEN_ALPHA.dat", "cohort archive", GREEN),
            ("└──", "06", "autonomous-security/", "review", BLUE)]
    for pre, n, name, tag, c in rows:
        m.line((pre + " ", LINE), (n + "  ", GREEN, "bold"),
               (f"{name:<22}", WHITE if name == "ECIS" else c, "bold"),
               (tag, PINK if name == "ECIS" else ICE), size=20, gap=32)
    m.gap(6)
    m.build(["cd debtwatch", "cd ai-bubblewatch", "cat GEN_ALPHA.dat",
             "tail mind.cache"])


def mod_operator():
    m = Module("mod-operator.svg", PINK, "operator.note", "tty1", "~",
               "cat operator.note")
    m.neofetch(emblem("operator"), (ICE, PINK), "operator@zurich-node",
               [("handle", "snowyarch", WHITE),
                ("is", "builder", WHITE), ("is", "researcher", WHITE),
                ("is", "markets obsessive", WHITE),
                ("is", "philosophy nerd", WHITE),
                ("is", "systems explorer", WHITE),
                ("is", "internet-native learner", WHITE),
                ("status", "still learning", GREEN)], kcol=8)
    m.section("operator.note")
    m.line(("> ", PINK, "bold"), ("I build things to understand them.", PINK,
                                  "bold"), size=21, gap=34)
    m.wrap("Most of my questions start somewhere between markets, "
           "companies, AI and philosophy, then refuse to stay in one "
           "category.", prefix="  ")
    m.gap()
    m.wrap("I'm interested in how money moves, how companies acquire "
           "power, how technology becomes culture, and what would make a "
           "convincing explanation fall apart.", prefix="  ")
    m.wrap("Sometimes that turns into code. Sometimes it becomes a "
           "research dossier with more unanswered questions than I started "
           "with.", color=ICE, prefix="  ")
    m.gap()
    m.section("environment")
    m.wrap("My working environment is mostly terminals, agents, source "
           "material and repeated revisions. I'm still learning the "
           "technical side as I go.", prefix="  ")
    m.wrap("This node collects the projects, ideas and strange corners of "
           "the internet that keep me coming back.", color=ICE, prefix="  ")
    m.build(["build things to understand them",
             "what would make it fall apart?", "still learning"])


def mod_debtwatch():
    m = Module("mod-debtwatch.svg", BLUE, "debtwatch :: credit-console",
               "01", "~/research/debtwatch", "cat brief.md")
    m.neofetch(emblem("debtwatch"), (BLUE, GREEN), "debtwatch@credit",
               [("type", "research · monitoring", WHITE),
                ("snapshot", "2026-10-02", WHITE),
                ("evidence", "to 2026-10-01", WHITE),
                ("edition", "2026-10-03", WHITE),
                ("mode", "historical", WHITE),
                ("forecast", "none", GREEN),
                ("result", "NOT YET", GREEN)])
    m.section("query")
    m.line(("Q  ", BLUE, "bold"), ("when does expensive credit", PINK, "bold"),
           size=22, gap=32)
    m.line(("   ", BLUE), ("become unavailable credit?", PINK, "bold"),
           size=22, gap=38)

    m.section("transmission :: conceptual")
    m.line(("[ ", BLUE), ("MACRO", WHITE, "bold"), (" ]", BLUE),
           (" → ", PINK, "bold"), ("[ ", BLUE), ("RATES", WHITE, "bold"),
           (" ]", BLUE), (" → ", PINK, "bold"), ("[ ", BLUE),
           ("CREDIT PRICING", WHITE, "bold"), (" ]", BLUE), size=19, gap=34)
    m.line(("  ↳ ", PINK, "bold"), ("[ ", BLUE), ("REFINANCING", WHITE, "bold"),
           (" ]", BLUE), (" → ", PINK, "bold"), ("[ ", BLUE),
           ("COMPANY CASH FLOWS", WHITE, "bold"), (" ]", BLUE), size=19,
           gap=36)
    kv(m, "PATH", "conditional", GREEN)
    kv(m, "DEPENDS ON", "maturities · fixed / floating rates", ICE)
    kv(m, "", "collateral · lender appetite", ICE)
    kv(m, "", "operating performance", ICE, gap=34)

    m.section("watchlist :: price / terms / access", GREEN)
    top = m.y
    m.raw(rect(X0, m.y - 21, X1 - X0, 30, fill=PANEL) +
          t(X0 + 14, m.y, "LAYER", 16, ICE, "bold") +
          t(X0 + 130, m.y, "WHAT IT OBSERVES", 16, ICE, "bold") +
          t(X0 + 424, m.y, "AT SNAPSHOT", 16, ICE, "bold"), 40)
    rows = [("PRICE", ["cost of borrowing"], "●", "more evident", GREEN),
            ("TERMS", ["more security,", "tighter restrictions"], "◐",
             "selective", BLUE),
            ("ACCESS", ["can it be obtained?"], "○", "not established", PINK)]
    for k, obs, mark, st, c in rows:
        y = m.y
        hgt = 26 * len(obs) + 16
        frag = rect(X0, y - 20, 4, hgt - 8, fill=c)
        frag += t(X0 + 14, y, k, 20, c, "bold")
        for i, o in enumerate(obs):
            frag += t(X0 + 130, y + i * 26, o, FS, WHITE)
        frag += t(X0 + 424, y, f"{mark} {st}", FS, WHITE, "bold")
        frag += line(X0, y + hgt - 24, X1, y + hgt - 24, stroke=LINE,
                     dash="3 5")
        m.raw(frag, hgt)
    m.items.append(hud(X0 - 8, top - 32, X1 - X0 + 16, m.y - top + 16,
                       GREEN, 10, 1.4, 0.9))
    m.gap(16)

    m.section("snapshot.log :: 2026-10-02")
    m.line(("+ ", GREEN, "bold"), ("pricing   ", BLUE, "bold"),
           ("pressure more evident", GREEN))
    m.line(("+ ", GREEN, "bold"), ("terms     ", BLUE, "bold"),
           ("selective deterioration", GREEN))
    m.line(("− ", PINK, "bold"), ("access    ", BLUE, "bold"),
           ("broad failure not established", PINK), gap=36)

    m.section("counterevidence :: limits")
    kv(m, "COUNTER", "successful refinancings kept on record", w=10)
    kv(m, "PANEL", "selected after cases of interest", w=10)
    kv(m, "LIMIT", "no market-wide prevalence estimate", PINK, w=10)
    kv(m, "SCOPE", "historical snapshot · 2026-10-02", w=10, gap=36)

    m.section("result", GREEN)
    m.line(("NOT YET", GREEN, "bold"), size=34, gap=40)
    kv(m, "THRESHOLD", "stronger conclusion: not crossed", w=11)
    kv(m, "RISK", "open · not ruled out", PINK, w=11)
    kv(m, "MODE", "research / monitoring · forecast none", ICE, w=11, gap=30)
    m.build(["price ≠ terms ≠ access", '"not yet" is a valid result',
             "forecast: none"])


def mod_ai():
    m = Module("mod-ai-bubblewatch.svg", PINK, "ai-bubblewatch :: observatory",
               "02", "~/…/ai-bubblewatch", "cat brief.md")
    m.neofetch(emblem("ai"), (PINK, BLUE), "bubblewatch@observatory",
               [("type", "ai economics research", WHITE),
                ("cutoff", "2026-09-21", WHITE),
                ("edition", "2026-10-03", WHITE),
                ("hypothesis", "unresolved", PINK),
                ("sample", "16 selected entities", WHITE),
                ("scope", "non-representative", WHITE),
                ("verdict", "none", GREEN)], kcol=11)
    m.section("query")
    m.line(("Q  ", PINK, "bold"), ("what would distinguish durable", PINK,
                                   "bold"), size=22, gap=32)
    m.line(("   ", PINK), ("investment from an unsustainable", PINK, "bold"),
           size=22, gap=32)
    m.line(("   ", PINK), ("buildout?", PINK, "bold"), size=22, gap=36)
    kv(m, "NAME", "question", GREEN, w=9)
    kv(m, "VERDICT", "none", GREEN, w=9, gap=36)

    m.section("analytical cells")
    cells = [("capex", BLUE, "announced ≠ spent", "≠ committed"),
             ("utilization", BLUE, "contracted capacity ≠",
              "realized, profitable use"),
             ("returns", BLUE, "cash after operating,",
              "maintenance, replacement"),
             ("obligations", BLUE, "debt · projects · leases",
              "· customer commitments"),
             ("financing", BLUE, "access to new money ≠",
              "good asset economics"),
             ("?", PINK, "name: question", "verdict: none")]
    cw_, ch_, g = 316, 112, 16
    for r in range(3):
        frag = ""
        for cidx in range(2):
            k, c, l1, l2 = cells[r * 2 + cidx]
            x = X0 + cidx * (cw_ + g)
            y = m.y - 22
            frag += hud(x, y, cw_, ch_ - 14, c, 12, 1.6, 1)
            frag += t(x + 16, y + 30, f"[{k}]", FS, c, "bold")
            frag += t(x + 16, y + 60, l1, 18, WHITE)
            frag += t(x + 16, y + 86, l2, 18, ICE)
        m.raw(frag, ch_)
    m.gap(10)

    m.section("conceptual map")
    m.line(("financing", WHITE, "bold"), (" → ", PINK, "bold"),
           ("capex", WHITE, "bold"), (" → ", PINK, "bold"),
           ("capacity", WHITE, "bold"), (" → ", PINK, "bold"),
           ("use", WHITE, "bold"), (" → ", PINK, "bold"),
           ("returns", WHITE, "bold"))
    m.line(("   └─ ", BLUE), ("obligations: who pays, when, which entity?",
                              ICE), gap=36)

    m.section("counterevidence")
    m.line(("+ ", GREEN, "bold"), ("priced financing activity works against",
                                   GREEN))
    m.line(("+ ", GREEN, "bold"), ('  "capital markets have closed"', GREEN))
    m.line(("− ", PINK, "bold"), ("alone it proves nothing about lifetime "
                                  "returns", PINK), gap=36)

    m.section("open :: unresolved")
    for q in ["returns from mature asset cohorts",
              "contracted vs realized, profitable use",
              "renewal and durable demand",
              "demand that depends on continuing financing",
              "who bears the risk"]:
        m.line(("· ", PINK, "bold"), (q, WHITE))
    m.gap(8)
    m.line(("VERDICT ", BLUE, "bold"), ("none   ", WHITE),
           ("LIVE ", BLUE, "bold"), ("—   ", WHITE),
           ("ADVICE ", BLUE, "bold"), ("—", WHITE), gap=30)
    m.build(["the name is a question", "stress ≠ weak returns ≠ bubble",
             "unresolved stays unresolved"])


def mod_culture():
    m = Module("mod-culture.svg", PINK, "culture-legitimacy :: dossier",
               "03", "~/…/culture-legitimacy", "cat index.md")
    m.neofetch(emblem("culture"), (PINK, ICE), "culture@dossier",
               [("file", "Tastewashing →", WHITE),
                ("", "Cultural Legitimacy", WHITE),
                ("", "Embedding", WHITE),
                ("tag", "working title", ICE),
                ("status", "documentary", WHITE),
                ("phase", "pre-experimental", WHITE),
                ("causal", "OPEN", PINK),
                ("cutoff", "2026-08-12", WHITE)], kcol=8)
    m.section("question")
    m.wrap("why are technology and defense-tech companies becoming "
           "cultural objects through clothing, design, events, communities "
           "and identity?", color=PINK, prefix="Q  ", width=50, size=20)
    m.gap(10)

    m.section("what the comparisons showed")
    m.wrap("similar practices appear in ordinary software businesses",
           prefix="> ")
    m.wrap("traditional defense companies already have histories of "
           "national, professional and community identification",
           prefix="> ")
    m.wrap("audiences read the same object as aesthetics, career ambition, "
           "investment, fandom, irony or political affinity", prefix="> ")
    m.gap(8)

    m.section("layers")
    layers = [("01", "PRODUCTION", "", BLUE,
               "what do companies make, communicate and organize?",
               "visible branding ≠ concealed intention"),
              ("02", "RECEPTION", "", BLUE,
               "how do people interpret or use those cultural objects?",
               "selected comments ≠ population-wide attitudes"),
              ("03", "CAUSAL QUESTION", "OPEN", PINK,
               "does affinity change the legitimacy granted to a company's "
               "functions or power?",
               "liking a brand ≠ evidence of this transition")]
    for n, name, flag, c, q, caveat in layers:
        m.line(("▌", c, "bold"), (n + " ", GREEN, "bold"), (name, c, "bold"),
               ("  " + flag if flag else "", PINK, "bold"), size=20, gap=30)
        m.wrap(q, prefix="   ")
        m.line(("   LIMIT  ", PINK, "bold"), (caveat, ICE))
        m.gap(10)

    m.section("finding")
    kv(m, "CAUSAL", "not established by the reports", PINK)
    kv(m, "LINKS", "connections ≠ coordination")
    kv(m, "EFFECT", "an effect ≠ proof of intention")
    kv(m, "FRAME", "working title · unvalidated", ICE, gap=36)

    m.section("reports/")
    m.line(("├── ", LINE), ("informe-sencillo.pdf  ", WHITE, "bold"),
           ("start here · ES · 10 pp", GREEN))
    m.line(("└── ", LINE), ("informe-formal.pdf    ", WHITE, "bold"),
           ("full synthesis · ES · 13 pp", GREEN))
    kv(m, "METHOD", "AI-assisted search · comparison", ICE, w=8)
    kv(m, "", "synthesis · adversarial review", ICE, w=8, gap=30)
    m.build(["liking a brand ≠ legitimacy", "the causal question stays open",
             "working title"])


def restricted_panel():
    # Static on purpose. Only the approved public words appear here.
    h = 420
    under, over = chrome(h, ICE, bars=False)
    b = [rect(16, 16, W - 32, h - 32, stroke=ICE, sw=3, opacity=0.3,
              extra=' filter="url(#soft)"'),
         rect(16, 16, W - 32, h - 32, fill=VOID, stroke=LINE, sw=1.4)] + \
        under + [
         rect(28, 28, W - 56, h - 56, stroke=LINE, sw=1, opacity=0.7),
         hud(16, 16, W - 32, h - 32, ICE, 22, 2.4, 1),
         hud(40, 40, W - 80, h - 80, PINK, 10, 1.2, 0.8),
         rect(28, 28, W - 56, h - 56, fill="url(#scan)")]
    for i, (c, dur) in enumerate(((GREEN, "2.8s"), (PINK, None),
                                  (LINE, None))):
        anim = (f'<animate attributeName="opacity" values="1;0.3;1" '
                f'dur="{dur}" repeatCount="indefinite"/>' if dur else "")
        b.append(f'<circle cx="{W - 96 + i * 14}" cy="58" r="3.8" '
                 f'fill="{c}">{anim}</circle>')
    for i, row in enumerate(emblem("lock")):
        c = mix(ICE, PINK, i / 10)
        b.append(f'<text x="58" y="{_f(122 + i * 17)}" font-size="14" '
                 f'fill="{c}" xml:space="preserve">{escape(row)}</text>')
    b.append(t(300, 150, "ECIS", 64, WHITE, "bold", spacing=12))
    b.append(t(302, 190, "PRIVATE R&D SYSTEM", 22, ICE, spacing=2))
    b.append(line(302, 214, W - 60, 214, stroke=LINE, sw=1))
    for i, (k, v, c) in enumerate((("STATUS", "ACTIVE", GREEN),
                                   ("ACCESS", "RESTRICTED", PINK),
                                   ("DETAILS", "UNDISCLOSED", ICE))):
        y = 256 + i * 40
        b.append(t(302, y, k, 22, ICE) + t(450, y, v, 22, c, "bold",
                                           spacing=1))
    for i in range(9):
        b.append(rect(58 + i * 22, h - 72, 16, 16,
                      fill=mix(ICE, PINK, i / 8), stroke=LINE, sw=1,
                      opacity=round(0.3 + 0.07 * i, 2)))
    b.append(shimmer(58, h - 72))
    b += over
    write("restricted-panel.svg", svg(h, "\n".join(b)))


def mod_mind():
    m = Module("mod-mind-cache.svg", GREEN, "mind.cache", "05 entries", "~",
               "tail -n 5 mind.cache")
    m.neofetch(emblem("mind"), (GREEN, PINK), "mind@cache",
               [("entries", "05", WHITE), ("state", "open", GREEN),
                ("type", "thought fragments", WHITE),
                ("answers", "none cached", PINK),
                ("method", "questions first", WHITE)], kcol=9)
    qs = [("what would make me change my mind?",
           "the question i try to ask before an answer gets comfortable. "
           "a habit, not a badge."),
          ("when does authority become legitimate?",
           "political philosophy, but also companies and institutions, and "
           "why people accept the power they hold."),
          ("who gets to define normal?",
           "language, norms, culture, and the way every generation judges "
           "the next one."),
          ("how much of identity is actually ours?",
           "the question underneath a lot of the fiction in ~/library: "
           "memory, belonging, consciousness, change."),
          ("why do markets believe what they believe?",
           "a price is a story with money behind it. where does the story "
           "come from?")]
    m.section("cache.dump")
    for i, (q, note) in enumerate(qs):
        m.line((f"[0x0{i + 1}] ", GREEN, "bold"), (q, WHITE, "bold"),
               size=20, gap=30)
        m.wrap(note, color=ICE, prefix="  └ ", cont="    ", pcolor=PINK)
        m.gap(12)
    m.build(["what would make me change my mind?", "questions > answers",
             "cache stays open"])


def mod_gen():
    m = Module("mod-gen-alpha.svg", GREEN, "GEN_ALPHA.dat", "05",
               "~/research", "cat GEN_ALPHA.dat")
    m.neofetch(emblem("gen"), (GREEN, BLUE), "GEN_ALPHA.dat",
               [("type", "research label", WHITE),
                ("snapshot", "2026-08-16", WHITE),
                ("edition", "2026-10-03", WHITE),
                ("records", "5", WHITE),
                ("causality", "UNRESOLVED", PINK),
                ("research", "open", GREEN)], kcol=11)
    m.section("query")
    m.wrap("what actually changes between generations, and what changes "
           "in the comparison?", color=PINK, prefix="Q  ", width=50, size=20)
    m.gap(10)
    recs = [("educational performance ≠ general cognition",
             "tests measure abilities in defined settings, not attention, "
             "working memory or independent judgment"),
            ("population · age · task · country · period",
             "PISA 2022 tested 15-year-olds, mostly born well before the "
             "usual Gen Alpha start dates"),
            ("school conditions",
             "instruction, attendance, pandemic disruption, socioeconomic "
             "and language context"),
            ("screens · short-form · algorithms · ai",
             "separate hypotheses, separate causal evidence. association ≠ "
             "direction; uncertainty ≠ harmless"),
            ("the observer",
             'biased memory makes "kids these days" look worse; dismissing '
             'a documented decline is also an error')]
    m.section("records")
    for i, (dom, note) in enumerate(recs):
        y = m.y
        lab = f"-[ RECORD 0{i + 1} ]"
        m.raw(t(X0, y, lab, FS, GREEN, "bold") +
              line(_f(X0 + len(lab) * FS * CW + 10), y - 6, X1, y - 6,
                   stroke=GREEN, sw=1, dash="2 4"), 30)
        m.line(("domain │ ", BLUE, "bold"), (dom, WHITE, "bold"))
        for j, ln in enumerate(textwrap.wrap(note, 45)):
            m.line(("obs    │ " if j == 0 else "       │ ", BLUE, "bold"),
                   (ln, ICE))
        m.gap(8)
    m.line(("(5 rows)", ICE), gap=36)
    m.section("reading")
    kv(m, "EVIDENCE", "heterogeneous picture")
    kv(m, "THRESHOLD", "one educational trend ≠")
    kv(m, "", "a generation-wide decline")
    kv(m, "SCOPE", "selected public synthesis", ICE, gap=30)
    m.build(["educational performance ≠ cognition",
             "the observer is part of the problem", "causality unresolved"])


def mod_security():
    m = Module("mod-security.svg", BLUE, "autonomous-security :: review",
               "06", "~/…/autonomous-security", "tail review.log")
    m.neofetch(emblem("shield"), (BLUE, PINK), "review@controlled",
               [("mode", "discovery", WHITE),
                ("method", "adversarial review", WHITE),
                ("claims", "under falsification", PINK),
                ("primitive", "none validated", WHITE),
                ("product", "none", WHITE),
                ("thesis", "none", WHITE),
                ("readiness", "unclaimed", GREEN)], kcol=11)
    m.section("review.log")
    log = [("scope", "security boundaries for increasingly", WHITE),
           ("", "autonomous action", WHITE),
           ("method", "compare proposed approaches with existing", WHITE),
           ("", "research and tools", WHITE),
           ("check", "novelty claims ........ under falsification", PINK),
           ("check", "protection claims ..... under falsification", PINK),
           ("result", "validated primitive ... none", WHITE),
           ("result", "validated product ..... none", WHITE),
           ("result", "startup thesis ........ none", WHITE)]
    for k, v, c in log:
        tagtxt = f"[{k:<6}] " if k else " " * 9
        if c == PINK:
            a, b_ = v.split(" under")
            m.line((tagtxt, BLUE, "bold"), (a, ICE),
                   (" under" + b_, PINK, "bold"))
        elif "none" in v:
            a = v[:-4]
            m.line((tagtxt, BLUE, "bold"), (a, ICE), ("none", WHITE, "bold"))
        else:
            m.line((tagtxt, BLUE, "bold"), (v, WHITE))
    m.gap(10)
    m.section("threshold", GREEN)
    kv(m, "THRESHOLD", "interesting question ≠", GREEN, w=11)
    kv(m, "", "defensible contribution", GREEN, w=11)
    kv(m, "RECORD", "direction + limits", w=11)
    kv(m, "CLAIMS", "security · deployment · readiness: —", ICE, w=11)
    m.build(["research before claims",
             "an interesting question ≠ a contribution"])


def mod_markets():
    m = Module("mod-markets.svg", BLUE, "market.frequencies", "interests",
               "~", "cat .market_frequencies")
    m.neofetch(emblem("antenna"), (BLUE, PINK), "market@frequencies",
               [("type", "interests", WHITE), ("positions", "—", WHITE),
                ("wallets", "—", WHITE), ("p&l", "—", WHITE),
                ("advice", "none", GREEN), ("mode", "questions", PINK)],
               kcol=10)
    m.section("channels")
    chans = [("CH-A", "CRYPTO", PINK, "bitcoin · solana · memecoins",
              "liquidity, incentives, coordination, narrative"),
             ("CH-B", "EQUITIES", BLUE, "banks · software · ai · defense-tech",
              "raising capital, market power, dependence"),
             ("CH-C", "CREDIT", GREEN, "obligations · maturities · refinancing",
              "when a financial problem starts to travel (→ debtwatch)"),
             ("CH-D", "STRUCTURE", BLUE, "liquidity · market structure",
              "who is on the other side; what can a price tell?"),
             ("CH-E", "NARRATIVE", PINK, "narrative ↔ price",
              "why a story becomes believable once money enters it")]
    for k, (ch, name, c, topics, lens) in enumerate(chans):
        y = m.y
        pts = " ".join(f"{_f(X0 + xi)},{_f(y - 7 + 6 * math.sin(xi / 6 + k))}"
                       for xi in range(0, 62, 2))
        frag = (f'<polyline points="{pts}" stroke="{c}" stroke-width="1.6" '
                f'fill="none"/>' +
                t(X0 + 76, y, f"[{ch}]", FS, c, "bold") +
                t(X0 + 76 + 8 * FS * CW, y, name, FS, WHITE, "bold"))
        m.raw(frag, 28)
        m.line((topics, WHITE), x=X0 + 76)
        m.line((lens, ICE), x=X0 + 76, size=17, gap=38)
    m.build(["why do markets believe what they believe?", "narrative ↔ price",
             "interests > positions"])


def mod_library():
    m = Module("mod-library.svg", PINK, "library :: culture-node", "orbit",
               "~", "ls -R library/")
    m.neofetch(emblem("library"), (PINK, BLUE), "library@culture-node",
               [("works", "12", WHITE), ("shelves", "books · fiction · myth",
                                         WHITE),
                ("ratings", "—", WHITE),
                ("mode", "orbit", PINK)], kcol=9)
    shelves = [("books/", BLUE, [
        ("dune", "power, religion, prescience"),
        ("leviathan", "authority, fear, order, sovereignty"),
        ("1984", "language, memory, control"),
        ("fahrenheit_451", "distraction, reading, conformity"),
        ("brave_new_world", "desire, comfort, conditioning"),
        ("the_road", "moral continuity after institutions"),
        ("cadaver_exquisito", "normality, language, dehumanization")]),
        ("fiction/", PINK, [
            ("monster", "identity, responsibility"),
            ("cyberpunk_edgerunners", "bodies, systems bigger than one"),
            ("angel_beats", "memory, loss, continuity"),
            ("charlotte", "bonds, personal continuity")]),
        ("myth/", GREEN, [("norse", "fate, transformation, endings")])]
    for shelf, c, works in shelves:
        m.section(shelf, c)
        for name, theme in works:
            dots = "." * max(2, 18 - len(name))
            m.line((name + " ", WHITE, "bold"), (dots + " ", LINE),
                   (theme, ICE))
        m.gap(6)
    m.build(["an orbit of works", "how much of identity is ours?"])


def mod_env():
    m = Module("mod-environment.svg", GREEN, "operator.environment", "env",
               "~", "cat .operator_env")
    m.neofetch(emblem("env"), (GREEN, BLUE), "operator@env",
               [("build", "claude code · git", WHITE),
                ("editor", "vs code", WHITE), ("lang", "python", WHITE),
                ("research", "chatgpt · sources", WHITE),
                ("mastery", "undefined", PINK)], kcol=10)
    m.section(".operator_env")
    for k, v in (("BUILD", "claude-code git vscode python"),
                 ("RESEARCH", "chatgpt source-reading"),
                 ("SCREENS", "tradingview reuters coinglass"),
                 ("CRYPTO", "axiom phantom")):
        m.line(("export ", BLUE), (k, PINK, "bold"), ("=", ICE),
               (f'"{v}"', GREEN))
    m.line(("export ", BLUE), ("MASTERY", PINK, "bold"), ("=undefined", WHITE))
    m.line(("export ", BLUE), ("LOOP", PINK, "bold"), ("=", ICE),
           ('"direct compare review revise"', GREEN), gap=36)
    m.build(["still learning", "one more revision"])


def mod_side():
    m = Module("mod-side.svg", GREEN, "side.frequencies", "off-duty", "~",
               "ls side_quests/")
    m.neofetch(emblem("side"), (GREEN, PINK), "side@quests",
               [("games", "minecraft · terraria", WHITE),
                ("habitat", "weird internet corners", WHITE),
                ("tabs", "too many", PINK), ("status", "exploring", GREEN)],
               kcol=9)
    m.section("side_quests/")
    m.line(("minecraft/      ", GREEN, "bold"), ("terraria/", GREEN, "bold"),
           size=20, gap=30)
    m.line(("weird-corners-of-the-internet/", PINK, "bold"), size=20, gap=30)
    m.line(("technical-rabbit-holes/  ", BLUE, "bold"),
           ("internet-culture/", BLUE, "bold"), size=20, gap=30)
    m.line(("too-many-tabs.txt", WHITE), size=20, gap=30)
    m.build(["too many tabs", "still one more question"])


def footer():
    h = 330
    under, over = chrome(h, PINK)
    b = [window(16, 16, W - 32, h - 32, PINK, "session.end", "zh-01",
                fill=VOID)] + under + [
         hud(26, 30, W - 52, h - 52, LINE, 10, 1.2, 0.9)]
    b.append(t(36, 70, "└─$", 21, BLUE))
    cmd, t0 = typed((36 + 4 * 21 * CW), 70, "exit", 21, WHITE, 0.8, cps=8)
    b.append(cmd)
    lines = [(112, "logout", 19, ICE, "normal"),
             (160, "session closed.", 30, WHITE, "bold"),
             (200, "questions still open.", 30, WHITE, "bold"),
             (240, "snowyarch // ZÜRICH NODE", 21, PINK, "bold"),
             (268, "AFTERHOURS / PERSONAL NODE", 18, ICE, "normal")]
    for i, (y, s, size, c, wt) in enumerate(lines):
        b.append(appear(t(36, y, s, size, c, wt), t0 + 0.4 + i * 0.35))
    b.append(blink(36 + 21 * 30 * CW + 10, 200, 30, GREEN, t0 + 1.2))
    for i in range(9):
        b.append(appear(rect(W - 250 + i * 24, 252, 18, 18,
                             fill=mix(PINK, BLUE, i / 8), stroke=LINE, sw=1),
                        t0 + 1.8 + i * 0.05))
    b.append(t(36, h - 30, "~-" * 40, 14, BLUE, opacity=0.6))
    b.append(appear(shimmer(W - 250, 252, 9, 24, 18), t0 + 2.4))
    b += over
    write("footer-signal.svg", svg(h, "\n".join(b)))


def main():
    OUT.mkdir(exist_ok=True)
    for p in OUT.glob("*.svg"):
        p.unlink()
    header()
    for fn in (mod_index, mod_operator, mod_debtwatch, mod_ai, mod_culture,
               restricted_panel, mod_mind, mod_gen, mod_security, mod_markets,
               mod_library, mod_env, mod_side, footer):
        fn()
    for p in sorted(OUT.glob("*.svg")):
        print(f"{p.name:28} {p.stat().st_size:>7} bytes")


if __name__ == "__main__":
    main()
