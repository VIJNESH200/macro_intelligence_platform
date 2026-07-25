import json
with open('pi_codelists.json', 'r') as f:
    pi = json.load(f)

for cl in pi:
    print(cl['id'])
    for code in cl.get('codes', []):
        if 'India' in code.get('name', '') or code.get('id') == 'IND' or 'IPIX' in code.get('id') or 'IX' in code.get('id'):
            print(f"  {code.get('id')}: {code.get('name')}")
