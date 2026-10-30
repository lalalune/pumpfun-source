#!/usr/bin/env python3
"""exact.py ref name..: exact (ratio-metric) matched orig insns per 0x400 orig region; deltas vs ref."""
import sys,os,difflib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import oracle
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a21-cto-helperbound')
o=oracle.mask(oracle.orig_window()); addr=[];x=0
for t in o: addr.append(x); x+=len(t)
step=int(os.environ.get('STEP','0x400'),16)
def per(n):
    c=oracle.mask(open(f'{O}/rx/{n}/fn.bin','rb').read()); sm=difflib.SequenceMatcher(None,o,c,autojunk=False); h={}
    for a,b,s in sm.get_matching_blocks():
        for k in range(s): h[addr[a+k]//step]=h.get(addr[a+k]//step,0)+1
    return h
names=sys.argv[1:]; R=[per(n) for n in names]
ks=sorted(set().union(*R))
print('region '+' '.join(f'{n[:10]:>10s}' for n in names))
for k in ks:
    v=[R[0].get(k,0)]+[r.get(k,0)-R[0].get(k,0) for r in R[1:]]
    print(f'{k*step:06x} '+' '.join(f'{x:>+10d}' if i else f'{x:>10d}' for i,x in enumerate(v)))
print('total  '+' '.join(f'{sum(r.values())-(sum(R[0].values()) if i else 0):>+10d}' for i,r in enumerate(R)))
