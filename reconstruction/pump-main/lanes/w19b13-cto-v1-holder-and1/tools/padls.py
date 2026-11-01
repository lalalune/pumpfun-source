#!/usr/bin/env python3
"""padls.py <fn.bin> : local search moving pads (volatile hk reads) between block boundaries with LCS proxy + difflib confirm."""
import sys,os,json,time
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w19b13-cto-v1-holder-and1')
sys.path.insert(0,OUT+'/tools')
from padsim import *
raw=open(sys.argv[1],'rb').read()
S=Sim(raw)
pads0=[i for i,t in enumerate(S.toks) if is_pad(t)]
rem=set(pads0)
# initial placement: same positions (pad before token after it)
pads={}
for i in pads0:
    j=i+1
    while j in rem: j+=1
    pads[j]=pads.get(j,0)+1
f=S.build(rem,pads); print('check identity',b''.join(f)==raw,len(pads0),'lcs',lcs(S,f),'dl',dl(S,f),flush=True)
cand=sorted(S.heads|{i+1 for i in pads0})
cur=lcs(S,f); best=(dl(S,f),dict(pads))
t0=time.time(); improved=True; rounds=0
tried={}
while improved and time.time()-t0<float(sys.argv[2]):
    improved=False; rounds+=1
    for p in list(pads.keys()):
        if pads.get(p,0)==0: continue
        for c in cand:
            if c==p: continue
            q=dict(pads); q[p]-=1
            if q[p]==0: del q[p]
            q[c]=q.get(c,0)+1
            m=lcs(S,S.build(rem,q))
            if m>cur:
                cur=m; pads=q; improved=True
                d=dl(S,S.build(rem,pads))
                print('move',hex(S.slot[p]*8),'->',hex(S.slot[c]*8),'lcs',m,'dl',d,flush=True)
                if d>best[0]: best=(d,dict(pads))
                break
f=S.build(rem,best[1]); print('best dl',best[0],'lcs',lcs(S,f))
print(json.dumps({hex(S.slot[k]*8):v for k,v in sorted(best[1].items())}))
