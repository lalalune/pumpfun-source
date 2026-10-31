#!/usr/bin/env python3
"""regflow.py fn.bin off reg: reaching defs of reg at off and first reads reachable from off (machine CFG)."""
import sys,os
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import artifacts as A
f,off,r=sys.argv[1],int(sys.argv[2],0),int(sys.argv[3])
ins,lout=A.liveness(open(f,'rb').read()); succ=A.LAST_SUCC
k=[i for i,d in enumerate(ins) if d['off']==off][0]
print('live-out at',hex(off),sorted(lout[k]))
print('reaching defs:',[ (hex(ins[j]['off']),ins[j]['txt']) for j in A.reaching(ins,succ,k,r)])
seen=set();st=list(succ[k]);uses=set()
while st:
    j=st.pop()
    if j in seen: continue
    seen.add(j); d=ins[j]
    if r in d['reads'] and not (d['op']==0x85): uses.add(j)
    if r in d['writes']: continue
    st.extend(succ[j])
print('first reads:',[(hex(ins[j]['off']),ins[j]['txt']) for j in sorted(uses)][:20])
