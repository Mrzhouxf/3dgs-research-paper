"""Official AI proceedings and publisher-verified journal metadata."""
import datetime as dt
import json
import re
import urllib.parse
import urllib.error

JOURNALS = {
    'TPAMI': ('0162-8828', 'IEEE Transactions on Pattern Analysis and Machine Intelligence'),
    'IJCV': ('0920-5691', 'International Journal of Computer Vision'),
    'TOG': ('0730-0301', 'ACM Transactions on Graphics'),
    'TVCG': ('1077-2626', 'IEEE Transactions on Visualization and Computer Graphics'),
    'TIP': ('1057-7149', 'IEEE Transactions on Image Processing'),
    'JMLR': ('1532-4435', 'Journal of Machine Learning Research'),
    'Artificial Intelligence': ('0004-3702', 'Artificial Intelligence'),
}

def record(title, venue, year, url, source, verification, kind='conference', abstract=''):
    return dict(title=title, venue=venue, year=year, url=url, source=source,
                verification=verification, publication_type=kind, abstract=abstract, pdf='')

def crossref(client, since, venue, issn=None, expected=None):
    from tracker import plain, gaussian
    query = {'query.title': 'Gaussian splatting', 'filter': f'from-pub-date:{since}-01-01', 'rows': 100, 'cursor': '*'}
    if issn:
        query['filter'] += ',type:journal-article,issn:' + issn
    else:
        query['query.container-title'] = {'AAAI':'AAAI Conference on Artificial Intelligence', 'IJCAI':'International Joint Conference on Artificial Intelligence', 'ACM MM':'ACM International Conference on Multimedia'}[venue]
    while True:
        source = 'https://api.crossref.org/works?' + urllib.parse.urlencode(query)
        message = json.loads(client.get(source))['message']
        items = message['items']
        for item in items:
            container = ' '.join(item.get('container-title', []))
            if re.search(r'workshop|companion|doctoral|symposium|retracted|retraction', container, re.I):
                continue
            if issn:
                if issn not in item.get('ISSN', []) or container.casefold() != expected.casefold():
                    continue
            elif venue == 'AAAI':
                if container != 'Proceedings of the AAAI Conference on Artificial Intelligence':
                    continue
            elif venue == 'IJCAI':
                if not re.search(r'^Proceedings of the .+International Joint Conference on Artificial Intelligence', container):
                    continue
            elif not re.search(r'^Proceedings of the \d+(?:st|nd|rd|th) ACM International Conference on Multimedia$', container):
                continue
            title = plain(' '.join(item.get('title', [])))
            if not gaussian(title) or re.search(r'correction|erratum|retraction', title, re.I):
                continue
            date = item.get('published', item.get('issued', {})).get('date-parts', [[0]])[0]
            if not date[0]:
                continue
            yield record(title, venue, date[0], 'https://doi.org/' + item['DOI'], source,
                         'Crossref 出版商期刊元数据' if issn else 'Crossref 出版商主会元数据',
                         'journal' if issn else 'conference', plain(item.get('abstract', '')))
        nxt = message.get('next-cursor')
        if len(items) < query['rows'] or not nxt or nxt == query['cursor']:
            break
        query['cursor'] = nxt

def neurips(client, since):
    from tracker import Links, gaussian
    index = 'https://papers.nips.cc/'
    listing = client.get(index)
    years = sorted({int(y) for y in re.findall(r'/paper_files/paper/(20\d\d)', listing) if int(y) >= since})
    if not years:
        raise ValueError('NeurIPS archive year links not found')
    for year in years:
        source = f'https://papers.nips.cc/paper_files/paper/{year}'
        links = Links(); links.feed(client.get(source))
        main_links = [(u,t) for u,t in links.items if 'main-conference' in u]
        for href, _ in main_links:
            extra = Links(); extra.feed(client.get(urllib.parse.urljoin(source, href)))
            links.items.extend(extra.items)
        for href, title in links.items:
            if gaussian(title) and '/hash/' in href and ('Abstract-Conference' in href or '-Abstract.html' in href):
                yield record(title, 'NeurIPS', year, urllib.parse.urljoin(source, href), source, 'NeurIPS 正式主会论文集')

def icml(client, since):
    from tracker import Links, gaussian, plain
    index = 'https://proceedings.mlr.press/'
    body = client.get(index)
    volumes = []
    for li in re.findall(r'<li\b[^>]*>(.*?)</li>', body, re.S):
        match = re.search(r'Proceedings of ICML (20\d\d)', plain(li))
        if match and int(match[1]) >= since:
            links=Links(); links.feed(li)
            volumes += [(urllib.parse.urljoin(index,u).rstrip('/')+'/',int(match[1])) for u,t in links.items if re.search(r'(?:^|/)v\d+/?$',u)]
    if not volumes:
        raise ValueError('ICML proceedings volumes not found')
    for source,year in volumes:
        body=client.get(source)
        # PMLR titles are paragraphs; the adjacent Abstract link contains the paper URL.
        for block in re.findall(r'<div class="paper">(.*?)</div>',body,re.S):
            title=re.search(r'<p class="title">(.*?)</p>',block,re.S)
            if not title or not gaussian(plain(title[1])):
                continue
            links=Links();links.feed(block)
            href=next((u for u,t in links.items if t.lower() in ('abstract','abs')),None)
            if href:
                yield record(plain(title[1]),'ICML',year,urllib.parse.urljoin(source,href),source,'PMLR ICML 正式主会论文集')

def iclr(client, since):
    from tracker import gaussian
    def value(content,key):
        v=content.get(key,'');return v.get('value','') if isinstance(v,dict) else v
    for year in range(max(since,2024),dt.date.today().year+1):
        venueid=f'ICLR.cc/{year}/Conference'
        offset=0
        while True:
            source='https://api2.openreview.net/notes?'+urllib.parse.urlencode({'content.venueid':venueid,'limit':1000,'offset':offset})
            result=json.loads(client.get(source))
            notes=result.get('notes',[])
            for note in notes:
                c=note.get('content',{});title=value(c,'title');label=value(c,'venue')
                if value(c,'venueid')!=venueid or re.search(r'submitted|withdrawn|rejected|workshop',label,re.I) or not re.search(r'ICLR.*(?:poster|oral|spotlight|accept)',label,re.I):
                    continue
                if gaussian(title):
                    yield record(title,'ICLR',year,'https://openreview.net/forum?id='+note['id'],source,'OpenReview 官方已录用主会记录',abstract=value(c,'abstract'))
            offset+=len(notes)
            if not notes or offset>=result.get('count',offset):
                break

def sources(client,since):
    result=[('NeurIPS',lambda:neurips(client,since)),('ICML',lambda:icml(client,since)),('ICLR',lambda:iclr(client,since))]
    result += [(v,lambda v=v:crossref(client,since,v)) for v in ('AAAI','IJCAI','ACM MM')]
    result += [(v,lambda v=v,i=i,n=n:crossref(client,since,v,i,n)) for v,(i,n) in JOURNALS.items()]
    return result
