from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen
import re

ROOT = Path(__file__).resolve().parents[1]
USERNAME = "cordukfurkanemre"
YEAR = date.today().year


class ContributionParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = {}
        self.ids = {}
        self.tooltip = None

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if values.get("data-date") and values.get("data-level") is not None:
            key = values["data-date"]
            self.days[key] = {"level": int(values["data-level"]), "count": 0}
            self.ids[values["id"]] = key
        elif tag == "tool-tip":
            self.tooltip = values.get("for")

    def handle_data(self, text):
        if self.tooltip in self.ids:
            match = re.search(r"(No|[\d,]+) contributions?", text)
            if match:
                value = 0 if match[1] == "No" else int(match[1].replace(",", ""))
                self.days[self.ids[self.tooltip]]["count"] = value

    def handle_endtag(self, tag):
        if tag == "tool-tip":
            self.tooltip = None


def fetch():
    url = f"https://github.com/users/{USERNAME}/contributions?from={YEAR}-01-01&to={YEAR}-12-31"
    request = Request(url, headers={"User-Agent": "animated-profile-calendar"})
    with urlopen(request, timeout=30) as response:
        parser = ContributionParser()
        parser.feed(response.read().decode("utf-8"))
    if len(parser.days) < 360:
        raise RuntimeError("GitHub returned an incomplete contribution calendar")
    return parser.days


def render(days):
    palette = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
    dates = [date.fromisoformat(value) for value in sorted(days)]
    first = date(YEAR, 1, 1)
    start = first.fromordinal(first.toordinal() - ((first.weekday() + 1) % 7))
    step, cell, left, top = 15, 12, 48, 57
    columns = 53
    total = sum(value["count"] for value in days.values())
    parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="860" height="190" viewBox="0 0 860 190" role="img">
<title>{total} contributions in {YEAR}</title>
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#0d1117"/><stop offset="1" stop-color="#111827"/></linearGradient>
  <linearGradient id="beam"><stop stop-color="#69f0a0" stop-opacity="0"/><stop offset=".5" stop-color="#69f0a0" stop-opacity=".9"/><stop offset="1" stop-color="#69f0a0" stop-opacity="0"/></linearGradient>
  <filter id="blur"><feGaussianBlur stdDeviation="5"/></filter>
</defs>
<style>
text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}
@keyframes cell{{0%{{opacity:0;transform:translateY(-6px)}}45%{{opacity:1;transform:translateY(0);fill:#69f0a0;filter:drop-shadow(0 0 4px #39d353)}}100%{{opacity:1;transform:translateY(0);filter:none}}}}
@keyframes sweep{{0%{{opacity:0;transform:translateX(0)}}8%,92%{{opacity:.95}}100%{{opacity:0;transform:translateX(780px)}}}}
.day{{opacity:0;animation:cell .55s cubic-bezier(.2,.8,.2,1) both}}
.beam{{animation:sweep 2.75s ease-in-out both}}
@media(prefers-reduced-motion:reduce){{.day{{opacity:1;animation:none}}.beam{{display:none}}}}
</style>
<rect x="1" y="1" width="858" height="188" rx="16" fill="url(#bg)" stroke="#30363d"/>
<text x="24" y="31" fill="#e6edf3" font-size="14" font-weight="600">{total} contributions in {YEAR}</text>''']

    seen = set()
    for current in dates:
        offset = (current - start).days
        column, row = divmod(offset, 7)
        marker = current.month
        if marker not in seen and current.day <= 7:
            parts.append(f'<text x="{left + column * step}" y="48" fill="#8b949e" font-size="10">{current.strftime("%b")}</text>')
            seen.add(marker)
        value = days[current.isoformat()]
        delay = column * .045 + row * .035
        parts.append(f'<rect class="day" x="{left + column * step}" y="{top + row * step}" width="{cell}" height="{cell}" rx="2.5" fill="{palette[value["level"]]}" style="animation-delay:{delay:.3f}s"><title>{current.isoformat()}: {value["count"]} contributions</title></rect>')

    for row, label in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        parts.append(f'<text x="20" y="{top + row * step + 9}" fill="#8b949e" font-size="9">{label}</text>')
    parts.append(f'<rect class="beam" x="{left-10}" y="{top-6}" width="28" height="117" rx="14" fill="url(#beam)" filter="url(#blur)"/>')
    legend_x, legend_y = 711, 170
    parts.append(f'<text x="{legend_x}" y="{legend_y}" fill="#8b949e" font-size="10" text-anchor="end">Less</text>')
    for index, color in enumerate(palette):
        parts.append(f'<rect x="{legend_x + 8 + index * 14}" y="{legend_y - 10}" width="11" height="11" rx="2" fill="{color}"/>')
    parts.append(f'<text x="{legend_x + 84}" y="{legend_y}" fill="#8b949e" font-size="10">More</text></svg>')
    return "".join(parts)


if __name__ == "__main__":
    contributions = fetch()
    output = render(contributions)
    (ROOT / "assets" / "contributions.svg").write_text(output, encoding="utf-8")
    print(f"Generated {YEAR} calendar with {sum(item['count'] for item in contributions.values())} contributions")
