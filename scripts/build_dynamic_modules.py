"""Generate the dynamic ZÜRICH NODE modules into assets/dynamic/.

Run from the repository root:

    python3 scripts/build_dynamic_modules.py

These modules reuse the exact chrome, palette, typing and atmosphere of
scripts/build_assets.py, so they read as part of the same machine. Their
data is real and local:

- git history of this public repository (dates only, never hours, and
  never raw commit messages; the scheduled refresh commits are ignored)
- the files inside public/
- the hand-maintained files in data/
- the generation time in the Europe/Zurich time zone

When a source is missing, the module renders an intentional terminal
failure state instead of inventing values. The existing assets and the
README are never touched by this script.
"""

import json
import math
import subprocess
import sys
import textwrap
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_assets import (  # noqa: E402
    BLUE, CW, FS, GREEN, ICE, LINE, OUT, PINK, VOID, WHITE, X0, X1,
    Module, _f, line, mix, rect, t)

ROOT = Path(__file__).resolve().parent.parent
DYN = OUT / "dynamic"
TZ = ZoneInfo("Europe/Zurich")
NOW = datetime.now(TZ)
REFRESH_SUBJECT = "chore(node): refresh dynamic signals"


# ---------------------------------------------------------------- sources

def git(*args):
    try:
        r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                           text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout if r.returncode == 0 else None


def commits(limit=400):
    """Public commits of this repo, newest first: (hash, date, files).
    Refresh commits made by the workflow are skipped so the node does not
    report on itself."""
    raw = git("log", f"-n{limit}", "--name-only",
              "--format=\x1e%h\x1f%cI\x1f%s")
    if raw is None:
        return None
    out = []
    for chunk in raw.split("\x1e")[1:]:
        head, *files = chunk.strip("\n").split("\n")
        h, when, subject = head.split("\x1f", 2)
        files = [f for f in files if f]
        if subject.startswith(REFRESH_SUBJECT):
            continue
        if files and all(f.startswith("assets/dynamic/") for f in files):
            continue
        day = datetime.fromisoformat(when).astimezone(TZ).date()
        out.append((h, day, files))
    return out


def classify(files):
    if any(f == "README.md" for f in files):
        return "PROFILE"
    if any(f.startswith("public/") for f in files):
        return "PUBLIC"
    if any(f.startswith(("data/", ".github/", "assets/dynamic/"))
           or f.endswith("build_dynamic_modules.py") for f in files):
        return "DYNAMIC"
    if any(f.startswith("assets/") for f in files):
        return "ASSET"
    return "DOC"


CLASS_TEXT = {"PROFILE": "profile surface updated",
              "PUBLIC": "public archive updated",
              "DYNAMIC": "dynamic node updated",
              "ASSET": "visual assets updated",
              "DOC": "docs / tooling updated"}
CLASS_COLOR = {"PROFILE": PINK, "PUBLIC": GREEN, "DYNAMIC": BLUE,
               "ASSET": ICE, "DOC": ICE}


def load_json(name):
    try:
        return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def stamp():
    return NOW.strftime("%Y-%m-%d")


# ---------------------------------------------------------------- helpers

class Dyn(Module):
    """A Module without a neofetch head: the body starts under the prompt."""

    def start(self, y=112):
        self.y = y


def ascii_rows(art):
    return art.strip("\n").split("\n")


def pulse_rings(cx, cy, color, n=3, r0=6, r1=34, dur=3.0):
    out = []
    for i in range(n):
        out.append(
            f'<circle cx="{_f(cx)}" cy="{_f(cy)}" r="{r0}" fill="none" '
            f'stroke="{color}" stroke-width="1.4" opacity="0">'
            f'<animate attributeName="r" values="{r0};{r1}" dur="{dur}s" '
            f'begin="{_f(i * dur / n)}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0.8;0" dur="{dur}s" '
            f'begin="{_f(i * dur / n)}s" repeatCount="indefinite"/>'
            f'</circle>')
    return "".join(out)


def led(cx, cy, color, dur=None, r=4):
    anim = (f'<animate attributeName="opacity" values="1;0.3;1" '
            f'dur="{dur}" repeatCount="indefinite"/>' if dur else "")
    return f'<circle cx="{_f(cx)}" cy="{_f(cy)}" r="{r}" fill="{color}">{anim}</circle>'


