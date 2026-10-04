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
import os
import re
import urllib.parse
import urllib.request
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


GH_USER = os.environ.get("NODE_GITHUB_USER", "snowyarch")
EVENT_CLASS = {
    "PushEvent": "PUSH",
    "CreateEvent": "CREATE", "PublicEvent": "CREATE", "ReleaseEvent": "CREATE",
    "WatchEvent": "SOCIAL", "ForkEvent": "SOCIAL",
    "IssuesEvent": "THREAD", "IssueCommentEvent": "THREAD",
    "PullRequestEvent": "THREAD", "PullRequestReviewEvent": "THREAD",
    "PullRequestReviewCommentEvent": "THREAD", "CommitCommentEvent": "THREAD",
}


def public_events(days=14):
    """Public GitHub events of GH_USER inside the window, as (date, class).
    Uses the public events endpoint only (never private data). The token,
    when present, only raises the rate limit. Returns None when the API
    cannot be reached, so the module shows a failure state instead."""
    since = NOW.date() - timedelta(days=days - 1)
    headers = {"Accept": "application/vnd.github+json",
               "User-Agent": "zurich-node-refresh",
               "X-GitHub-Api-Version": "2022-11-28"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    out = []
    for page in (1, 2, 3):  # the endpoint serves at most 300 events
        url = (f"https://api.github.com/users/{GH_USER}/events/public"
               f"?per_page=100&page={page}")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=20) as r:
                batch = json.loads(r.read().decode("utf-8"))
        except (OSError, ValueError):
            return None
        if not isinstance(batch, list):
            return None
        for e in batch:
            day = datetime.fromisoformat(
                e["created_at"].replace("Z", "+00:00")).astimezone(TZ).date()
            if day < since:
                continue
            # skip the node's own scheduled refresh pushes
            if e.get("type") == "PushEvent":
                msgs = [c.get("message", "") for c in
                        e.get("payload", {}).get("commits", []) or []]
                if msgs and all(m.startswith(REFRESH_SUBJECT) for m in msgs):
                    continue
            out.append((day, EVENT_CLASS.get(e.get("type"), "OTHER")))
        if len(batch) < 100 or (batch and datetime.fromisoformat(
                batch[-1]["created_at"].replace("Z", "+00:00"))
                .astimezone(TZ).date() < since):
            break
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


def failure(m, state, source, cond):
    """An intentional terminal failure state."""
    m.section("status", PINK)
    m.line(("[ ", ICE), ("!!", PINK, "bold"), (" ] ", ICE),
           (state, PINK, "bold"), size=22, gap=36)
    m.line(("SOURCE   ", BLUE, "bold"), (source, WHITE))
    m.line(("STATE    ", BLUE, "bold"), (cond, PINK), gap=30)


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
        ("/radio", [ROOT / "assets/dynamic/radio-afterhours.svg"],
         "station deck"),
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
    m.line(("[ .. ] ", ICE), ("tz: Europe/Zurich", WHITE), gap=34)
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
             "afterhours // zürich node" if mounted == len(results)
             else "awaiting mounts"])


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
         ("scope", "snowyarch/snowyarch", WHITE),
         ("window", "last 5", WHITE), ("mode", "classified", WHITE),
         ("last rx", last, GREEN)], kcol=9)
    m.head.append(pulse_rings(X0 + 92, 126, PINK, 3, 4, 40, 2.8))
    if data is None:
        failure(m, "SIGNAL SOURCE UNAVAILABLE", "repo history", "unreadable")
    elif not recent:
        failure(m, "NO RECENT PUBLIC TRANSMISSION", "repo history", "empty")
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
        m.line(("● incoming  ○ archived  ◆ asset", ICE), size=17, gap=28)
    m.build(["tail -n 5 transmission.log", "listening on public repo"])


EV_COLORS = [("PUSH", GREEN), ("CREATE", BLUE), ("THREAD", WHITE),
             ("SOCIAL", PINK), ("OTHER", ICE)]


