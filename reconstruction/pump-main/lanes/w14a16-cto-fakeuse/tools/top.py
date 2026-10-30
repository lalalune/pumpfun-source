import json,sys,collections
f=sys.argv[1]; n=int(sys.argv[2]) if len(sys.argv)>2 else 25
R=[json.loads(l) for l in open(f)]
print(len(R),'same',sum(r.get('same',0) for r in R),'27400',sum(r.get('bytes')==27400 for r in R),'err',sum('error' in r for r in R))
g=[r for r in R if r.get('d') is not None and r['d']>0]
g.sort(key=lambda r:(-(r['bytes']==27400),-r['d']))
for r in g[:n]: print(r['d'],r['bytes'],r.get('slots'),r['v'],r['ty'],r['def'][:40],'->',r['blk'][:50])
