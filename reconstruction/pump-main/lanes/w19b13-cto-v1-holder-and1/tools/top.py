import json,sys,os
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w19b13-cto-v1-holder-and1')
R=[json.loads(l) for l in open(OUT+'/res/'+sys.argv[1])]
print(len(R),'rows; errors',sum(1 for r in R if r.get('M') is None))
R=[r for r in R if r.get('M')]
base=int(sys.argv[2]) if len(sys.argv)>2 else 2338
lim=int(sys.argv[3]) if len(sys.argv)>3 else 27400
A=[r for r in R if r['bytes']<=lim]; A.sort(key=lambda r:(-r['M'],r['bytes']))
seen=set()
for r in A[:400]:
    if r['sig'] in seen: continue
    seen.add(r['sig'])
    if len(seen)>25: break
    print(r['M'],r['bytes'],r.get('block','')[:34],r.get('p',''),r.get('where',''),r.get('br','')[:60],r['sig'])
B=[r for r in R if r['bytes']>lim]; B.sort(key=lambda r:(-r['M'],r['bytes']))
print('off-size:')
seen=set()
for r in B[:60]:
    if r['sig'] in seen: continue
    seen.add(r['sig'])
    if len(seen)>10: break
    print(r['M'],r['bytes'],r.get('block','')[:34],r.get('p',''),r.get('br','')[:60])