def signal_activity():
    m = Module("dynamic/signal-activity.svg", BLUE, "signal.activity", "14d",
               "~", f"rx --user {GH_USER} --window 14d")
    events = public_events(14)
    days = [NOW.date() - timedelta(days=13 - i) for i in range(14)]
    per = None
    if events is not None:
        per = {d: {k: 0 for k, _ in EV_COLORS} for d in days}
        for day, cls in events:
            if day in per:
                per[day][cls] += 1
    totals = [sum(per[d].values()) for d in days] if per else None
    total = sum(totals) if totals else 0
    lastday = next((d for d, n in zip(reversed(days), reversed(totals or []))
                    if n), None)
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
        [("rx", ("ACTIVE" if total else "IDLE") if per else "NO CARRIER",
          GREEN if total else (ICE if per else PINK)),
         ("source", "github public events", WHITE),
         ("scope", f"{GH_USER} · public", WHITE),
         ("window", "14d", WHITE),
         ("total", str(total) if per else "—", WHITE),
         ("peak", f"{max(totals)}/day" if per else "—", WHITE),
         ("last", lastday.isoformat() if lastday else "—", GREEN)], kcol=8)
    m.head.append(pulse_rings(X0 + 92, 120, BLUE, 3, 4, 44, 3.2))
    if per is None:
        failure(m, "SIGNAL SOURCE UNAVAILABLE", "github public events",
                "unreachable")
        m.build([f"rx --user {GH_USER} --window 14d", "no carrier"])
        return
    m.section("spectrum :: public events / day")
    top, hgt = m.y, 170
    base = top + hgt
    slot = (X1 - X0) / 14
    peak = max(totals) or 1
    g = [rect(X0, top - 8, X1 - X0, hgt + 16, fill="url(#grid)")]
    for k in range(1, 4):
        g.append(line(X0, base - hgt * k / 4, X1, base - hgt * k / 4,
                      stroke=LINE, sw=1, dash="2 6", opacity=0.7))
    for i, d in enumerate(days):
        x = X0 + i * slot + slot * 0.2
        w = slot * 0.6
        n = totals[i]
        if n:
            full = max(6, (hgt - 26) * n / peak)
            g.append(rect(_f(x), _f(base - full), _f(w), _f(full), fill=BLUE,
                          opacity=0.22, extra=' filter="url(#soft)"'))
            yb = base
            for cls, col in EV_COLORS:
                c = per[d][cls]
                if not c:
                    continue
                seg = full * c / n
                g.append(rect(_f(x), _f(yb - seg), _f(w), _f(seg), fill=col,
                              opacity=0.85))
                yb -= seg
            g.append(rect(_f(x), _f(base - full - 3), _f(w), 2, fill=WHITE))
            g.append(t(_f(x + w / 2), _f(base - full - 10), str(n), 16, WHITE,
                       "bold", anchor="middle"))
        else:
            g.append(rect(_f(x), base - 2, _f(w), 2, fill=LINE))
        g.append(t(_f(x + w / 2), base + 22, d.strftime("%d"), 15, ICE,
                   anchor="middle"))
    g.append(line(X0, base, X1, base, stroke=BLUE, sw=1.4))
    g.append(f'<rect x="{X0}" y="{top - 8}" width="3" height="{hgt + 8}" '
             f'fill="{GREEN}" opacity="0.5"><animate attributeName="x" '
             f'values="{X0};{X1 - 3}" dur="7s" repeatCount="indefinite"/>'
             f'</rect>')
    if not total:
        g.append(t((X0 + X1) / 2, top + hgt / 2, "NO SIGNAL IN WINDOW", 22,
                   PINK, "bold", anchor="middle"))
    m.raw("".join(g), hgt + 48)
    legend = []
    for cls, col in EV_COLORS:
        legend += [("■ ", col, "bold"), (cls.lower() + "  ", ICE)]
    m.line(*legend, size=16, gap=26)
    m.line((f"{days[0].isoformat()} → {days[-1].isoformat()}", ICE),
           size=17, gap=28)
    m.build([f"rx --user {GH_USER} --window 14d", "carrier: public events"])


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
         ("sync", stamp(), GREEN)],
        kcol=8)
    if not entries:
        failure(m, "ORBIT EMPTY", "data/orbit.json", "no bodies")
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
    m.gap(6)
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
        failure(m, "QUEUE EMPTY", "data/research-queue.json", "no jobs")
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
    m.line(("● OPEN   ○ QUEUED   ◇ PARKED", ICE), size=17, gap=28)
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
    abbr = NOW.tzname() or ""
    rows = [("sync", f"{NOW.strftime('%H:%M')} {abbr}", GREEN),
            ("zone", "Europe/Zurich", WHITE),
            ("offset", f"UTC{sign}{oh:02d}:{om:02d}", WHITE),
            ("date", stamp(), WHITE)]
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
    m.build(["date --tz Europe/Zurich", f"sync {NOW.strftime('%H:%M')} {abbr}"])


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
    m.line(("MODE   ", BLUE, "bold"), ("conceptual", WHITE), size=17, gap=28)
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
        failure(m, "ARCHIVE NOT MOUNTED", "public/", "missing")
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
    m.gap(6)
    m.build(["ls -la public/", "the archive is the public record"])


# ---------------------------------------------------------------- weather