def failure(m, state, detail):
    """An intentional terminal failure state."""
    m.section("status", PINK)
    m.line(("[ ", ICE), ("!!", PINK, "bold"), (" ] ", ICE),
           (state, PINK, "bold"), size=22, gap=34)
    m.line(("# ", ICE), (detail, ICE), gap=34)
    m.line(("# ", ICE), ("no values are shown rather than invented", ICE),
           gap=30)


# ---------------------------------------------------------------- modules

def boot_sequence():
    m = Module("dynamic/boot-sequence.svg", GREEN, "boot.sequence", "zh-01",
               "~", "boot --public")
    checks = [
        ("/research", sorted(ROOT.glob("public/*.md")), "public notes"),
        ("/markets", [ROOT / "assets/mod-markets.svg"], "frequency module"),
        ("/library", [ROOT / "assets/mod-library.svg"], "culture node"),
        ("/archive", sorted(ROOT.glob("public/*")), "public files"),
        ("/signals", [ROOT / "data/orbit.json",
                      ROOT / "data/research-queue.json"], "node data"),
        ("/radio", [ROOT / "assets/dynamic/radio-afterhours.svg"], ""),
    ]
    results = []
    for mount, paths, what in checks:
        found = [p for p in paths if p.exists()]
        ok = bool(found)
        results.append((mount, ok, f"{len(found)} {what}" if ok else ""))
    mounted = sum(1 for _, ok, _ in results if ok)
    m.neofetch(ascii_rows(r"""
   .---------------.
   |  ZÜRICH  //   |
   |  NODE   01    |
   '-------.-------'
           |
   .-------'-------.
   | ############  |
   '---------------'
     SIGNAL  INIT
"""), (GREEN, BLUE), "boot@zurich-node",
        [("node", "zh-01", WHITE), ("mode", "public", WHITE),
         ("mounted", f"{mounted} / {len(results)}", GREEN),
         ("boot", stamp(), WHITE), ("tz", "Europe/Zurich", WHITE),
         ("scope", "public only", ICE)], kcol=9)
    # boot progress bar under the emblem: fills once, then holds
    m.head.append(
        f'<rect x="{X0 + 24}" y="210" width="0" height="10" fill="{GREEN}" '
        f'opacity="0.85"><animate attributeName="width" values="0;150" '
        f'dur="2.4s" begin="1.2s" fill="freeze"/></rect>')
    m.section("boot.log")
    m.line(("[ .. ] ", ICE), ("kernel: afterhours personal node", WHITE))
    m.line(("[ .. ] ", ICE), ("tz: Europe/Zurich · node time", WHITE), gap=34)
    for mount, ok, note in results:
        if ok:
            m.line(("[ ", ICE), ("OK", GREEN, "bold"), (" ] ", ICE),
                   (f"{mount:<12}", WHITE, "bold"), (note, ICE))
        else:
            m.line(("[ ", ICE), ("--", PINK, "bold"), (" ] ", ICE),
                   (f"{mount:<12}", ICE, "bold"), ("NOT MOUNTED", PINK, "bold"))
    m.gap(8)
    m.line(("node.status       ", BLUE, "bold"), ("ONLINE", GREEN, "bold"),
           size=20, gap=30)
    m.line(("scope             ", BLUE, "bold"), ("public modules only", ICE),
           size=20, gap=30)
    m.build(["boot --public", f"{mounted} modules mounted",
             "radio: not mounted yet"])


