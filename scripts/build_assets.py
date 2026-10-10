#!/usr/bin/env python3
"""Builds assets/hero.svg and assets/status.svg in the style of alexradu.co.

status.svg is live: recent repos, 2026 goals (edit scripts/goals.json), and a
30 day push graph. The Quizzr goal reads the user count from the
<!--QUIZZR-USERS--> marker in README.md, so whatever updates that marker also
updates the bar.

usage: python3 scripts/build_assets.py [--demo]
env:   GH_USER (default alextheradu), GITHUB_TOKEN (optional, raises rate limit)
"""
import html
import json
import os
import re
import sys
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
USER = os.environ.get("GH_USER", "alextheradu")

# palette copied from alexradu.co
BG, BORDER, BAR_BG = "#0d0f11", "#23272b", "#1c1f22"
WHITE, TEXT, SOFT = "#f0f1f2", "#b7bcc1", "#9aa1a8"
MUTED, DIM, DARK = "#6d7378", "#3a4045", "#444a4f"
HEAD, GREEN = "#7f868c", "#00ff1e"

STYLE = (
    "<style>"
    ".s{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif}"
    ".m{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}"
    "</style>"
)
W = 900
PAD = 28


def esc(s):
    return html.escape(str(s), quote=True)


def trunc(s, n):
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[: n - 3].rstrip() + "..."


def ago(then, now):
    secs = (now - then).total_seconds()
    for name, size in (("d", 86400), ("h", 3600), ("m", 60)):
        if secs >= size:
            return f"{int(secs // size)}{name} ago", secs
    return "just now", secs


def parse(iso):
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def get_json(url):
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-assets"},
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.load(r)


def fetch_live():
    repos = get_json(f"https://api.github.com/users/{USER}/repos?sort=pushed&per_page=30&type=owner")
    events = []
    for page in (1, 2, 3):
        chunk = get_json(f"https://api.github.com/users/{USER}/events/public?per_page=100&page={page}")
        events += chunk
        if len(chunk) < 100:
            break
    return repos, events


def demo_data(now):
    def iso(**k):
        return (now - timedelta(**k)).strftime("%Y-%m-%dT%H:%M:%SZ")

    repos = [
        {"name": "command", "description": "self-hostable team management PWA for FRC teams", "language": "TypeScript", "fork": False, "archived": False, "pushed_at": iso(hours=3)},
        {"name": "shahlab-nf-scatac", "description": "nextflow pipeline for demultiplexing DATAC reads", "language": "Nextflow", "fork": False, "archived": False, "pushed_at": iso(days=2)},
        {"name": "curator", "description": "AI chatbot and assistant for FIRST Robotics teams", "language": "TypeScript", "fork": False, "archived": False, "pushed_at": iso(days=4)},
        {"name": "portfolio-v3", "description": "personal site", "language": "JavaScript", "fork": False, "archived": False, "pushed_at": iso(days=9)},
        {"name": "reelbot", "description": "instagram reels to slack", "language": "Python", "fork": False, "archived": False, "pushed_at": iso(days=15)},
        {"name": "phhshack.club", "description": None, "language": "JavaScript", "fork": False, "archived": False, "pushed_at": iso(days=21)},
    ]
    pattern = [3, 0, 2, 5, 1, 0, 0, 4, 2, 6, 3, 0, 1, 2, 0, 0, 7, 4, 2, 1, 0, 3, 5, 2, 0, 1, 4, 3, 6, 2]
    events = [
        {"type": "PushEvent", "created_at": (now - timedelta(days=29 - i)).strftime("%Y-%m-%dT12:00:00Z")}
        for i, n in enumerate(pattern)
        for _ in range(n)
    ]
    return repos, events


def quizzr_count():
    try:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        m = re.search(r"<!--QUIZZR-USERS-->(\d+)<!--/QUIZZR-USERS-->", text)
        return int(m.group(1)) if m else None
    except OSError:
        return None


