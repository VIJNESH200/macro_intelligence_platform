from __future__ import annotations
import json
with open('cpi_codelists.json', 'r') as f:
    cpi = json.load(f)
with open('pi_codelists.json', 'r') as f:
    pi = json.load(f)

def find_india_and_index(cl_list, name):
    print(f'\n--- {name} ---')
    for cl in cl_list:
        if 'REF_AREA' in cl['id']:
            for code in cl.get('codes', []):
                if 'India' in code.get('name', '') or code.get('id') == 'IND':
                    print('REF_AREA code for India:', code.get('id'))
        
        if 'INDICATOR' in cl['id'] or 'INDEX' in cl['id']:
            print(f'Looking at codelist: {cl["id"]}')
            for code in cl.get('codes', []):
                if 'IX' in code.get('id') or 'PI' in code.get('id'):
                    print(f"  {code.get('id')}: {code.get('name')}")

find_india_and_index(cpi, 'CPI')
find_india_and_index(pi, 'PI')
