#!/usr/bin/env python3
"""summ.py: markdown summary row per screened base (b/*.jsonl). Experiment only."""
import os,json,glob,collections
OUT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R=json.load(open(OUT+'/res/ref.json'))
Q={}
for q in glob.glob(OUT+'/res/queue*.txt'):
    for l in open(q):
        f=l.split()
        if f: Q[f[0]]=(f[1],f[2])
Q.setdefault('A01',('pt:execute:28905','8ca4317449a7'))
rows=[]
for p in sorted(glob.glob(OUT+'/b/*.jsonl')):
    name=os.path.basename(p)[:-6]
    if not os.path.exists(OUT+f'/b/{name}.done'): continue
    ids,bsig=Q.get(name,('?','?'))
    n=0;err=0;best=None;neu=set();add=0;nadd=0;pos=0;bestoff=None
    for l in open(p):
        r=json.loads(l)
        if 'M' not in r: err+=1; continue
        n+=1; b=r['id'].split('+')[-1]
        if r['bytes']==27400:
            if best is None or r['M']>best[0]: best=(r['M'],b)
            if r['M']==2295 and r['sig'] not in (bsig,'61dcfe87f489'): neu.add(r['sig'])
        elif bestoff is None or r['M']>bestoff[0]: bestoff=(r['M'],r['bytes'])
        if b in R:
            if r['M']-2295==R[b][0]: add+=1
            else:
                nadd+=1
                if r['M']-2295>R[b][0]: pos+=1
    rows.append((name,ids,n,err,best,len(neu),bestoff,add,nadd,pos))
print('| base | cells | combos | best M @27,400 | new neutral sigs | best off-size | same dM as on main | differ (better) |')
print('| --- | --- | ---: | ---: | ---: | --- | ---: | ---: |')
for name,ids,n,err,best,nn,bo,add,nadd,pos in rows:
    print(f"| {name} | `{ids.replace(',','` + `')}` | {n} | {best[0] if best else '-'} | {nn} | {bo[0]} @{bo[1]} | {add} | {nadd} ({pos}) |" if bo else f"| {name} | {ids} | {n} | {best[0] if best else '-'} | {nn} | - | {add} | {nadd} ({pos}) |")