def transmission_log():
    m = Module("dynamic/transmission-log.svg", PINK, "transmission.log",
               "rx", "~", "tail -n 5 transmission.log")
    data = commits()
    recent = data[:5] if data else []
    last = recent[0][1].isoformat() if recent else "—"
    m.neofetch(ascii_rows(r"""
          /\
         /  \
        / || \
          ||
     ))   ||   ((
    )))   ||   (((
          ||
     [ RECEIVER ]
     '----------'
"""), (PINK, BLUE), "rx@transmission",
        [("source", "public repo commits", WHITE),
         ("window", "last 5", WHITE), ("format", "classified", WHITE),
         ("raw msgs", "hidden", ICE), ("last rx", last, GREEN)], kcol=10)
    m.head.append(pulse_rings(X0 + 92, 126, PINK, 3, 4, 40, 2.8))
    if data is None:
        failure(m, "SIGNAL SOURCE UNAVAILABLE", "git history could not be read")
    elif not recent:
        failure(m, "NO RECENT PUBLIC TRANSMISSION", "no commits in history")
    else:
        m.section("incoming")
        for i, (h, day, files) in enumerate(recent):
            cls = classify(files)
            mark = "●" if i == 0 else ("◆" if cls == "ASSET" else "○")
            c = CLASS_COLOR[cls]
            m.line((f"{mark} ", PINK if i == 0 else c, "bold"),
                   (day.isoformat() + "  ", WHITE),
                   (f"{cls:<9}", c, "bold"), (h, LINE), size=19, gap=26)
            m.line(("  └ ", LINE), (CLASS_TEXT[cls], ICE), size=18, gap=32)
        m.gap(4)
        m.line(("● incoming  ○ archived  ◆ asset", ICE), size=17, gap=26)
        m.line(("# dates only · messages are classified, not shown", ICE),
               size=17, gap=28)
    m.build(["tail -n 5 transmission.log", "listening on public repo"])


def signal_activity():
    m = Module("dynamic/signal-activity.svg", BLUE, "signal.activity", "14d",
               "~", "rx --window 14d")
    data = commits()
    days = [NOW.date() - timedelta(days=13 - i) for i in range(14)]
    counts = None
    if data is not None:
        per = {d: 0 for d in days}
        for _, day, _ in data:
            if day in per:
                per[day] += 1
        counts = [per[d] for d in days]
    total = sum(counts) if counts else 0
    lastday = next((d for d in reversed(days) if counts and
                    counts[days.index(d)]), None)
    m.neofetch(ascii_rows(r"""
           |
          /|\
         / | \
        /  |  \
       /   |   \
     ))    |    ((
    )))    |    (((
       '---+---'
     =============
"""), (BLUE, GREEN), "rx@signal",
        [("rx", "ACTIVE" if total else "IDLE", GREEN if total else ICE),
         ("window", "14 days", WHITE),
         ("source", "public repo commits", WHITE),
         ("total", str(total) if counts else "—", WHITE),
         ("peak", f"{max(counts)}/day" if counts else "—", WHITE),
         ("last", lastday.isoformat() if lastday else "—", GREEN)], kcol=8)
    m.head.append(pulse_rings(X0 + 92, 120, BLUE, 3, 4, 44, 3.2))
    if counts is None:
        failure(m, "SIGNAL SOURCE UNAVAILABLE", "git history could not be read")
        m.build(["rx --window 14d", "no signal source"])
        return
    m.section("spectrum :: commits / day")
    top, hgt = m.y, 170
    base = top + hgt
    slot = (X1 - X0) / 14
    peak = max(counts) or 1
    g = [rect(X0, top - 8, X1 - X0, hgt + 16, fill="url(#grid)")]
    for k in range(1, 4):
        g.append(line(X0, base - hgt * k / 4, X1, base - hgt * k / 4,
                      stroke=LINE, sw=1, dash="2 6", opacity=0.7))
    for i, (d, c) in enumerate(zip(days, counts)):
        x = X0 + i * slot + slot * 0.2
        w = slot * 0.6
        if c:
            bh = max(6, (hgt - 26) * c / peak)
            col = mix(BLUE, GREEN, c / peak)
            g.append(rect(_f(x), _f(base - bh), _f(w), _f(bh), fill=col,
                          opacity=0.25, extra=' filter="url(#soft)"'))
            g.append(rect(_f(x), _f(base - bh), _f(w), _f(bh), fill=col,
                          opacity=0.85))
            g.append(rect(_f(x), _f(base - bh - 3), _f(w), 2, fill=WHITE))
            g.append(t(_f(x + w / 2), _f(base - bh - 10), str(c), 16, WHITE,
                       "bold", anchor="middle"))
        else:
            g.append(rect(_f(x), base - 2, _f(w), 2, fill=LINE))
        g.append(t(_f(x + w / 2), base + 22, d.strftime("%d"), 15, ICE,
                   anchor="middle"))
    g.append(line(X0, base, X1, base, stroke=BLUE, sw=1.4))
    # a slow receiver sweep across the window
    g.append(f'<rect x="{X0}" y="{top - 8}" width="3" height="{hgt + 8}" '
             f'fill="{GREEN}" opacity="0.5"><animate attributeName="x" '
             f'values="{X0};{X1 - 3}" dur="7s" repeatCount="indefinite"/>'
             f'</rect>')
    if not total:
        g.append(t((X0 + X1) / 2, top + hgt / 2, "NO SIGNAL IN WINDOW", 22,
                   PINK, "bold", anchor="middle"))
    m.raw("".join(g), hgt + 48)
    m.line((f"{days[0].isoformat()} → {days[-1].isoformat()}", ICE),
           size=17, gap=26)
    m.line(("# real counts · scheduled refresh commits excluded", ICE),
           size=17, gap=28)
    m.build(["rx --window 14d", "signal is real or it is absent"])


