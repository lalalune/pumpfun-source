#!/usr/bin/env python3
"""addit.py <name> [...]: additivity of single edits B on a neutral base A (b/<name>.jsonl) against main (res/ref.json).
Prints per base: n with main ref, n additive (same dM and dB as on main), and the non-additive cells (interaction
d = dM_A(B) - dM_main(B), size interaction)."""
import sys,os,json,collections
OUT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R=json.load(open(OUT+'/res/ref.json'))
MM=2295; SZ=27400
tot=collections.Counter()
for name in sys.argv[1:]:
    p=OUT+f'/b/{name}.jsonl'
    if not os.path.exists(p): continue
    c=collections.Counter(); na=[]
    for l in open(p):
        r=json.loads(l)
        if 'M' not in r: c['err']+=1; continue
        b=r['id'].split('+')[-1]
        if b not in R: c['noref']+=1; continue
        dm,db,sig=R[b]
        d=(r['M']-MM)-dm; dbb=(r['bytes']-SZ)-db
        if d==0 and dbb==0: c['additive']+=1
        else:
            c['non-additive']+=1; na.append((d,dbb,b,r['M'],r['bytes']))
            if d>0: c['positive-interaction']+=1
    tot.update(c)
    na.sort(reverse=True)
    print(name,dict(c),'best interactions:',[(x[0],x[1],x[2],x[3],x[4]) for x in na[:4]])
print('TOTAL',dict(tot))
