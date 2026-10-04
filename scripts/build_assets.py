"""Generate the SVG assets for the snowyarch profile README.

Run from the repository root:

    python3 scripts/build_assets.py

The README itself is native text: code blocks hold every module's
output. The SVGs here are only the animated parts: the neofetch-style
header, one thin prompt strip per module, and the closing `exit`.

Every asset is hand-built SVG: no scripts, no external fonts, no
embedded images, no metadata. Typing effects use SMIL, and every
animation only hides things for a while, so a renderer that ignores
animation still shows the finished terminal. All visible text is
written literally in this file.
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


def window(x, y, w, h, color, title, right="", fill=PANEL):
    """A TUI pane: flat frame with the title cut into the top border."""
    out = [rect(x, y, w, h, fill=fill), rect(x, y, w, h, stroke=color, sw=1.4)]
    label = f"[ {title} ]"
    out.append(rect(x + 16, y - 13, len(label) * 20 * CW + 12, 26, fill=VOID))
    out.append(t(x + 22, y + 7, label, 20, color, "bold"))
    if right:
        rl = f"[ {right} ]"
        rw = len(rl) * 20 * CW + 12
        out.append(rect(x + w - 16 - rw, y - 13, rw, 26, fill=VOID))
        out.append(t(x + w - 22, y + 7, rl, 20, ICE, anchor="end"))
    return "\n".join(out)


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
        f'values="{";".join(_f(v) for v in xs)}"/></rect>')
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
    b = [window(16, 16, W - 32, h - 32, PINK, "snowyarch@zurich-node: ~",
                "AFTERHOURS", fill=VOID)]
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

    # neofetch-style info column
    x0 = 286
    fs2, lh2 = 19, 29
    b.append(appear(t(x0, 112, "snowyarch@zurich-node", 22, PINK, "bold"),
                    t0 + 0.1))
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
    write("header.svg", svg(h, "\n".join(b)))


def footer():
    h = 300
    rnd = random.Random(5)
    b = []
    # low skyline reprise
    x = 0
    while x < W:
        bw = rnd.choice([30, 40, 52])
        bh = rnd.randint(20, 60)
        b.append(rect(x, h - bh, bw - 3, bh, fill="#0B1220", stroke=LINE,
                      sw=1))
        x += bw
    b.append(rect(0, h - 2, W, 2, fill="url(#fadeP)"))
    # fading signal bars
    for i in range(36):
        hh = 4 + abs(math.sin(i * 0.55)) * 22 * (1 - i / 40)
        b.append(rect(32 + i * 18, 40 - hh / 2, 8, round(hh, 1), fill=PINK,
                      opacity=round(max(0.08, 0.9 - i * 0.025), 2)))
    b.append(t(40, 98, "└─$", 22, BLUE))
    cmd, t0 = typed(40 + 4 * 22 * CW, 98, "exit", 22, WHITE, 0.8, cps=8)
    b.append(cmd)
    b.append(appear(t(40, 140, "session closed.", 28, WHITE), t0 + 0.4))
    b.append(appear(t(40, 176, "questions still open.", 28, WHITE), t0 + 0.8))
    b.append(appear(t(40, 214, "snowyarch // ZÜRICH NODE", 22, PINK, "bold",
                      spacing=1), t0 + 1.2))
    b.append(blink(40 + 21 * 28 * CW + 10, 176, 28, GREEN, t0 + 1.2))
    write("footer-signal.svg", svg(h, "\n".join(b)))


MODULES = [
    # file, color, module label, right label, prompt path, command
    ("mod-index.svg", BLUE, "~/research", "index", "~/research",
     "tree -L 1"),
    ("mod-operator.svg", PINK, "operator.note", "tty1", "~",
     "cat operator.note"),
    ("mod-debtwatch.svg", BLUE, "debtwatch :: credit-console", "01",
     "~/research/debtwatch", "cat brief.md"),
    ("mod-ai-bubblewatch.svg", PINK, "ai-bubblewatch :: observatory", "02",
     "~/…/ai-bubblewatch", "cat brief.md"),
    ("mod-culture.svg", PINK, "culture-legitimacy :: dossier", "03",
     "~/…/culture-legitimacy", "tree ."),
    ("mod-mind-cache.svg", GREEN, "mind.cache", "open", "~",
     "tail -n 5 mind.cache"),
    ("mod-gen-alpha.svg", GREEN, "GEN_ALPHA.dat", "05", "~/research",
     "cat GEN_ALPHA.dat"),
    ("mod-security.svg", BLUE, "autonomous-security :: review", "06",
     "~/…/autonomous-security", "tail review.log"),
    ("mod-markets.svg", BLUE, "market.frequencies", "interests", "~",
     "cat .market_frequencies"),
    ("mod-library.svg", PINK, "library", "orbit", "~", "cat library.yml"),
    ("mod-environment.svg", GREEN, "operator.environment", "env", "~",
     "cat .operator_env"),
    ("mod-side.svg", GREEN, "side.frequencies", "off-duty", "~",
     "ls side_quests"),
]


def module_strip(name, color, label, right, path, cmd):
    """A thin module header: rule with the module name, then a prompt
    that types its command. The module's output is native text below."""
    h = 124
    fs = 21
    b = [line(16, 22, W - 16, 22, stroke=color, sw=1.4)]
    lab = f"[ {label} ]"
    b.append(rect(30, 8, len(lab) * 20 * CW + 12, 28, fill=VOID))
    b.append(t(36, 29, lab, 20, color, "bold"))
    rl = f"[ {right} ]"
    rw = len(rl) * 20 * CW + 12
    b.append(rect(W - 30 - rw, 8, rw, 28, fill=VOID))
    b.append(t(W - 36, 29, rl, 20, ICE, anchor="end"))
    b.append(t(36, 72, "┌──(", fs, BLUE) +
             t(36 + 4 * fs * CW, 72, "snowyarch@zurich", fs, PINK, "bold") +
             t(36 + 20 * fs * CW, 72, f")-[{path}]", fs, BLUE))
    b.append(t(36, 106, "└─$", fs, BLUE))
    x = 36 + 4 * fs * CW
    cmd_svg, end = typed(x, 106, cmd, fs, WHITE, 0.5, cps=16)
    b.append(cmd_svg)
    b.append(blink(x + len(cmd) * fs * CW + 6, 106, fs, GREEN, end, "6"))
    write(name, svg(h, "\n".join(b)))


def main():
    OUT.mkdir(exist_ok=True)
    keep = {"header.svg", "footer-signal.svg"} | {m[0] for m in MODULES}
    for p in OUT.glob("*.svg"):
        if p.name not in keep:
            p.unlink()
    header()
    footer()
    for m in MODULES:
        module_strip(*m)
    for p in sorted(OUT.glob("*.svg")):
        print(f"{p.name:28} {p.stat().st_size:>7} bytes")


if __name__ == "__main__":
    main()
