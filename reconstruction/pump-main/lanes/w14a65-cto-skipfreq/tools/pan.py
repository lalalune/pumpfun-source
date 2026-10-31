import json,sys,collections
R=[json.loads(l) for f in sys.argv[1:] for l in open(f)]
R=[r for r in R if 'F' in r]
print('n',len(R))
c=collections.Counter((r['k'],r.get('flag','-'),r['moved']==0) for r in R); print(c.most_common(20))
print('-- top F with flag!=r9 (deep)')
for r in sorted([r for r in R if r.get('flag') not in (None,'r9','?')],key=lambda r:-r['F'])[:15]: print(r['e'],r['ratio'],r['bytes'],r['F'],r['Fw'],r['moved'],r.get('reord_ratio'),r['flag'],r.get('r9'))
print('-- top F moved==0')
for r in sorted([r for r in R if r['moved']==0],key=lambda r:-r['F'])[:10]: print(r['e'],r['ratio'],r['bytes'],r['F'],r['Fw'],r['moved'],r.get('flag'))
print('-- top ratio')
for r in sorted(R,key=lambda r:-r['ratio'])[:10]: print(r['e'],r['ratio'],r['bytes'],r['F'],r['Fw'],r['moved'],r.get('flag'))
