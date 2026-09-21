"""Daily, standard-library-only 3DGS proceedings monitor."""
import argparse
import datetime as dt
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sqlite3
import time
import urllib.parse
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parent

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items, self.href, self.label = [], None, []
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.href, self.label = dict(attrs).get('href'), []
    def handle_data(self, data):
        if self.href is not None:
            self.label.append(data)
    def handle_endtag(self, tag):
        if tag == 'a' and self.href is not None:
            self.items.append((self.href, ' '.join(''.join(self.label).split())))
            self.href = None

def plain(s):
    return ' '.join(html.unescape(re.sub('<[^>]+>', ' ', s)).split())

def gaussian(title):
    return bool(re.search(r'\b3dgs\b|\bsplat\w*|3d gaussian|gaussian.*(?:render|radiance|raster)', title, re.I))

def category(title, abstract=''):
    # A generic real-time rendering claim alone is not evidence of acceleration.
    if not gaussian(title + ' ' + abstract):
        return None
    if re.search(r'2D Gaussian|image compression|image representations|pose alignment|motion reasoning|head avatar|belief propagation|\bSLAM\b|active mapping|registration|human representation', title, re.I):
        return None
    evidence = title
    accelerated = re.search(r'accelerat|speedup|speed.up|faster|efficient|efficiency|fast|hardware|mobile|prun|compress|rasteriz|rasteris|roofline', evidence, re.I)
    direct_claim = re.search(r'(?:accelerat\w*|faster|efficient\w*)\s+(?:\w+\s+){0,3}(?:render\w*|rasteriz\w*)|(?:render\w*|rasteriz\w*)\s+(?:\w+\s+){0,3}(?:speedup|acceleration|faster)', abstract, re.I)
    if not accelerated and not direct_claim:
        return None
    if re.search(r'training|convergence|feed.forward|reconstruction', title, re.I) and not re.search(r'render|raster|inference', title, re.I):
        return '训练/重建加速（相关方向）'
    if re.search(r'render|raster|mobile|roofline|inference', title, re.I):
        return '渲染加速候选'
    return '压缩/效率（需复核渲染收益）'

class Client:
    def __init__(self, delay=1.0):
        self.delay = delay
    def get(self, url):
        for attempt in range(3):
            time.sleep(self.delay if attempt == 0 else 2 ** attempt)
            try:
                req = urllib.request.Request(url, headers={'User-Agent': '3DGSPaperTracker/1.0 (personal academic metadata monitor)'})
                with urllib.request.urlopen(req, timeout=35) as r:
                    return r.read().decode('utf-8', errors='replace')
            except urllib.error.HTTPError as e:
                if e.code < 500 and e.code != 429:
                    raise
                if attempt == 2:
                    raise
            except (OSError, TimeoutError):
                if attempt == 2:
                    raise

def official(client, index, venue, year=None):
    parser = Links()
    parser.feed(client.get(index))
    seen = set()
    for href, title in parser.items:
        if not gaussian(title):
            continue
        url = urllib.parse.urljoin(index, href)
        if venue == 'ECCV':
            match = re.search(r'/papers/eccv_(\d{4})/papers_ECCV/html/', url)
            if not match:
                continue
            paper_year = int(match[1])
        else:
            if f'/content/{venue}{year}/html/' not in url:
                continue
            paper_year = year
        if url in seen:
            continue
        seen.add(url)
        # Yield discovery first; individual detail failures must not discard a whole source.
        yield {'title': title, 'year': paper_year, 'venue': venue, 'url': url,
               'verification': '官方主会论文集', 'source': index}

def enrich(client, paper):
    body = client.get(paper['url'])
    match = re.search(r'<div[^>]+id=["\']abstract["\'][^>]*>(.*?)</div>', body, re.S | re.I)
    paper['abstract'] = plain(match[1]) if match else ''
    links = Links()
    links.feed(body)
    paper['pdf'] = next((urllib.parse.urljoin(paper['url'], u) for u, label in links.items if label.strip('[] ').lower() == 'pdf'), '')
    return paper

def dblp(client):
    for query in ('gaussian', 'splatting'):
        offset = 0
        while True:
            url = 'https://dblp.org/search/publ/api?' + urllib.parse.urlencode({'q': query, 'format': 'json', 'h': 1000, 'f': offset})
            hits = json.loads(client.get(url))['result']['hits']
            for hit in hits.get('hit', []):
                p = hit['info']
                venue = p.get('venue', '')
                # Deliberately exclude TOG journals: a TOG record alone does not prove SIGGRAPH presentation.
                if venue not in ('SIGGRAPH', 'SIGGRAPH Asia') or not p.get('key', '').startswith('conf/'):
                    continue
                title = plain(p['title'])
                if gaussian(title):
                    yield {'title': title, 'year': int(p['year']), 'venue': venue,
                           'url': p['url'], 'source': p['url'], 'verification': 'DBLP 主会记录', 'abstract': '', 'pdf': ''}
            offset += 1000
            if offset >= int(hits.get('@total', 0)):
                break

