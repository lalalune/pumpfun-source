#!/usr/bin/env python3
"""post.py <name>... : for captured variants fx/<name>/m.ll, score plain / n2 (per-exit copies) / o3 (j60 fold + bb57 placement)."""
import sys,os,json
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import lx,pipe,skel,d as D
OUT=os.path.dirname(T)
for n in sys.argv[1:]:
    m=open(OUT+'/fx/%s/m.ll'%n).read(); row={'name':n}
    for pn,pf in (('plain',None),('n2',pipe.N2),('o3',pipe.O3)):
        try:
            t=pf(m) if pf else m
            p=OUT+'/t/%s.%s.ll'%(n,pn); open(p,'w').write(t)
            r=lx.run(p,n+'.'+pn); os.remove(p)
            if 'err' in r: row[pn]='err'; continue
            b=D.load(OUT+'/lx/%s.%s/fn.bin'%(n,pn))
            row[pn]='%d@%d m3=%d'%(r['M'],r['bytes'],skel.M(b,3))
        except Exception as e: row[pn]='EXC '+str(e)[:80]
    print(json.dumps(row),flush=True)
