from datetime import date, timedelta
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from pathlib import Path
import json
import re
from html import escape
ROOT = Path(__file__).resolve().parents[1]
class Calendar(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = {}
        self.ids = {}
        self.counts = {}
        self.tip = None
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('data-date') and 'data-level' in a:
            d = date.fromisoformat(a['data-date'])
            level = int(a['data-level'])
            if not 0 <= level <= 4: raise ValueError('Invalid activity level')
            self.days[d.isoformat()] = level
            self.ids[a['id']] = d.isoformat()
        if tag == 'tool-tip': self.tip = a.get('for')
    def handle_data(self, text):
        if self.tip in self.ids:
            match = re.search(r'(No|[\d,]+) contributions?', text)
            if match: self.counts[self.ids[self.tip]] = 0 if match[1] == 'No' else int(match[1].replace(',', ''))
    def handle_endtag(self, tag):
        if tag == 'tool-tip': self.tip = None

def wrap(body, height):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="860" height="{height}" viewBox="0 0 860 {height}">
<style>text{{font-family:Consolas,monospace}}.r{{animation:show .7s both;animation-delay:var(--d,0s)}}@keyframes show{{from{{opacity:0;transform:translateY(5px)}}to{{opacity:1;transform:translateY(0)}}}}@media(prefers-reduced-motion:reduce){{.r{{animation:none}}}}</style>
<rect x="1" y="1" width="858" height="{height-2}" rx="16" fill="#0d1117" stroke="#30363d"/>{body}</svg>'''
def profile():
    b = '<title>Furkan Emre Çördük — Junior Software Developer</title>'
    for x,c in [(28,'#ff5f57'),(48,'#febc2e'),(68,'#28c840')]: b += f'<circle cx="{x}" cy="26" r="5" fill="{c}"/>'
    b += '<text x="830" y="31" text-anchor="end" fill="#788391" font-size="12">~/furkan</text><path d="M1 49H859" stroke="#212a35"/>'
    b += '<text x="32" y="88" fill="#78dfa1" font-size="16">❯ whoami</text>'
    for i,(k,v) in enumerate([('name','Furkan Emre Çördük'),('role','Junior Software Developer'),('focus','Backend Development')]):
        b += f'<g class="r" style="--d:{.2+i*.25}s"><text x="32" y="{133+i*42}" fill="#788391" font-size="18">{k}</text><text x="148" y="{133+i*42}" fill="#e6edf3" font-size="22">{v}</text></g>'
    b += '<text class="r" style="--d:1.1s" x="32" y="266" fill="#78dfa1" font-size="16">❯ <tspan fill="#788391">_</tspan></text>'
    return wrap(b,292)
def heatmap(days, counts):
    end=date.fromisoformat(max(days)); start=date.fromisoformat(min(days))
    start-=timedelta(days=(start.weekday()+1)%7)
    colors=['#161b22','#0e4429','#006d32','#26a641','#39d353']
    b='<title>GitHub contribution calendar</title><text x="30" y="35" fill="#e6edf3" font-size="16">CONTRIBUTIONS</text>'
    b+=f'<text x="830" y="35" text-anchor="end" fill="#8b949e" font-size="12">{sum(counts.values())} contributions in the last year</text>'
    for row,label in [(1,'Mon'),(3,'Wed'),(5,'Fri')]: b+=f'<text x="19" y="{82+row*17}" fill="#8b949e" font-size="10">{label}</text>'
    month = None
    d=start
    while d<=end:
        col,row=divmod((d-start).days,7); key=d.isoformat()
        if d.month != month and (d-start).days >= 7 and d.day <= 7:
            b+=f'<text x="{53+col*14.7}" y="62" fill="#8b949e" font-size="11">{d.strftime("%b")}</text>'
            month=d.month
        if key in days:
            level=days[key]
            b+=f'<rect opacity="0" x="{53+col*14.7}" y="{73+row*17}" width="11" height="12" rx="2" fill="{colors[level]}"><title>{key}: {counts[key]} contributions</title><animate attributeName="opacity" from="0" to="1" begin="{(col*.065+row*.035):.3f}s" dur="0.4s" fill="freeze"/></rect>'
        d+=timedelta(days=1)
    b+=f'<text x="30" y="224" fill="#8b949e" font-size="12">{min(days)} — {max(days)} · public activity</text><text x="660" y="224" fill="#8b949e" font-size="11">Less</text>'
    for i,c in enumerate(colors): b+=f'<rect x="{697+i*17}" y="214" width="12" height="12" rx="2" fill="{c}"/>'
    b+='<text x="790" y="224" fill="#8b949e" font-size="11">More</text>'
    return wrap(b,248)
def main():
    req=Request('https://github.com/users/cordukfurkanemre/contributions',headers={'User-Agent':'profile-calendar'})
    with urlopen(req,timeout=30) as response:
        p=Calendar(); p.feed(response.read().decode())
    if set(p.days) != set(p.counts): raise RuntimeError('Contribution counts missing')
    if len(p.days)<300: raise RuntimeError('Incomplete calendar; existing assets preserved')
    (ROOT/'assets').mkdir(exist_ok=True); (ROOT/'data').mkdir(exist_ok=True)
    (ROOT/'assets/profile.svg').write_text(profile(),encoding='utf-8')
    (ROOT/'assets/contributions.svg').write_text(heatmap(p.days, p.counts),encoding='utf-8')
    (ROOT/'data/contributions.json').write_text(json.dumps({d: {'level': p.days[d], 'count': p.counts[d]} for d in p.days},sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(f'Generated assets from {len(p.days)} real contribution days')
if __name__=='__main__': main()