def currently_orbiting():
    m = Module("dynamic/currently-orbiting.svg", PINK, "currently.orbiting",
               "orbit", "~", "orbit --list")
    data = load_json("orbit.json")
    entries = []
    if data and isinstance(data.get("orbit"), list):
        for e in data["orbit"][:4]:
            cat = str(e.get("category", "")).strip().upper()[:12]
            item = str(e.get("item", "")).strip()[:30]
            if cat and item:
                entries.append((cat, item))
    m.neofetch(ascii_rows(r"""
          .   *   .
      .-~~~~~~~~~~~-.
    .'   .-~~~~~-.   '.
   /    /  (@@)   \    \
  |  o |  (@@@@)   | o  |
   \    \  (@@)   /    /
    '.   '-~~~~~-'   .'
      '-~~~~~~~~~~~-'
          .   *   .
"""), (PINK, BLUE), "orbit@zurich-node",
        [("mode", "CURRENT ORBIT", PINK), ("bodies", str(len(entries)), WHITE),
         ("source", "data/orbit.json", WHITE),
         ("claim", "orbit, not a log", ICE), ("sync", stamp(), GREEN)],
        kcol=8)
    if not entries:
        failure(m, "ORBIT EMPTY", "data/orbit.json has no entries")
        m.build(["orbit --list", "nothing in orbit"])
        return
    m.section("orbital display")
    top = m.y
    cx, cy = (X0 + X1) / 2, top + 150
    g = [rect(X0, top - 10, X1 - X0, 300, fill="url(#grid)", opacity=0.6)]
    rings = [(268, 118, PINK, "7 6"), (190, 82, BLUE, "3 7"),
             (110, 46, LINE, "2 5")]
    for rx, ry, c, dash in rings:
        g.append(f'<ellipse cx="{_f(cx)}" cy="{_f(cy)}" rx="{rx}" ry="{ry}" '
                 f'fill="none" stroke="{c}" stroke-width="1.2" '
                 f'stroke-dasharray="{dash}" opacity="0.8"/>')
    # small bodies drifting along the rings
    for k, (rx, ry, c, _) in enumerate(rings):
        path = (f"M{_f(cx + rx)} {_f(cy)} A{rx} {ry} 0 1 1 {_f(cx - rx)} "
                f"{_f(cy)} A{rx} {ry} 0 1 1 {_f(cx + rx)} {_f(cy)}")
        for j in range(2):
            g.append(f'<circle r="3" fill="{c if c != LINE else ICE}">'
                     f'<animateMotion dur="{36 + k * 14}s" '
                     f'begin="-{j * (18 + k * 7)}s" repeatCount="indefinite" '
                     f'path="{path}"/></circle>')
    g.append(pulse_rings(cx, cy, PINK, 3, 18, 46, 4))
    g.append(f'<circle cx="{_f(cx)}" cy="{_f(cy)}" r="16" fill="{VOID}" '
             f'stroke="{PINK}" stroke-width="2"/>'
             f'<circle cx="{_f(cx)}" cy="{_f(cy)}" r="5" fill="{PINK}"/>')
    g.append(t(cx, cy + 40, "SNOWYARCH", 18, WHITE, "bold", anchor="middle"))
    spots = [(-0.78, -0.62, "end"), (0.78, -0.62, "start"),
             (-0.78, 0.66, "end"), (0.78, 0.66, "start")]
    colors = [PINK, BLUE, GREEN, ICE]
    for (sx, sy, anchor), (cat, item), c in zip(spots, entries, colors):
        nx, ny = cx + sx * 268 * 0.82, cy + sy * 118 * 0.95
        g.append(line(_f(cx), _f(cy), _f(nx), _f(ny), stroke=c, sw=1,
                      dash="2 5", opacity=0.7))
        g.append(f'<circle cx="{_f(nx)}" cy="{_f(ny)}" r="7" fill="{c}"/>'
                 f'<circle cx="{_f(nx)}" cy="{_f(ny)}" r="13" fill="none" '
                 f'stroke="{c}" stroke-width="1.2" opacity="0.6"/>')
        tx = nx - 20 if anchor == "end" else nx + 20
        g.append(t(_f(tx), _f(ny - 4), f"[ {cat} ]", 16, c, "bold",
                   anchor=anchor))
    m.raw("".join(g), 300)
    m.section("bodies")
    for (cat, item), c in zip(entries, colors):
        dots = "." * max(2, 14 - len(cat))
        m.line((cat + " ", c, "bold"), (dots + " ", LINE), (item, WHITE))
    m.gap(4)
    m.line(("# current orbit · not a reading log · hand-maintained", ICE),
           size=17, gap=28)
    m.build(["orbit --list", "what keeps pulling me back"])


