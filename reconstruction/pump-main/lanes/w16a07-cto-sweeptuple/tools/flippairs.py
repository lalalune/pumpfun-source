#!/usr/bin/env python3
"""flippairs.py <fn.bin> <flipall.json> <out.json>: every (-8 flip, +8 flip) pair at the base size (binary oracle)."""
import sys,os,json,multiprocessing as mp
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import flipall as F, relab as R
RAW=open(sys.argv[1],'rb').read(); D=json.load(open(sys.argv[2]))
mi=[r['k'] for r in D['res'] if r['kind']=='-']; pl=[r['k'] for r in D['res'] if r['kind']=='+']
def ev(p):
    k1,k2=p
    if k2 in (k1,k1+1): return None
    a=F.flip_minus(RAW,k1); k2b=k2-1 if k2>k1 else k2
    b=F.flip_plus(a,k2b); return (k1,k2,len(b),R.M(b))
if __name__=='__main__':
    pairs=[(a,b) for a in mi for b in pl]
    with mp.get_context('fork').Pool(int(os.environ.get('NP','6'))) as P: res=[r for r in P.map(ev,pairs,chunksize=16) if r]
    json.dump(res,open(sys.argv[3],'w'))
    I=F.parse(RAW); slot=[0]
    for b in I: slot.append(slot[-1]+len(b)//8)
    for k1,k2,n,M in sorted(res,key=lambda r:-r[3])[:20]: print(hex(slot[k1]*8),hex(slot[k2]*8),n,M)
