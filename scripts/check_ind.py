import json
with open('pi_codelists.json', 'r') as f:
    pi = json.load(f)

for cl in pi:
    if cl['id'] == 'CL_IPI_PRODUCTION_INDEX':
        print(f"Checking {cl['id']}")
        for code in cl.get('codes', []):
            if code['id'] == 'IND':
                print(f"  Code {code['id']} means: {code['name']}")