STATE_GLYPH = {"OPEN": ("●", GREEN), "QUEUED": ("○", BLUE),
               "PARKED": ("◇", ICE)}


def research_queue():
    m = Module("dynamic/research-queue.svg", GREEN, "research.queue", "jobs",
               "~/research", "queue --list")
    data = load_json("research-queue.json")
    jobs = []
    if data and isinstance(data.get("queue"), list):
        for j in data["queue"]:
            st = str(j.get("state", "")).upper()
            q = str(j.get("question", "")).strip()
            if st in STATE_GLYPH and q:
                jobs.append((st, str(j.get("module", "")).strip()[:20], q))
    counts = {s: sum(1 for j in jobs if j[0] == s) for s in STATE_GLYPH}
    m.neofetch(ascii_rows(r"""
   .-----------------.
   | [#] [#] [#] [ ] |
   |-----------------|
   | [#] [#] [ ] [ ] |
   |-----------------|
   | [#] [ ] [ ] [ ] |
   '--------.--------'
         ___|___
        |_______|
"""), (GREEN, BLUE), "queue@scheduler",
        [("jobs", str(len(jobs)), WHITE), ("open", str(counts["OPEN"]), GREEN),
         ("queued", str(counts["QUEUED"]), BLUE),
         ("parked", str(counts["PARKED"]), ICE),
         ("eta", "none", ICE), ("source", "data/research-queue.json", WHITE)],
        kcol=8)
    if not jobs:
        failure(m, "QUEUE EMPTY", "data/research-queue.json has no jobs")
        m.build(["queue --list", "queue empty"])
        return
    m.section("process table")
    m.raw(rect(X0, m.y - 21, X1 - X0, 30, fill="#101724") +
          t(X0 + 12, m.y, "PID", 16, ICE, "bold") +
          t(X0 + 70, m.y, "STATE", 16, ICE, "bold") +
          t(X0 + 170, m.y, "SIG", 16, ICE, "bold") +
          t(X0 + 230, m.y, "MODULE", 16, ICE, "bold"), 40)
    for i, (st, mod, q) in enumerate(jobs):
        glyph, c = STATE_GLYPH[st]
        y = m.y
        frag = led(X0 + 4, y - 6, c, "2.4s" if st == "OPEN" else None, 3)
        frag += t(X0 + 12, y, f"{i + 1:02d}", FS, GREEN, "bold")
        frag += t(X0 + 70, y, st, FS, c, "bold")
        frag += t(X0 + 176, y, glyph, FS, c, "bold")
        frag += t(X0 + 230, y, mod, FS, WHITE, "bold")
        # memory-row ornament: identical for every job, never a measure
        for k in range(6):
            frag += rect(X1 - 76 + k * 12, y - 13, 8, 12, fill=c,
                         opacity=round(0.15 + 0.06 * k, 2))
        m.raw(frag, 26)
        for ln in textwrap.wrap(q, 48):
            m.line(("     ", LINE), (ln, ICE), size=18, gap=24)
        m.raw(line(X0, m.y - 14, X1, m.y - 14, stroke=LINE, dash="3 5"), 14)
    m.line(("● OPEN   ○ QUEUED   ◇ PARKED", ICE), size=17, gap=26)
    m.line(("# no percentages · no ETA · states set by hand", ICE),
           size=17, gap=28)
    m.build(["queue --list", "questions run until they close"])


