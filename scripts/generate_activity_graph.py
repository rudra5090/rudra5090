import json
import os
import urllib.request
from datetime import date, timedelta
from xml.sax.saxutils import escape

USERNAME = "rudra5090"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
DAYS = 31

query = """
query($login:String!, $from:DateTime!, $to:DateTime!) {
  user(login:$login) {
    contributionsCollection(from:$from, to:$to) {
      contributionCalendar {
        weeks {
          contributionDays { date contributionCount }
        }
      }
    }
  }
}
"""

today = date.today()
start = today - timedelta(days=DAYS - 1)
variables = {
    "login": USERNAME,
    "from": f"{start.isoformat()}T00:00:00Z",
    "to": f"{today.isoformat()}T23:59:59Z",
}

req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": query, "variables": variables}).encode(),
    headers={
        "Authorization": f"bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": USERNAME,
    },
)

with urllib.request.urlopen(req) as response:
    payload = json.load(response)

if payload.get("errors"):
    raise RuntimeError(payload["errors"])

days = []
for week in payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]:
    days.extend(week["contributionDays"])

counts = {d["date"]: d["contributionCount"] for d in days}
values = [counts.get((start + timedelta(days=i)).isoformat(), 0) for i in range(DAYS)]
max_count = max(values or [0])

width, height = 1000, 250
left, right, top, bottom = 55, 25, 55, 55
plot_w = width - left - right
plot_h = height - top - bottom
step = plot_w / max(1, DAYS - 1)

points = []
for i, value in enumerate(values):
    x = left + i * step
    y = top + plot_h - (value / max_count * plot_h if max_count else 0)
    points.append((x, y))

polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
area = f"{left},{top + plot_h} " + polyline + f" {left + plot_w},{top + plot_h}"

circles = "".join(
    f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="#58a6ff"><title>{escape(str(values[i]))} contributions on {start + timedelta(days=i)}</title></circle>'
    for i, (x, y) in enumerate(points)
)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" rx="14" fill="#0d1117"/>
<text x="{left}" y="30" fill="#f0f6fc" font-family="Arial,sans-serif" font-size="20" font-weight="700">Rudra's Build History</text>
<text x="{width-right}" y="30" text-anchor="end" fill="#8b949e" font-family="Arial,sans-serif" font-size="13">Last {DAYS} days • GitHub contributions</text>
<polygon points="{area}" fill="#58a6ff" opacity="0.12"/>
<polyline points="{polyline}" fill="none" stroke="#58a6ff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
{circles}
<line x1="{left}" y1="{top+plot_h}" x2="{left+plot_w}" y2="{top+plot_h}" stroke="#30363d"/>
<text x="{left}" y="{height-18}" fill="#8b949e" font-family="Arial,sans-serif" font-size="12">{start}</text>
<text x="{left+plot_w}" y="{height-18}" text-anchor="end" fill="#8b949e" font-family="Arial,sans-serif" font-size="12">{today}</text>
</svg>'''

os.makedirs(".", exist_ok=True)
with open("activity-graph.svg", "w", encoding="utf-8") as f:
    f.write(svg)
print(f"Generated activity graph: {sum(values)} total contributions across {DAYS} days")
