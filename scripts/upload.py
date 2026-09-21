import json
import os
from pathlib import Path
import urllib.request
from urllib.parse import urlparse

root = Path(__file__).resolve().parent
data = json.loads((root / 'data' / 'papers.json').read_text(encoding='utf-8'))
url = os.environ['SITE_URL'].rstrip('/')
if urlparse(url).scheme != 'https' or not os.environ.get('INGEST_TOKEN'):
    raise SystemExit('Configure HTTPS SITE_URL and INGEST_TOKEN in GitHub settings')
payload = {'papers': data['papers'], 'errors': data['status']['errors'], 'sources_ok': data['status']['sources_ok']}
headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + os.environ['INGEST_TOKEN']}
if os.environ.get('SITES_ACCESS_TOKEN'):
    headers['OAI-Sites-Authorization'] = 'Bearer ' + os.environ['SITES_ACCESS_TOKEN']
request = urllib.request.Request(url + '/api/ingest', data=json.dumps(payload).encode(), headers=headers, method='POST')
with urllib.request.urlopen(request, timeout=60) as response:
    result = json.load(response)
    print('Uploaded records:', result['saved'])