def frame(height, label, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height}" width="{W}" height="{height}" role="img" aria-label="{esc(label)}">\n'
        f"{STYLE}\n"
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{height - 1}" rx="12" fill="{BG}" stroke="{BORDER}"/>\n'
        f"{body}\n</svg>\n"
    )


def build_hero():
    nav = " / ".join(["about", "skills", "projects", "goals"])
    body = f"""
<text class="s" x="{PAD}" y="48" font-size="15" fill="{SOFT}">// portfolio :O</text>
<text class="s" x="{W - PAD}" y="48" font-size="14" fill="{MUTED}" text-anchor="end">{esc(nav)}</text>
<text class="s" x="{PAD}" y="128" font-size="54" font-weight="700" fill="{WHITE}">Alex Radu<tspan fill="{GREEN}">_<animate attributeName="fill-opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1.2s" repeatCount="indefinite"/></tspan></text>
<text class="s" x="{PAD}" y="164" font-size="18" fill="{TEXT}">full stack web dev and hardware specialist (from nj!)</text>
<text class="s" x="{PAD}" y="196" font-size="15" fill="{MUTED}">i build cool apps (i think) like curator, my frc team's scouting app, and more!</text>
"""
    return frame(224, "Alex Radu, full stack web dev and hardware specialist from NJ", body)


def h2(y, text, right=None):
    out = f'<text class="s" x="{PAD}" y="{y}" font-size="15" font-weight="600" fill="{HEAD}">{esc(text)}</text>'
    if right:
        out += f'<text class="m" x="{W - PAD}" y="{y}" font-size="12" fill="{DIM}" text-anchor="end">{esc(right)}</text>'
    return out