def graphics(client):
    try:
        yield from dblp(client)
        return
    except Exception as error:
        print('DBLP unavailable; trying Crossref proceedings:', str(error), flush=True)
    url = 'https://api.crossref.org/works?' + urllib.parse.urlencode({
        'query': 'Gaussian splatting', 'filter': 'type:proceedings-article,from-pub-date:2023-01-01', 'rows': 1000})
    records = json.loads(client.get(url))['message']['items']
    for item in records:
        container = ' '.join(item.get('container-title', []))
        if not re.search(r'SIGGRAPH', container, re.I) or re.search(r'workshop|posters|abstracts|courses|talks|emerging|real.time live', container, re.I):
            continue
        if not re.search(r'technical papers|conference papers', container, re.I):
            continue
        title = plain(' '.join(item.get('title', [])))
        if gaussian(title):
            yield {'title': title, 'year': item.get('published', item['issued'])['date-parts'][0][0],
                   'venue': 'SIGGRAPH Asia' if re.search(r'Asia', container, re.I) else 'SIGGRAPH',
                   'url': 'https://doi.org/' + item['DOI'], 'source': url,
                   'verification': 'Crossref 出版商会议论文元数据', 'abstract': plain(item.get('abstract', '')), 'pdf': ''}

def identity(p):
    return hashlib.sha256(re.sub(r'\W+', '', p['title'].casefold()).encode()).hexdigest()

def save(db, p, now):
    key = identity(p)
    old = db.execute('SELECT first_seen FROM papers WHERE id=?', (key,)).fetchone()
    p['first_seen'] = old[0] if old else now
    p['last_seen'] = now
    db.execute('INSERT INTO papers VALUES (?,?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data',
               (key, p['first_seen'], json.dumps(p, ensure_ascii=False)))
    db.commit()
    return old is None

def export(db, status):
    papers = [json.loads(r[0]) for r in db.execute('SELECT data FROM papers')]
    for p in papers:
        p['category'] = category(p['title'], p.get('abstract', ''))
    papers = [p for p in papers if p['category']]
    papers.sort(key=lambda p: (p['year'], p['first_seen'], p['title']), reverse=True)
    data = {'status': status, 'papers': papers}
    for name, value in [('papers.json', data), ('status.json', status)]:
        tmp = ROOT / 'data' / (name + '.tmp')
        tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
        tmp.replace(ROOT / 'data' / name)
    lines = ['# 3DGS 加速论文追踪', '', f"最近检查：{status['time']}；新增：{status['new']}；数据源错误：{len(status['errors'])}", '',
             '每天更新；年份为发表年份，发现日期不等于发表日期。方向标签由规则筛选，需阅读论文确认。', '']
    for p in papers:
        lines += [f"## {p['title']}", f"- {p['venue']} {p['year']} · {p['verification']} · {p['category']}",
                  f"- [论文与来源]({p['url']})" + (f" · [PDF]({p['pdf']})" if p.get('pdf') else ''),
                  f"- 首次发现：{p['first_seen']}", '']
    if status['errors']:
        lines += ['## 本轮未完成的数据源', *['- ' + e for e in status['errors']]]
    (ROOT / '论文列表.md').write_text('\n'.join(lines), encoding='utf-8')

def run(args):
    (ROOT / 'data').mkdir(exist_ok=True)
    db = sqlite3.connect(ROOT / 'data' / 'papers.sqlite3', timeout=30)
    db.execute('CREATE TABLE IF NOT EXISTS papers (id TEXT PRIMARY KEY, first_seen TEXT NOT NULL, data TEXT NOT NULL)')
    now = dt.datetime.now().astimezone().isoformat(timespec='seconds')
    status = {'time': now, 'new': 0, 'checked': 0, 'errors': [], 'sources_ok': []}
    client = Client(args.delay)
    year = dt.date.today().year
    sources = []
    for y in range(args.since, year + 1):
        sources.append((f'CVPR {y}', lambda y=y: official(client, f'https://openaccess.thecvf.com/CVPR{y}?day=all', 'CVPR', y)))
        if y % 2:
            sources.append((f'ICCV {y}', lambda y=y: official(client, f'https://openaccess.thecvf.com/ICCV{y}?day=all', 'ICCV', y)))
    if not args.cvf_only:
        from extended_sources import sources as extended_sources
        sources += [('ECCV', lambda: official(client, 'https://www.ecva.net/papers.php', 'ECCV')),
                    ('SIGGRAPH / SIGGRAPH Asia', lambda: graphics(client))]
        sources += extended_sources(client, args.since)
    for label, source in sources:
        print('Checking', label, flush=True)
        try:
            for p in source():
                if p['year'] < args.since:
                    continue
                if not category(p['title']):
                    continue
                if p['verification'].startswith('官方'):
                    try:
                        enrich(client, p)
                    except Exception as e:
                        status['errors'].append(p['url'] + ': ' + str(e))
                p['category'] = category(p['title'], p.get('abstract', ''))
                status['checked'] += 1
                if p['category']:
                    p.setdefault('publication_type', 'conference')
                    status['new'] += int(save(db, p, now))
                    print('  ' + p['title'], flush=True)
                    export(db, status)
            status['sources_ok'].append(label)
        except Exception as e:
            status['errors'].append(label + ': ' + str(e))
        export(db, status)
    export(db, status)
    with (ROOT / 'data' / 'runs.jsonl').open('a', encoding='utf-8') as f:
        f.write(json.dumps(status, ensure_ascii=False) + '\n')
    db.close()
    print(json.dumps(status, ensure_ascii=False), flush=True)
    return 2 if status['errors'] else 0

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--since', type=int, default=2023)
    ap.add_argument('--delay', type=float, default=1.0)
    ap.add_argument('--cvf-only', action='store_true', help='Only check CVF; intended for diagnostics')
    raise SystemExit(run(ap.parse_args()))
