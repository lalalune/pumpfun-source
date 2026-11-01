import json,sys
R=[json.loads(l) for l in open(sys.argv[1])]
E=[r for r in R if 'M' not in r]
R=[r for r in R if 'M' in r]
n=int(sys.argv[2]) if len(sys.argv)>2 else 30
only=len(sys.argv)>3
R.sort(key=lambda r:(-(r['bytes']==27400), -r['M']))
for r in R[:n]:
    if only and r['bytes']!=27400: continue
    print(r['M'],r['bytes'],r['lddw'],r['spec'],'|',r.get('name_ord'))
print('errors',len(E), E[:2])