# Zürich city-centre coordinates, used only to query the forecast API.
ZRH_LAT, ZRH_LON = 47.3769, 8.5417
WMO = {0: "CLEAR", 1: "MAINLY CLEAR", 2: "PARTLY CLOUDY", 3: "OVERCAST",
       45: "FOG", 48: "RIME FOG", 51: "LIGHT DRIZZLE", 53: "DRIZZLE",
       55: "DENSE DRIZZLE", 56: "FREEZING DRIZZLE", 57: "FREEZING DRIZZLE",
       61: "LIGHT RAIN", 63: "RAIN", 65: "HEAVY RAIN", 66: "FREEZING RAIN",
       67: "FREEZING RAIN", 71: "LIGHT SNOW", 73: "SNOW", 75: "HEAVY SNOW",
       77: "SNOW GRAINS", 80: "RAIN SHOWERS", 81: "RAIN SHOWERS",
       82: "HEAVY SHOWERS", 85: "SNOW SHOWERS", 86: "SNOW SHOWERS",
       95: "THUNDERSTORM", 96: "STORM + HAIL", 99: "STORM + HAIL"}


def sky_kind(code, is_day):
    if code in (0, 1):
        return "clear-day" if is_day else "clear-night"
    if code in (45, 48):
        return "fog"
    if code in (95, 96, 99):
        return "storm"
    if 71 <= code <= 77 or code in (85, 86):
        return "snow"
    if 51 <= code <= 67 or 80 <= code <= 82:
        return "rain"
    return "cloud"


