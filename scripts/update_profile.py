from datetime import date, timedelta
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from pathlib import Path
import json
ROOT = Path(__file__).resolve().parents[1]
class Calendar(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = {}
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('data-date') and 'data-level' in a:
            d = date.fromisoformat(a['data-date'])
            level = int(a['data-level'])
            if not 0 <= level <= 4: raise ValueError('Invalid activity level')
            self.days[d.isoformat()] = level

def wrap(body, height):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="860" height="{height}" viewBox="0 0 860 {height}">
<style>text{{font-family:Consolas,monospace}}.r{{animation:show .7s both;animation-delay:var(--d,0s)}}@keyframes show{{from{{opacity:0;transform:translateY(5px)}}to{{opacity:1;transform:translateY(0)}}}}@media(prefers-reduced-motion:reduce){{.r{{animation:none}}}}</style>
<rect x="1" y="1" width="858" height="{height-2}" rx="16" fill="#0d1117" stroke="#30363d"/>{body}</svg>'''
def profile():
    b = '<title>Furkan Emre Çördük — Junior Software Developer</title>'
    for x,c in [(25,'#ff5f57'),(45,'#febc2e'),(65,'#28c840')]: b += f'<circle cx="{x}" cy="25" r="5" fill="{c}"/>'
    b += '<text x="91" y="30" fill="#8b949e" font-size="12">furkan@github: ~</text>'
    rows=['███████╗ ███████╗','██╔════╝ ██╔════╝','█████╗   █████╗  ','██╔══╝   ██╔══╝  ','██║      ███████╗','╚═╝      ╚══════╝']
    for i,row in enumerate(rows): b += f'<text class="r" style="--d:{i*.12}s" x="30" y="{90+i*23}" fill="#58d68d" font-size="18" xml:space="preserve">{row}</text>'
    b += '<path d="M245 65V230" stroke="#30363d"/>'
    for i,(k,v) in enumerate([('Name','Furkan Emre Çördük'),('Role','Junior Software Developer'),('Focus','Backend Development')]):
        b += f'<g class="r" style="--d:{.5+i*.25}s"><text x="272" y="{103+i*47}" fill="#58d68d" font-size="18">{k}</text><text x="355" y="{103+i*47}" fill="#e6edf3" font-size="18">{v}</text></g>'
    b += '<text class="r" style="--d:1.4s" x="30" y="265" fill="#8b949e" font-size="13">$ exploring, learning, building. ▋</text>'
    return wrap(b,292)
def heatmap(days):
    end=date.fromisoformat(max(days)); start=end-timedelta(days=364)
    start-=timedelta(days=(start.weekday()+1)%7)
    colors=['#161b22','#0e4429','#006d32','#26a641','#39d353']
    b='<title>GitHub contribution calendar</title><text x="30" y="35" fill="#e6edf3" font-size="16">CONTRIBUTIONS</text>'
    b+=f'<text x="830" y="35" text-anchor="end" fill="#8b949e" font-size="12">updated {end}</text>'
    d=start
    while d<=end:
        col,row=divmod((d-start).days,7); key=d.isoformat()
        if key in days:
            level=days[key]
            b+=f'<rect class="r" style="--d:{(col+row)*.018:.3f}s" x="{30+col*15}" y="{57+row*17}" width="11" height="12" rx="2" fill="{colors[level]}"><title>{key}: activity level {level}/4</title></rect>'
        d+=timedelta(days=1)
    b+='<text x="30" y="206" fill="#8b949e" font-size="12">Small steps. Consistent progress.</text><text x="660" y="206" fill="#8b949e" font-size="11">Less</text>'
    for i,c in enumerate(colors): b+=f'<rect x="{697+i*17}" y="196" width="12" height="12" rx="2" fill="{c}"/>'
    b+='<text x="790" y="206" fill="#8b949e" font-size="11">More</text>'
    return wrap(b,230)
def main():
    req=Request('https://github.com/users/cordukfurkanemre/contributions',headers={'User-Agent':'profile-calendar'})
    with urlopen(req,timeout=30) as response:
        p=Calendar(); p.feed(response.read().decode())
    if len(p.days)<300: raise RuntimeError('Incomplete calendar; existing assets preserved')
    (ROOT/'assets').mkdir(exist_ok=True); (ROOT/'data').mkdir(exist_ok=True)
    (ROOT/'assets/profile.svg').write_text(profile(),encoding='utf-8')
    (ROOT/'assets/contributions.svg').write_text(heatmap(p.days),encoding='utf-8')
    (ROOT/'data/contributions.json').write_text(json.dumps(p.days,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(f'Generated assets from {len(p.days)} real contribution days')
if __name__=='__main__': main()
