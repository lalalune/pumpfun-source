#!/usr/bin/env python3
"""prof.py <cand> [--ref main]: abort-jump profile. The abort block = target of the largest ja cluster (orig 0x26e0).
For each of the original's 41 abort jumps (in order), prints cand rel position (jump - abort block) minus orig's, i.e.
the cumulative drift relative to the abort block; 0 = displacement correct. Also per-segment deltas."""
import sys,os,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from abortjs import load,clusters
def profile(raw):
    cl=clusters(raw); t=max(cl,key=lambda k:len(cl[k])); js=sorted(cl[t]); return t,js
O=load('orig'); OT,OJ=profile(O); OREL=[j-OT for j in OJ]
def rel(raw):
    t,js=profile(raw)
    if len(js)!=len(OJ): return None,t,js
    return [ (j-t)-o for j,o in zip(js,OREL)],t,js
if __name__=='__main__':
    raw=load(sys.argv[1]); d,t,js=rel(raw)
    if d is None: print('cluster size mismatch',len(js),'vs',len(OJ)); sys.exit(1)
    nz=sum(1 for x in d if x==0)
    seg=[d[0]]+[d[i]-d[i-1] for i in range(1,len(d))]
    print(json.dumps({'abort':hex(t),'bytes':len(raw),'good':nz,'good_tcf':sum(1 for x in d[:25] if x==0),'good_sh':sum(1 for x in d[25:] if x==0),'cum':d,'seg':seg}))