def build_status(repos, events, goals, now):
    parts = []
    parts.append(f'<text class="s" x="{PAD}" y="42" font-size="15" fill="{SOFT}">// live</text>')
    parts.append(
        f'<text class="m" x="{W - PAD}" y="42" font-size="12" fill="{DIM}" text-anchor="end">synced {now.strftime("%Y-%m-%d %H:%M")} utc</text>'
    )

    # shipping
    parts.append(h2(88, "shipping", "most recent pushes"))
    rows = []
    for repo in repos:
        if repo.get("fork") or repo.get("archived") or repo["name"].lower() == USER.lower():
            continue
        rows.append(repo)
        if len(rows) == 6:
            break
    top = 104
    for i, repo in enumerate(rows):
        base = top + 28
        when, secs = ago(parse(repo["pushed_at"]), now)
        fresh = secs < 48 * 3600
        parts.append(f'<text class="m" x="{PAD}" y="{base}" font-size="12" fill="{DIM}">{i + 1:02d}</text>')
        parts.append(f'<text class="s" x="{PAD + 34}" y="{base}" font-size="16" fill="{WHITE}">{esc(trunc(repo["name"], 22))}</text>')
        lang = repo.get("language")
        if lang:
            cw = len(lang) * 7 + 14
            parts.append(f'<rect x="{PAD + 250}" y="{base - 14}" width="{cw}" height="20" rx="3" fill="none" stroke="{BORDER}"/>')
            parts.append(f'<text class="m" x="{PAD + 257}" y="{base}" font-size="11" fill="{MUTED}">{esc(lang.lower())}</text>')
        desc = trunc(repo.get("description") or "", 46)
        if desc:
            parts.append(f'<text class="s" x="{PAD + 370}" y="{base}" font-size="13" fill="{MUTED}">{esc(desc)}</text>')
        parts.append(
            f'<text class="m" x="{W - PAD}" y="{base}" font-size="12" fill="{GREEN if fresh else MUTED}" text-anchor="end">{esc(when)}</text>'
        )
        if i < len(rows) - 1:
            parts.append(f'<line x1="{PAD}" y1="{top + 44}" x2="{W - PAD}" y2="{top + 44}" stroke="{BAR_BG}"/>')
        top += 44
    if not rows:
        parts.append(
            f'<text class="s" x="{PAD}" y="{top + 28}" font-size="13" fill="{MUTED}">waiting for the first sync. run the refresh workflow once from the actions tab.</text>'
        )
        top += 44
    y = top + 40

    # goals
    parts.append(h2(y, "personal goals", "2026"))
    top = y + 16
    for g in goals:
        want = g["want"]
        if g.get("live") == "quizzr":
            have = quizzr_count()
            if have is None:
                have = g.get("have", 0)
        else:
            have = g["have"]
        pct = max(0, min(100, round(have * 100 / want)))
        unit = f" {g['unit']}" if g.get("unit") else ""
        parts.append(f'<text class="s" x="{PAD}" y="{top + 22}" font-size="15" fill="{WHITE}">{esc(g["name"])}</text>')
        parts.append(f'<text class="m" x="{W - PAD}" y="{top + 22}" font-size="12" fill="{MUTED}" text-anchor="end">{have}/{want}{esc(unit)}</text>')
        bw = W - 2 * PAD
        parts.append(f'<rect x="{PAD}" y="{top + 32}" width="{bw}" height="6" rx="3" fill="{BAR_BG}"/>')
        if pct:
            parts.append(f'<rect x="{PAD}" y="{top + 32}" width="{bw * pct / 100:.1f}" height="6" rx="3" fill="{GREEN}"/>')
        parts.append(f'<text class="s" x="{PAD}" y="{top + 58}" font-size="12" fill="{MUTED}">{pct}% complete</text>')
        top += 66
    y = top + 36

    # push graph
    days = [(now - timedelta(days=29 - i)).date() for i in range(30)]
    counts = Counter(parse(e["created_at"]).date() for e in events if e.get("type") == "PushEvent")
    series = [counts.get(d, 0) for d in days]
    total, peak = sum(series), max(series + [1])
    parts.append(h2(y, "pushes, last 30 days", f"{total} pushes"))
    gtop, gh = y + 18, 64
    slot = (W - 2 * PAD) / 30
    bw = slot - 6
    for i, n in enumerate(series):
        x = PAD + i * slot
        if n == 0:
            parts.append(f'<rect x="{x:.1f}" y="{gtop + gh - 3}" width="{bw:.1f}" height="3" rx="1.5" fill="{BAR_BG}"/>')
        else:
            h = max(6, gh * n / peak)
            op = 0.35 + 0.65 * n / peak
            parts.append(f'<rect x="{x:.1f}" y="{gtop + gh - h:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="2" fill="{GREEN}" fill-opacity="{op:.2f}"/>')
    parts.append(f'<text class="m" x="{PAD}" y="{gtop + gh + 20}" font-size="11" fill="{DIM}">{days[0].strftime("%b %d").lower()}</text>')
    parts.append(f'<text class="m" x="{W - PAD}" y="{gtop + gh + 20}" font-size="11" fill="{DIM}" text-anchor="end">today</text>')

    height = gtop + gh + 20 + 28
    label = f"Live status: {len(rows)} recent repos, personal goals for 2026, and {total} pushes in the last 30 days"
    return frame(height, label, "\n".join(parts))


def main():
    now = datetime.now(timezone.utc)
    demo = "--demo" in sys.argv
    out = Path(os.environ.get("OUT_DIR", ROOT / "assets"))
    out.mkdir(parents=True, exist_ok=True)
    if demo:
        repos, events = demo_data(now)
    elif "--offline" in sys.argv:
        repos, events = [], []  # placeholder panel until the first real sync
    else:
        repos, events = fetch_live()
    goals = json.loads((ROOT / "scripts" / "goals.json").read_text(encoding="utf-8"))
    (out / "hero.svg").write_text(build_hero(), encoding="utf-8")
    (out / "status.svg").write_text(build_status(repos, events, goals, now), encoding="utf-8")
    print("wrote", out / "hero.svg", "and", out / "status.svg")


if __name__ == "__main__":
    main()