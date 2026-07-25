import requests
BASE = 'https://api.imf.org/external/sdmx/3.0'
r = requests.get(f'{BASE}/structure/dataflow/IMF.STA/PI/+', params={'detail': 'full', 'references': 'all'})
d = r.json()
for ds in d['data']['dataStructures']:
    print('DataStructure:', ds['id'])
    for cmp in ds['dataStructureComponents']['dimensionList']['dimensions']:
        enum = cmp.get('localRepresentation', {}).get('enumeration', '')
        print(f"  {cmp['id']} -> {enum}")
