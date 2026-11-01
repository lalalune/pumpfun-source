#!/usr/bin/env python3
"""slotmap.py <fn.bin|orig> [n]: per spill offset (<= -2264): k, ref count, first/last access offset, stores"""
import sys,os,struct
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import relab as R
def table(b):
    acc={}
    for i,n in R.ins(b):
        o=R.memoff(b,i)
        if o is None or o>-2264: continue
        st=(b[i]&7) in (2,3)
        acc.setdefault(o,[]).append((i,st,b[i+1]))
    return acc
if __name__=='__main__':
    b=R.ORIG if sys.argv[1]=='orig' else open(sys.argv[1],'rb').read(); n=int(sys.argv[2]) if len(sys.argv)>2 else 40
    acc=table(b)
    for o in sorted(acc,reverse=True)[:n]:
        L=acc[o]; k=(-2264-o)//8
        print(f"k={k:3d} {o} n={len(L):2d} first={L[0][0]:#06x} last={L[-1][0]:#06x} stores={sum(1 for x in L if x[1])}")
    print('nslots',len(acc))
