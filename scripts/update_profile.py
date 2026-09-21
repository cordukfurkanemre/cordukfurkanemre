from datetime import date, timedelta
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from pathlib import Path
import json
import os
import re
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

def fetch_private_calendar(token):
    query = '''query($login:String!,$from:DateTime!,$to:DateTime!){
      viewer{login}
      user(login:$login){contributionsCollection(from:$from,to:$to){
        restrictedContributionsCount
        contributionCalendar{totalContributions weeks{contributionDays{date contributionCount contributionLevel}}}
      }}
    }'''
    today=date.today()
    payload=json.dumps({'query':query,'variables':{
        'login':'cordukfurkanemre',
        'from':f'{today-timedelta(days=365)}T00:00:00Z',
        'to':f'{today}T23:59:59Z'
    }}).encode()
    req=Request('https://api.github.com/graphql',data=payload,headers={
        'Authorization':f'Bearer {token}','Content-Type':'application/json','User-Agent':'profile-calendar'
    })
    with urlopen(req,timeout=30) as response:
        result=json.loads(response.read())
    if result.get('errors'):
        raise RuntimeError(f'GitHub GraphQL error: {result["errors"][0]["message"]}')
    if result['data']['viewer']['login'].lower() != 'cordukfurkanemre':
        raise RuntimeError('PROFILE_TOKEN must belong to cordukfurkanemre')
    collection=result['data']['user']['contributionsCollection']
    calendar=collection['contributionCalendar']
    counts={d['date']:d['contributionCount'] for week in calendar['weeks'] for d in week['contributionDays']}
    if sum(counts.values()) != calendar['totalContributions']:
        raise RuntimeError('GraphQL contribution total does not match calendar cells')
    return counts, collection['restrictedContributionsCount']

