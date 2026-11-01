#!/usr/bin/env python3
"""permhc.py <dir>: bestperm + pairwise-swap hill climb over vote-suggested swaps; reports per-bin gain of the final perm"""
import sys,os,json,time; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import relab as R
d=sys.argv[1]; b=R.g['elf_fn'](d+'/f.o',R.g['KEEP']); sp=R.spills(d+'/pei.mir')
m0=R.M(b); mb,pm=R.bestperm(b,sp,3)
cur=dict(pm); best=mb; t0=time.time()
for rnd in range(3):
    bb=R.apply(b,cur); V=R.votes(bb,set(cur.values())); inv={v:k for k,v in cur.items()}
    cand=set()
    if os.environ.get('FULL'):
        S=sorted(inv); cand={(S[i],S[j]) for i in range(len(S)) for j in range(i+1,len(S))}
    for y,dd in V.items():
        for x in dd:
            if x in inv and x!=y: cand.add(tuple(sorted((y,x))))
    imp=0
    for y,x in sorted(cand):
        a,c=inv[y],inv[x]; t=dict(cur); t[a],t[c]=cur[c],cur[a]
        m=R.M(R.apply(b,t))
        if m>best: best=m; cur=t; inv={v:k for k,v in cur.items()}; imp+=1
    print('round',rnd,'cands',len(cand),'improved',imp,'M',best,'%.0fs'%(time.time()-t0),file=sys.stderr)
    if not imp: break
moved={k:v for k,v in cur.items() if k!=v}
json.dump({'M':m0,'Mperm':mb,'Mhc':best,'moved':moved},open(d+'/permhc.json','w'))
print(json.dumps({'d':d,'M':m0,'Mperm':mb,'Mhc':best,'nmoved':len(moved),'ratio':R.ratio(R.apply(b,cur))}))
