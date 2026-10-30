import json,sys,collections
R=[]
for f in sys.argv[1:]:
    for l in open(f):
        r=json.loads(l); r['src']=f.split('/')[-1].split('.')[0]; R.append(r)
print('variants',len(R),'at27400',sum(r.get('bytes')==27400 for r in R),'same',sum(r.get('same',False) for r in R),
      'gain@27400',sum(1 for r in R if r.get('bytes')==27400 and (r.get('d') or 0)>0),
      'loss@27400',sum(1 for r in R if r.get('bytes')==27400 and (r.get('d') or 0)<0))
bv=collections.defaultdict(list)
for r in R: bv[r['v']].append(r)
rows=[]
for v,rs in bv.items():
    p=[r for r in rs if r.get('bytes')==27400 and r.get('d') is not None]
    best=max(p,key=lambda r:r['d']) if p else None
    q=[r for r in rs if r.get('d') is not None]
    anyb=max(q,key=lambda r:r['d']) if q else None
    rows.append((best['d'] if best else -9,v,rs[0]['ty'],len(rs),len(p),best,anyb))
rows.sort(key=lambda x:-x[0])
for d,v,t,n,np_,b,a in rows[:int(__import__('os').environ.get('N','40'))]:
    print('%-28s %-4s n=%-4d n27400=%-4d best27400=%s %s | bestany=%s@%s %s'%(v[:28],t,n,np_,
      b['d'] if b else None,(b['blk'][:34]+' '+b['src']) if b else '',a['d'] if a else None,a['bytes'] if a else None,a['blk'][:30] if a else ''))
