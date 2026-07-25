from __future__ import annotations
import urllib.request
import urllib.parse
import json

try:
    q = urllib.parse.quote('title:"Index of Eight Core Industries"')
    url = f'https://data.gov.in/api/3/action/package_search?q={q}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    response = urllib.request.urlopen(req)
    html = response.read().decode('utf-8')
    print('Raw response:', html[:200])
    data = json.loads(html)
    for result in data.get('result', {}).get('results', []):
        print(f"Dataset: {result['title']}")
        for resource in result.get('resources', []):
            print(f"  Resource: {resource['name']} -> ID: {resource['id']}")
except Exception as e:
    print('Error:', e)