def fetch_public_calendar():
    req=Request('https://github.com/users/cordukfurkanemre/contributions',headers={'User-Agent':'profile-calendar'})
    with urlopen(req,timeout=30) as response:
        parser=Calendar(); parser.feed(response.read().decode())
    if set(parser.days) != set(parser.counts) or len(parser.days) < 300:
        raise RuntimeError('Incomplete public contribution calendar')
    return parser.counts

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
def heatmap(days, counts, restricted=0):
    palette=['#161b22','#0e4429','#006d32','#26a641','#39d353','#69f0a0']
    ordered=[date.fromisoformat(key) for key in sorted(days)]
    first,last=ordered[0],ordered[-1]
    start=first-timedelta(days=(first.weekday()+1)%7)
    cols=((last-start).days//7)+1
    step=15; cell=12; left=52; top=50
    width=left+cols*step+22; height=272

    def level(count):
        if count == 0: return 0
        if count <= 2: return 1
        if count <= 5: return 2
        if count <= 10: return 3
        if count <= 20: return 4
        return 5

    active=[d for d in ordered if counts[d.isoformat()] > 0]
    longest=current=run=0
    previous=None
    for d in active:
        run=run+1 if previous and d == previous+timedelta(days=1) else 1
        longest=max(longest,run); previous=d
    cursor=last
    while cursor >= first and counts.get(cursor.isoformat(),0) > 0:
        current+=1; cursor-=timedelta(days=1)
    best=max(counts,key=counts.get)

    css='''<style>
    @keyframes cell{0%{opacity:0;transform:translateY(-8px)}100%{opacity:1;transform:translateY(0)}}
    .c{opacity:0;animation:cell .42s cubic-bezier(.2,.8,.2,1) both}
    text{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
    @media(prefers-reduced-motion:reduce){.c{animation:none;opacity:1}}
    </style>'''
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',css,
           '<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#0d1420"/><stop offset="1" stop-color="#0a0e14"/></linearGradient></defs>',
           f'<rect width="{width}" height="{height}" rx="12" fill="url(#bg)"/><rect x=".5" y=".5" width="{width-1}" height="{height-1}" rx="12" fill="none" stroke="#1f6feb" stroke-opacity=".55"/>',
           '<line x1="0" y1="30" x2="100%" y2="30" stroke="#1f6feb" stroke-opacity=".35"/>']
    for i,color in enumerate(['#ff5f56','#ffbd2e','#27c93f']):
        parts.append(f'<circle cx="{22+i*16}" cy="15" r="5" fill="{color}"/>')
    parts.append(f'<text x="{width/2}" y="19" fill="#7d8590" font-size="12" text-anchor="middle">furkan@github: ~/contributions --graph</text>')
    seen=set()
    for d in ordered:
        col=(d-start).days//7
        marker=(d.year,d.month)
        if marker not in seen and d.day <= 7:
            parts.append(f'<text x="{left+col*step}" y="44" fill="#7d8590" font-size="10">{d.strftime("%b")}</text>'); seen.add(marker)
    for row,label in [(1,'Mon'),(3,'Wed'),(5,'Fri')]:
        parts.append(f'<text x="22" y="{top+row*step+9.5}" fill="#7d8590" font-size="9">{label}</text>')
    for d in ordered:
        key=d.isoformat(); offset=(d-start).days; col,row=divmod(offset,7)
        delay=col*.018+row*.045
        parts.append(f'<rect class="c" x="{left+col*step}" y="{top+row*step}" width="{cell}" height="{cell}" rx="2.5" fill="{palette[level(counts[key])]}" style="animation-delay:{delay:.3f}s"><title>{key}: {counts[key]} contributions</title></rect>')
    legend_y=top+7*step+7; legend_x=width-145
    parts.append(f'<text x="{legend_x}" y="{legend_y+9}" fill="#7d8590" font-size="10" text-anchor="end">Less</text>')
    for i,color in enumerate(palette):
        parts.append(f'<rect x="{legend_x+8+i*12}" y="{legend_y}" width="11" height="11" rx="2" fill="{color}"/>')
    parts.append(f'<text x="{legend_x+85}" y="{legend_y+9}" fill="#7d8590" font-size="10">More</text>')
    sep=legend_y+27
    parts.append(f'<line x1="0" y1="{sep}" x2="{width}" y2="{sep}" stroke="#1f6feb" stroke-opacity=".25"/>')
    total=sum(counts.values())
    parts.append(f'<text x="22" y="{sep+25}" fill="#39d353" font-size="13" font-weight="700">{total}<tspan fill="#7d8590" font-weight="400"> contributions in the last year</tspan></text>')
    parts.append(f'<text x="{width-22}" y="{sep+25}" fill="#7d8590" font-size="12" text-anchor="end">{first} → {last}</text>')
    parts.append(f'<text x="22" y="{sep+49}" fill="#7d8590" font-size="13">current streak <tspan fill="#22d3ee" font-weight="700">{current} days</tspan> · longest <tspan fill="#22d3ee" font-weight="700">{longest} days</tspan></text>')
    parts.append(f'<text x="{width-22}" y="{sep+49}" fill="#7d8590" font-size="12" text-anchor="end">best day <tspan fill="#f2cc60" font-weight="700">{counts[best]}</tspan> on {best}</text></svg>')
    return ''.join(parts)
def main():
    token=os.environ.get('PROFILE_TOKEN')
    if token:
        counts,restricted=fetch_private_calendar(token)
        source=f'authenticated calendar ({restricted} private contributions)'
    else:
        counts=fetch_public_calendar(); restricted=0
        source='public calendar; set PROFILE_TOKEN to include private contributions'
    days={key:0 for key in counts}
    (ROOT/'assets').mkdir(exist_ok=True); (ROOT/'data').mkdir(exist_ok=True)
    (ROOT/'assets/profile.svg').write_text(profile(),encoding='utf-8')
    (ROOT/'assets/contributions.svg').write_text(heatmap(days,counts,restricted),encoding='utf-8')
    (ROOT/'data/contributions.json').write_text(json.dumps({d:{'count':counts[d]} for d in days},sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(f'Generated {len(days)} days and {sum(counts.values())} contributions from {source}')
if __name__=='__main__': main()