def fetch_json(url, headers=None, timeout=20):
    try:
        req = urllib.request.Request(url, headers=headers or {
            "User-Agent": "zurich-node-refresh"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except (OSError, ValueError):
        return None


def weather_now():
    fields = ("temperature_2m,apparent_temperature,relative_humidity_2m,"
              "is_day,weather_code,cloud_cover,pressure_msl,wind_speed_10m,"
              "wind_direction_10m")
    data = fetch_json(
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={ZRH_LAT}&longitude={ZRH_LON}&current={fields}"
        "&timezone=Europe%2FZurich&wind_speed_unit=kmh")
    cur = (data or {}).get("current")
    if not isinstance(cur, dict) or "weather_code" not in cur:
        return None
    return cur


def compass(deg):
    pts = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return pts[int(((deg or 0) + 22.5) // 45) % 8]


CLOUD = r"""
         .-~~~~-.
   .-~~-(        )~-.
  (                  )~.
 (  .                   )
  '~-.______________.-~'
"""


def sky_art(kind, x, y, wind=10):
    """Original ASCII / pixel weather art for the left instrument bay."""
    g = []
    cloud_rows = CLOUD.strip("\n").split("\n")

    def cloud(cx, cy, color=ICE, drift=14, dur=14):
        rows = "".join(
            f'<text x="{_f(cx)}" y="{_f(cy + i * 17)}" font-size="15" '
            f'fill="{color}" xml:space="preserve">{r}</text>'
            for i, r in enumerate(cloud_rows))
        return (f'<g>{rows}<animateTransform attributeName="transform" '
                f'type="translate" values="0 0;{drift} 0;0 0" dur="{dur}s" '
                f'repeatCount="indefinite"/></g>')

    if kind == "clear-day":
        cx, cy = x + 112, y + 96
        rays = "".join(
            line(_f(cx + 52 * math.cos(math.radians(a))),
                 _f(cy + 52 * math.sin(math.radians(a))),
                 _f(cx + 74 * math.cos(math.radians(a))),
                 _f(cy + 74 * math.sin(math.radians(a))), stroke=GREEN, sw=3)
            for a in range(0, 360, 30))
        g.append(f'<g>{rays}<animateTransform attributeName="transform" '
                 f'type="rotate" values="0 {cx} {cy};360 {cx} {cy}" '
                 f'dur="48s" repeatCount="indefinite"/></g>')
        for i in range(-3, 4):
            for j in range(-3, 4):
                if i * i + j * j <= 10:
                    g.append(rect(cx + i * 12 - 5, cy + j * 12 - 5, 10, 10,
                                  fill=GREEN if i * i + j * j < 6 else PINK,
                                  opacity=0.9))
        g.append(f'<circle cx="{cx}" cy="{cy}" r="44" fill="{GREEN}" '
                 f'opacity="0.18" filter="url(#soft)"/>')
    elif kind == "clear-night":
        cx, cy = x + 120, y + 90
        g.append(f'<circle cx="{cx}" cy="{cy}" r="44" fill="{ICE}" '
                 f'opacity="0.9"/><circle cx="{cx + 20}" cy="{cy - 12}" '
                 f'r="40" fill="{VOID}"/>')
        g.append(f'<circle cx="{cx}" cy="{cy}" r="52" fill="{BLUE}" '
                 f'opacity="0.12" filter="url(#soft)"/>')
        for k, (sx, sy) in enumerate(((x + 30, y + 30), (x + 200, y + 40),
                                      (x + 60, y + 160), (x + 214, y + 150),
                                      (x + 170, y + 190), (x + 20, y + 110))):
            g.append(f'<rect x="{sx}" y="{sy}" width="4" height="4" '
                     f'fill="{WHITE}"><animate attributeName="opacity" '
                     f'values="1;0.2;1" dur="{2.4 + k * 0.7:.1f}s" '
                     f'repeatCount="indefinite"/></rect>')
    elif kind == "fog":
        for k in range(7):
            yy = y + 30 + k * 26
            g.append(f'<rect x="{x}" y="{yy}" width="230" height="10" '
                     f'fill="{ICE}" opacity="{0.12 + 0.04 * (k % 3):.2f}">'
                     f'<animateTransform attributeName="transform" '
                     f'type="translate" values="0 0;{18 if k % 2 else -18} 0;'
                     f'0 0" dur="{10 + k}s" repeatCount="indefinite"/></rect>')
    else:
        g.append(cloud(x + 4, y + 30, ICE if kind != "storm" else BLUE))
        if kind in ("rain", "storm"):
            for k in range(14):
                rx = x + 30 + (k * 37) % 190
                dl = (k * 0.29) % 1.2
                g.append(
                    f'<line x1="{rx}" y1="{y + 124}" x2="{rx - 4}" '
                    f'y2="{y + 138}" stroke="{BLUE}" stroke-width="1.6" '
                    f'opacity="0.8"><animateTransform attributeName="transform" '
                    f'type="translate" values="0 0;-12 70" dur="1.2s" '
                    f'begin="-{dl:.2f}s" repeatCount="indefinite"/></line>')
        if kind == "snow":
            for k in range(12):
                sx = x + 30 + (k * 41) % 190
                g.append(
                    f'<rect x="{sx}" y="{y + 124}" width="4" height="4" '
                    f'fill="{WHITE}"><animateTransform attributeName="transform" '
                    f'type="translate" values="0 0;8 36;-6 72" '
                    f'dur="{4 + k % 3}s" begin="-{k * 0.4:.1f}s" '
                    f'repeatCount="indefinite"/></rect>')
        if kind == "storm":
            g.append(f'<polyline points="{x + 130},{y + 120} {x + 112},{y + 158} '
                     f'{x + 128},{y + 158} {x + 108},{y + 200}" fill="none" '
                     f'stroke="{PINK}" stroke-width="3" opacity="0">'
                     f'<animate attributeName="opacity" values="0;0;1;0;0.7;0;0" '
                     f'keyTimes="0;0.8;0.81;0.83;0.84;0.86;1" dur="6s" '
                     f'repeatCount="indefinite"/></polyline>')
    # wind lines along the floor of the bay; speed follows the real wind
    dur = max(2.5, 12 - (wind or 0) / 4)
    for k in range(3):
        yy = y + 214 + k * 8
        g.append(f'<line x1="{x}" y1="{yy}" x2="{x + 60}" y2="{yy}" '
                 f'stroke="{LINE}" stroke-width="1.4" stroke-dasharray="10 8">'
                 f'<animateTransform attributeName="transform" type="translate" '
                 f'values="0 0;170 0" dur="{dur + k:.1f}s" '
                 f'repeatCount="indefinite"/></line>')
    return "".join(g)


def weather_signal():
    m = Dyn("dynamic/weather-signal.svg", BLUE,
            "weather.signal :: atmospheric-uplink", "zürich", "~",
            "weather --now")
    m.start(116)
    top = m.y
    cur = weather_now()
    rx = X0 + 272
    g = [rect(X0 - 4, top - 18, 250, 252, fill="url(#grid)", opacity=0.6),
         f'<rect x="{X0 - 4}" y="{top - 18}" width="250" height="252" '
         f'fill="none" stroke="{LINE}" stroke-width="1"/>']
    g.append(t(rx, top + 6, "ZÜRICH, CH", 22, PINK, "bold"))
    g.append(t(rx, top + 26, "-" * 14, 19, LINE))
    if cur is None:
        g.append(sky_art("cloud", X0, top - 6))
        g.append(t(rx, top + 70, "[ !! ] SOURCE OFFLINE", 20, PINK, "bold"))
        for i, (k, v, c) in enumerate((("source", "open-meteo", WHITE),
                                       ("state", "no signal", PINK),
                                       ("zone", "Europe/Zurich", WHITE))):
            y = top + 110 + i * 28
            g.append(t(rx, y, f"{k}:", 18, BLUE, "bold") +
                     t(_f(rx + 8 * 18 * CW), y, v, 18, c))
        m.raw("".join(g), 252)
        m.build(["weather --now", "uplink: no signal"])
        return
    code = int(cur.get("weather_code", 3))
    is_day = bool(cur.get("is_day", 1))
    kind = sky_kind(code, is_day)
    temp = round(cur.get("temperature_2m", 0))
    feels = round(cur.get("apparent_temperature", temp))
    wind = round(cur.get("wind_speed_10m", 0))
    obs = datetime.fromisoformat(cur["time"]).replace(tzinfo=TZ) \
        if cur.get("time") else NOW
    g.append(sky_art(kind, X0, top - 6, wind))
    cond = WMO.get(code, "UNKNOWN")
    g.append(t(rx, top + 64, cond, 26 if len(cond) <= 13 else 21, WHITE, "bold"))
    rows = [("temp", f"{temp}°C", GREEN),
            ("feels", f"{feels}°C", WHITE),
            ("humidity", f"{round(cur.get('relative_humidity_2m', 0))}%", WHITE),
            ("wind", f"{wind} km/h {compass(cur.get('wind_direction_10m'))}",
             WHITE),
            ("pressure", f"{round(cur.get('pressure_msl', 0))} hPa", WHITE),
            ("cloud", f"{round(cur.get('cloud_cover', 0))}%", WHITE),
            ("cycle", "DAY" if is_day else "NIGHT", PINK)]
    for i, (k, v, c) in enumerate(rows):
        y = top + 96 + i * 22
        g.append(t(rx, y, f"{k}:", 17, BLUE, "bold") +
                 t(_f(rx + 10 * 17 * CW), y, v, 17, c))
    # thermometer: fill follows the real temperature on a -15..35 °C scale
    tx, ty, th = X1 - 18, top + 40, 150
    frac = min(1, max(0, (temp + 15) / 50))
    g.append(rect(tx, ty, 10, th, fill=VOID, stroke=LINE, sw=1.2))
    g.append(rect(tx + 2, _f(ty + th - (th - 4) * frac - 2), 6,
                  _f((th - 4) * frac), fill=mix(BLUE, PINK, frac)))
    for k in range(6):
        g.append(line(tx - 6, ty + k * th / 5, tx - 1, ty + k * th / 5,
                      stroke=LINE, sw=1))
    m.raw("".join(g), 252)
    m.section("uplink")
    m.line(("SYNC     ", BLUE, "bold"),
           (obs.strftime("%H:%M ") + (obs.tzname() or NOW.tzname() or ""),
            GREEN), ("   SOURCE  ", BLUE, "bold"), ("open-meteo", WHITE))
    m.build(["weather --now", f"{cond.lower()} · {temp}°C"])


# ---------------------------------------------------------------- traffic

REPO = os.environ.get("NODE_REPO", "snowyarch/snowyarch")


def traffic():
    """14-day traffic for the profile repository. Prefers the optional
    PROFILE_TRAFFIC_TOKEN (fine-grained, Administration: read); falls back
    to GITHUB_TOKEN. Tokens are only ever sent as a header."""
    headers = {"Accept": "application/vnd.github+json",
               "User-Agent": "zurich-node-refresh",
               "X-GitHub-Api-Version": "2022-11-28"}
    token = os.environ.get("PROFILE_TRAFFIC_TOKEN") or \
        os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    base = f"https://api.github.com/repos/{REPO}/traffic/"
    views = fetch_json(base + "views", headers)
    if not isinstance(views, dict) or "views" not in views:
        return None
    clones = fetch_json(base + "clones", headers) or {}
    refs = fetch_json(base + "popular/referrers", headers) or []
    paths = fetch_json(base + "popular/paths", headers) or []
    return views, clones, refs if isinstance(refs, list) else [], \
        paths if isinstance(paths, list) else []


def node_traffic():
    m = Module("dynamic/node-traffic.svg", PINK,
               "node.traffic :: passive-sensor", "14d", "~",
               "rx --passive --window 14d")
    data = traffic()
    days = [NOW.date() - timedelta(days=13 - i) for i in range(14)]
    if data:
        views, clones, refs, paths = data
        vday = {v["timestamp"][:10]: (v.get("count", 0), v.get("uniques", 0))
                for v in views.get("views", [])}
        cday = {c["timestamp"][:10]: c.get("count", 0)
                for c in clones.get("clones", [])}
        series = [vday.get(d.isoformat(), (0, 0)) for d in days]
        cser = [cday.get(d.isoformat(), 0) for d in days]
        top_ref = refs[0]["referrer"][:20] if refs else "—"
        top_path = paths[0]["path"][:22] if paths else "—"
        info = [("window", "14d", WHITE),
                ("views", str(views.get("count", 0)), GREEN),
                ("unique", str(views.get("uniques", 0)), WHITE),
                ("clones", str(clones.get("count", 0)), WHITE),
                ("cloners", str(clones.get("uniques", 0)), WHITE),
                ("channel", top_ref, PINK), ("path", top_path, WHITE),
                ("sync", stamp(), GREEN)]
    else:
        info = [("window", "14d", WHITE), ("views", "—", WHITE),
                ("unique", "—", WHITE), ("clones", "—", WHITE),
                ("source", "repo traffic", WHITE), ("sync", stamp(), ICE)]
    m.neofetch(ascii_rows(r"""
     ))       .-.       ((
    )))     ( <> )     (((
     ))       '-'       ((
               |
              /|\
           __/ | \__
          /    |    \
        RX    NODE    TX
       ====================
"""), (PINK, BLUE), "rx@node-traffic", info, kcol=9)
    total = data[0].get("count", 0) if data else 0
    m.head.append(pulse_rings(X0 + 104, 132, PINK,
                              min(5, 2 + total // 25) if data else 1, 6, 46,
                              3.0))
    if not data:
        failure(m, "TRAFFIC SOURCE OFFLINE", "repo traffic", "no signal")
        m.build(["rx --passive --window 14d", "sensor idle"])
        return
    m.section("inbound :: views / day")
    top, hgt = m.y, 150
    base = top + hgt
    slot = (X1 - X0) / 13
    peak = max([c for c, _ in series] + [1])
    g = [rect(X0, top - 8, X1 - X0, hgt + 16, fill="url(#grid)")]
    for k in range(1, 4):
        g.append(line(X0, base - hgt * k / 4, X1, base - hgt * k / 4,
                      stroke=LINE, sw=1, dash="2 6", opacity=0.7))
    pts = [(X0 + i * slot, base - (hgt - 24) * c / peak)
           for i, (c, _) in enumerate(series)]
    area = (f"M{_f(pts[0][0])} {base} " +
            " ".join(f"L{_f(x)} {_f(y)}" for x, y in pts) +
            f" L{_f(pts[-1][0])} {base} Z")
    g.append(f'<path d="{area}" fill="{PINK}" opacity="0.12"/>')
    g.append(f'<polyline points="{" ".join(f"{_f(x)},{_f(y)}" for x, y in pts)}" '
             f'fill="none" stroke="{PINK}" stroke-width="2" opacity="0.35" '
             f'filter="url(#soft)"/>')
    g.append(f'<polyline points="{" ".join(f"{_f(x)},{_f(y)}" for x, y in pts)}" '
             f'fill="none" stroke="{PINK}" stroke-width="1.8"/>')
    upeak = max([u for _, u in series] + [1])
    for i, (c, u) in enumerate(series):
        x = X0 + i * slot
        uy = base - (hgt - 24) * u / max(peak, upeak)
        if u:
            g.append(f'<circle cx="{_f(x)}" cy="{_f(uy)}" r="3.5" '
                     f'fill="{GREEN}"/>')
        if cser[i]:
            ch = min(30, 6 + cser[i] * 4)
            g.append(rect(_f(x - 3), _f(base - ch), 6, _f(ch), fill=BLUE,
                          opacity=0.8))
        if i % 2 == 0:
            g.append(t(_f(x), base + 22, days[i].strftime("%d"), 15, ICE,
                       anchor="middle"))
    g.append(line(X0, base, X1, base, stroke=PINK, sw=1.4))
    # an inbound packet riding the waveform
    path = "M" + " L".join(f"{_f(x)} {_f(y)}" for x, y in pts)
    g.append(f'<circle r="4" fill="{WHITE}"><animateMotion dur="9s" '
             f'repeatCount="indefinite" path="{path}"/></circle>')
    if not total:
        g.append(t((X0 + X1) / 2, top + hgt / 2, "NO INBOUND SIGNAL", 22,
                   PINK, "bold", anchor="middle"))
    m.raw("".join(g), hgt + 48)
    m.line(("━ ", PINK, "bold"), ("views  ", ICE), ("● ", GREEN, "bold"),
           ("unique  ", ICE), ("▮ ", BLUE, "bold"), ("clones", ICE),
           size=16, gap=26)
    m.line((f"{days[0].isoformat()} → {days[-1].isoformat()}", ICE),
           size=17, gap=28)
    m.build(["rx --passive --window 14d", "signals arriving at the node"])


# ---------------------------------------------------------------- radio

PLAYLIST_RE = re.compile(
    r"^https://open\.spotify\.com/(?:intl-[a-z]{2}(?:-[A-Za-z]{2})?/)?"
    r"playlist/[A-Za-z0-9]{22}(?:\?\S*)?$")
TRACK_RE = re.compile(
    r"^https://open\.spotify\.com/(?:intl-[a-z]{2}(?:-[A-Za-z]{2})?/)?"
    r"track/[A-Za-z0-9]{22}(?:\?\S*)?$")


def radio_config():
    """Station config from data/radio.json; the playlist URL is only
    accepted when it is a real public Spotify playlist link."""
    cfg = load_json("radio.json") or {}
    url = str(cfg.get("playlist_url", "")).strip()
    rotation = []
    for r in (cfg.get("rotation") or [])[:5]:
        title = str(r.get("title", "")).strip()
        artist = str(r.get("artist", "")).strip()
        link = str(r.get("spotify_url", "")).strip()
        if title and artist and TRACK_RE.match(link):
            rotation.append((title, artist))
    return (str(cfg.get("station", "")).strip() or "AFTERHOURS FM",
            url if PLAYLIST_RE.match(url) else None, rotation)


def playlist_title(url):
    """Optional: public oEmbed title for the configured playlist. Any
    failure simply leaves the station on its local config."""
    data = fetch_json("https://open.spotify.com/oembed?url=" +
                      urllib.parse.quote(url, safe=""))
    title = (data or {}).get("title") if isinstance(data, dict) else None
    return str(title).strip()[:26] if title else None


def clip(s, n):
    return s if len(s) <= n else s[:n - 1] + "…"


def radio_afterhours():
    m = Module("dynamic/radio-afterhours.svg", PINK,
               "radio.afterhours :: frequency-deck", "fm", "~",
               "tune afterhours.fm")
    station, url, rotation = radio_config()
    title = playlist_title(url) if url else None
    online = url is not None
    m.neofetch(ascii_rows(r"""
      .--------------.
  ))  | AFTERHOURS FM |  ((
 )))  | .----------. |  (((
  ))  | | |||||||| | |  ((
      | '----------' |
      | (o)      (o) |
      '------.-------'
             |
        ==========
"""), (PINK, BLUE), "radio@afterhours",
        [("station", clip(station, 20), WHITE),
         ("source", "spotify", WHITE),
         ("mode", "playlist rotation", WHITE),
         ("signal", "ONLINE" if online else "UNCONFIGURED",
          GREEN if online else PINK),
         ("playlist", clip(title, 20) if title else "—", WHITE),
         ("rotation", f"{len(rotation)} / 5", WHITE),
         ("sync", stamp(), GREEN if online else ICE)], kcol=10)
    m.head.append(pulse_rings(X0 + 110, 150, PINK if online else LINE,
                              3 if online else 1, 8, 52, 3.4))

    # tuning dial: a scale with a needle that sweeps the band
    m.section("tuner")
    top = m.y
    dl, dr = X0 + 10, X1 - 10
    g = [rect(X0, top - 16, X1 - X0, 74, fill="#0B1220", stroke=LINE, sw=1.2)]
    for k in range(0, 41):
        x = dl + (dr - dl) * k / 40
        major = k % 4 == 0
        g.append(line(_f(x), top + 26 - (14 if major else 7), _f(x), top + 26,
                      stroke=ICE if major else LINE, sw=1.4 if major else 1))
        if major:
            g.append(t(_f(x), top + 48, str(88 + k // 2), 15, ICE,
                       anchor="middle"))
    g.append(line(dl, top + 26, dr, top + 26, stroke=LINE, sw=1))
    nx = dl + (dr - dl) * 0.62
    sweep = ('<animateTransform attributeName="transform" type="translate" '
             'values="0 0;-60 0;24 0;0 0" dur="14s" '
             'repeatCount="indefinite"/>' if online else "")
    g.append(f'<g>{line(_f(nx), top - 10, _f(nx), top + 34, stroke=PINK, sw=2.4)}'
             f'<rect x="{_f(nx - 5)}" y="{top - 14}" width="10" height="6" '
             f'fill="{PINK}"/>{sweep}</g>')
    m.raw("".join(g), 78)

    # spectrum analyser
    m.section("spectrum")
    top = m.y
    hgt, n = 96, 28
    base = top + hgt
    slot = (X1 - X0) / n
    g = [rect(X0, top - 10, X1 - X0, hgt + 18, fill="url(#grid)")]
    for i in range(n):
        x = X0 + i * slot + slot * 0.18
        w = slot * 0.64
        shape = 0.35 + 0.65 * abs(math.sin(i * 0.55 + 0.6)) * (1 - i / (n * 1.4))
        h0 = max(6, hgt * shape * (0.85 if online else 0.12))
        col = mix(BLUE, PINK, i / (n - 1))
        anim = ""
        if online:
            lo, hi = max(4, h0 * 0.35), h0
            vals = f"{_f(lo)};{_f(hi)};{_f(lo * 1.4)};{_f(hi * 0.8)};{_f(lo)}"
            ys = ";".join(_f(base - float(v)) for v in vals.split(";"))
            dur = f"{1.6 + (i % 5) * 0.23:.2f}s"
            anim = (f'<animate attributeName="height" values="{vals}" '
                    f'dur="{dur}" repeatCount="indefinite"/>'
                    f'<animate attributeName="y" values="{ys}" dur="{dur}" '
                    f'repeatCount="indefinite"/>')
        g.append(f'<rect x="{_f(x)}" y="{_f(base - h0)}" width="{_f(w)}" '
                 f'height="{_f(h0)}" fill="{col}" '
                 f'opacity="{0.85 if online else 0.35}">{anim}</rect>')
    g.append(line(X0, base, X1, base, stroke=PINK, sw=1.4))
    if not online:
        g.append(t((X0 + X1) / 2, top + hgt / 2, "STATION UNCONFIGURED", 22,
                   PINK, "bold", anchor="middle"))
    m.raw("".join(g), hgt + 30)

    if rotation:
        m.section("rotation")
        top = m.y
        rows = len(rotation)
        sel = (f'<rect x="{X0}" y="{top - 20}" width="{X1 - X0}" height="28" '
               f'fill="{PINK}" opacity="0.12"><animate attributeName="y" '
               f'values="{";".join(str(top - 20 + k * 30) for k in range(rows))}" '
               f'dur="{rows * 3}s" calcMode="discrete" '
               f'repeatCount="indefinite"/></rect>')
        m.raw(sel, 0)
        for k, (ttl, art) in enumerate(rotation):
            m.line((f"CH{k + 1:02d}  ", GREEN, "bold"),
                   (clip(art, 18) + " — ", ICE), (clip(ttl, 24), WHITE),
                   gap=30)
    else:
        # tape deck: reels turn while the station is configured
        m.section("deck")
        top = m.y
        g = [rect(X0 + 90, top - 14, 468, 120, fill="#0B1220", stroke=LINE,
                  sw=1.2),
             rect(X0 + 180, top + 64, 288, 26, fill=VOID, stroke=LINE, sw=1)]
        for cx in (X0 + 230, X0 + 418):
            cy = top + 34
            spokes = "".join(
                line(_f(cx + 8 * math.cos(math.radians(a))),
                     _f(cy + 8 * math.sin(math.radians(a))),
                     _f(cx + 30 * math.cos(math.radians(a))),
                     _f(cy + 30 * math.sin(math.radians(a))),
                     stroke=ICE, sw=2) for a in (0, 120, 240))
            spin = (f'<animateTransform attributeName="transform" '
                    f'type="rotate" values="0 {cx} {cy};360 {cx} {cy}" '
                    f'dur="6s" repeatCount="indefinite"/>' if online else "")
            g.append(f'<circle cx="{cx}" cy="{cy}" r="38" fill="none" '
                     f'stroke="{PINK}" stroke-width="1.6"/>'
                     f'<circle cx="{cx}" cy="{cy}" r="6" fill="{PINK}"/>'
                     f'<g>{spokes}{spin}</g>')
        g.append(line(X0 + 268, top + 66, X0 + 380, top + 66, stroke=ICE,
                      sw=1.2))
        g.append(t(X0 + 324, top + 82, "SIDE A", 14, ICE, anchor="middle"))
        for k, c in enumerate((GREEN if online else LINE, PINK, BLUE)):
            anim = ('<animate attributeName="opacity" values="1;0.3;1" '
                    f'dur="{2 + k * 0.7:.1f}s" repeatCount="indefinite"/>'
                    if online and k == 0 else "")
            g.append(f'<circle cx="{X0 + 116}" cy="{top + 4 + k * 22}" r="4.5" '
                     f'fill="{c}">{anim}</circle>')
        m.raw("".join(g), 124)

    m.line(("STATION  ", BLUE, "bold"), (clip(station, 18), WHITE),
           ("   SIGNAL  ", BLUE, "bold"),
           ("ONLINE" if online else "UNCONFIGURED", GREEN if online else PINK,
            "bold"), size=18, gap=30)
    m.build(["tune afterhours.fm",
             "afterhours fm" if online else "station unconfigured"])


def main():
    DYN.mkdir(parents=True, exist_ok=True)
    for fn in (boot_sequence, transmission_log, signal_activity,
               node_traffic, currently_orbiting, research_queue, node_clock,
               weather_signal, signal_map, signal_archive, radio_afterhours):
        fn()
    for p in sorted(DYN.glob("*.svg")):
        print(f"dynamic/{p.name:28} {p.stat().st_size:>7} bytes")


if __name__ == "__main__":
    main()