def node_clock():
    m = Dyn("dynamic/node-clock.svg", BLUE, "node.clock", "europe/zurich",
            "~", "date --tz Europe/Zurich")
    m.start(116)
    top = m.y
    cx, cy, r = X0 + 120, top + 112, 96
    g = []
    g.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#0B1220" '
             f'stroke="{BLUE}" stroke-width="1.6"/>')
    g.append(f'<circle cx="{cx}" cy="{cy}" r="{r + 10}" fill="none" '
             f'stroke="{LINE}" stroke-width="1" stroke-dasharray="2 6">'
             f'<animateTransform attributeName="transform" type="rotate" '
             f'values="0 {cx} {cy};360 {cx} {cy}" dur="60s" '
             f'repeatCount="indefinite"/></circle>')
    for k in range(60):
        a = math.radians(k * 6)
        r0 = r - (12 if k % 5 == 0 else 5)
        g.append(line(_f(cx + r0 * math.sin(a)), _f(cy - r0 * math.cos(a)),
                      _f(cx + (r - 2) * math.sin(a)),
                      _f(cy - (r - 2) * math.cos(a)),
                      stroke=WHITE if k % 15 == 0 else (ICE if k % 5 == 0
                                                         else LINE),
                      sw=2 if k % 5 == 0 else 1))
    hh, mm = NOW.hour % 12, NOW.minute
    for ang, ln, c, w in ((math.radians((hh + mm / 60) * 30), r * 0.5, WHITE,
                           4), (math.radians(mm * 6), r * 0.78, BLUE, 2.5)):
        g.append(line(cx, cy, _f(cx + ln * math.sin(ang)),
                      _f(cy - ln * math.cos(ang)), stroke=c, sw=w))
    g.append(f'<circle cx="{cx}" cy="{cy}" r="5" fill="{PINK}"/>')
    g.append(pulse_rings(cx, cy, BLUE, 2, 8, 30, 4))
    # digital readout
    rx = X0 + 272
    g.append(t(rx, top + 6, "ZÜRICH NODE TIME", 19, PINK, "bold"))
    g.append(t(rx, top + 26, "-" * 16, 19, LINE))
    hh24 = NOW.strftime("%H")
    g.append(t(rx, top + 100, hh24, 64, WHITE, "bold"))
    g.append(f'<text x="{_f(rx + 2 * 64 * CW)}" y="{top + 96}" '
             f'font-size="64" fill="{BLUE}" font-weight="bold">:'
             f'<animate attributeName="opacity" values="1;1;0.15;0.15" '
             f'keyTimes="0;0.5;0.5;1" dur="2s" repeatCount="indefinite"/>'
             f'</text>')
    g.append(t(_f(rx + 3 * 64 * CW), top + 100, NOW.strftime("%M"), 64,
               WHITE, "bold"))
    off = NOW.utcoffset() or timedelta(0)
    sign = "+" if off >= timedelta(0) else "-"
    oh, om = divmod(int(abs(off).total_seconds()) // 60, 60)
    rows = [("zone", NOW.tzname() or "—", GREEN),
            ("offset", f"UTC{sign}{oh:02d}:{om:02d}", WHITE),
            ("date", stamp(), WHITE),
            ("sync", "at generation", WHITE)]
    for i, (k, v, c) in enumerate(rows):
        y = top + 140 + i * 26
        g.append(t(rx, y, f"{k}:", 18, BLUE, "bold") +
                 t(_f(rx + 8 * 18 * CW), y, v, 18, c))
    m.raw("".join(g), 252)
    m.section("timing")
    wy = m.y
    pts, x, hi = [], X0, False
    while x <= X1:
        pts.append(f"{_f(x)},{wy - (14 if hi else 0)}")
        x += 24
        pts.append(f"{_f(min(x, X1))},{wy - (14 if hi else 0)}")
        hi = not hi
    m.raw(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{GREEN}" '
          f'stroke-width="1.6" stroke-dasharray="6 4">'
          f'<animate attributeName="stroke-dashoffset" values="0;-40" '
          f'dur="2s" repeatCount="indefinite"/></polyline>', 30)
    m.line(("state    ", BLUE, "bold"), ("snapshot · refreshed by workflow",
                                         WHITE))
    m.line(("note     ", BLUE, "bold"), ("node time, not a location", ICE),
           gap=30)
    m.build(["date --tz Europe/Zurich", "time as of the last refresh"])


MAP_NODES = [("n01", "MARKETS", BLUE), ("n02", "PHILOSOPHY", PINK),
             ("n03", "CULTURE", PINK), ("n04", "AI / SYSTEMS", BLUE),
             ("n05", "SECURITY", BLUE), ("n06", "RESEARCH", GREEN),
             ("n07", "LIBRARY", GREEN)]
MAP_LINKS = [("n01", "n06"), ("n02", "n03"), ("n03", "n07"),
             ("n04", "n05"), ("n04", "n06"), ("n02", "n07")]


def signal_map():
    m = Dyn("dynamic/signal-map.svg", BLUE, "signal.map", "conceptual",
            "~", "netmap --conceptual")
    m.start(110)
    top = m.y
    m.section("topology :: snowyarch")
    top = m.y
    cx, cy = (X0 + X1) / 2, top + 220
    rx, ry = 236, 170
    g = [rect(X0, top - 10, X1 - X0, 470, fill="url(#grid)", opacity=0.7)]
    for rr, op in ((ry * 1.18, 0.35), (ry * 0.62, 0.5)):
        g.append(f'<ellipse cx="{_f(cx)}" cy="{_f(cy)}" rx="{_f(rr * rx / ry)}" '
                 f'ry="{_f(rr)}" fill="none" stroke="{LINE}" '
                 f'stroke-width="1" stroke-dasharray="2 6" opacity="{op}"/>')
    pos = {}
    for i, (nid, label, c) in enumerate(MAP_NODES):
        a = -math.pi / 2 + i * 2 * math.pi / len(MAP_NODES)
        pos[nid] = (cx + rx * math.cos(a), cy + ry * math.sin(a))
    # affinity links (dotted) between related nodes
    for a_, b_ in MAP_LINKS:
        (x1, y1), (x2, y2) = pos[a_], pos[b_]
        g.append(line(_f(x1), _f(y1), _f(x2), _f(y2), stroke=LINE, sw=1.2,
                      dash="3 6"))
    # spokes with packets travelling outwards and back
    for i, (nid, label, c) in enumerate(MAP_NODES):
        x, y = pos[nid]
        g.append(line(_f(cx), _f(cy), _f(x), _f(y), stroke=c, sw=1.4,
                      opacity=0.55))
        p = f"M{_f(cx)} {_f(cy)} L{_f(x)} {_f(y)}"
        g.append(f'<circle r="3" fill="{WHITE}"><animateMotion '
                 f'dur="{3.2 + (i % 3) * 0.7}s" begin="{_f(i * 0.45)}s" '
                 f'repeatCount="indefinite" path="{p}"/>'
                 f'<animate attributeName="opacity" values="0;1;1;0" '
                 f'dur="{3.2 + (i % 3) * 0.7}s" begin="{_f(i * 0.45)}s" '
                 f'repeatCount="indefinite"/></circle>')
    for i, (nid, label, c) in enumerate(MAP_NODES):
        x, y = pos[nid]
        g.append(f'<circle cx="{_f(x)}" cy="{_f(y)}" r="16" fill="{c}" '
                 f'opacity="0.18" filter="url(#soft)"/>')
        g.append(f'<circle cx="{_f(x)}" cy="{_f(y)}" r="12" fill="{VOID}" '
                 f'stroke="{c}" stroke-width="1.6"/>'
                 f'<circle cx="{_f(x)}" cy="{_f(y)}" r="5" fill="{c}">'
                 f'<animate attributeName="opacity" values="1;0.4;1" '
                 f'dur="{2.4 + i * 0.3:.1f}s" repeatCount="indefinite"/>'
                 f'</circle>')
        side = abs(y - cy) < 60
        above = y < cy - 10 or side
        ly = y - 24 if above else y + 34
        g.append(t(_f(x), _f(ly), label, 17, WHITE, "bold", anchor="middle"))
        g.append(t(_f(x), _f(ly - 18 if above else ly + 18), nid, 13, c,
                   anchor="middle"))
    g.append(pulse_rings(cx, cy, PINK, 3, 20, 60, 4.5))
    g.append(f'<circle cx="{_f(cx)}" cy="{_f(cy)}" r="24" fill="{VOID}" '
             f'stroke="{PINK}" stroke-width="2.2"/>'
             f'<circle cx="{_f(cx)}" cy="{_f(cy)}" r="14" fill="none" '
             f'stroke="{PINK}" stroke-width="1" stroke-dasharray="3 3">'
             f'<animateTransform attributeName="transform" type="rotate" '
             f'values="0 {_f(cx)} {_f(cy)};360 {_f(cx)} {_f(cy)}" dur="20s" '
             f'repeatCount="indefinite"/></circle>'
             f'<circle cx="{_f(cx)}" cy="{_f(cy)}" r="6" fill="{PINK}"/>')
    g.append(t(cx, cy + 46, "SNOWYARCH", 18, PINK, "bold", anchor="middle"))
    g.append(t(cx, cy + 64, "n00", 13, ICE, anchor="middle"))
    m.raw("".join(g), 470)
    m.line(("● node   ── signal   ┄┄ affinity", ICE), size=17, gap=26)
    m.line(("# conceptual topology · not geography · no locations", ICE),
           size=17, gap=28)
    m.build(["netmap --conceptual", "everything routes through questions"])


def signal_archive():
    m = Module("dynamic/signal-archive.svg", PINK, "signal.archive",
               "public/", "~", "ls -la public/")
    pub = ROOT / "public"
    files = sorted(p for p in pub.glob("*") if p.is_file()) if pub.is_dir() \
        else []
    info = []
    for p in files:
        rel = p.relative_to(ROOT).as_posix()
        when = (git("log", "-1", "--format=%cI", "--", rel) or "").strip()
        day = (datetime.fromisoformat(when).astimezone(TZ).date().isoformat()
               if when else "uncommitted")
        info.append((p.name, p.suffix.lstrip(".") or "file",
                     p.stat().st_size, day))
    last = max((d for *_, d in info if d != "uncommitted"), default="—")
    total = sum(s for _, _, s, _ in info)
    m.neofetch(ascii_rows(r"""
     .-------------.
     |  ___   ___  |
     | |01 | |02 | |
     | |___| |___| |
     |  ___   ___  |
     | |03 | |04 | |
     | |___| |___| |
     |  ___   ___  |
     | |05 | |06 | |
     '-------------'
"""), (PINK, ICE), "archive@public",
        [("files", str(len(info)), WHITE),
         ("state", "MOUNTED" if info else "NOT MOUNTED",
          GREEN if info else PINK),
         ("size", f"{total / 1024:.0f} KB" if info else "—", WHITE),
         ("changed", last, WHITE), ("scope", "public/ only", ICE)], kcol=9)
    if not info:
        failure(m, "ARCHIVE NOT MOUNTED", "public/ is missing or empty")
        m.build(["ls -la public/", "archive not mounted"])
        return
    m.section("/public")
    for i, (name, ext, size, day) in enumerate(info):
        pre = "└── " if i == len(info) - 1 else "├── "
        c = GREEN if ext == "pdf" else BLUE
        m.raw(led(X0 + 4, m.y - 6, c, None, 3), 0)
        m.line(("  " + pre, LINE), (name, WHITE, "bold"), size=18, gap=24)
        kb = f"{size / 1024:.1f} KB"
        m.line(("  " + ("    " if i == len(info) - 1 else "│   "), LINE),
               (f"{ext:<4} ", c, "bold"), (f"{kb:>9}  ", ICE), (day, ICE),
               size=16, gap=28)
    m.gap(4)
    m.line(("# generated from public/ · nothing outside it", ICE),
           size=17, gap=28)
    m.build(["ls -la public/", "the archive is the public record"])


def main():
    DYN.mkdir(parents=True, exist_ok=True)
    for fn in (boot_sequence, transmission_log, signal_activity,
               currently_orbiting, research_queue, node_clock, signal_map,
               signal_archive):
        fn()
    for p in sorted(DYN.glob("*.svg")):
        print(f"dynamic/{p.name:28} {p.stat().st_size:>7} bytes")


if __name__ == "__main__":
    main()
