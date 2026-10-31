#!/usr/bin/env python3
"""ins.py <dir> [step]: insert one free 8 B frame slot at depth p (every offset <= -p moves by -8), M per p; best p then bestperm."""
import sys,os,json,multiprocessing as mp
O=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,O); import relab as R
d=sys.argv[1]; b=open(d+'/f.bin','rb').read()
offs=sorted({R.memoff(b,i) for i,n in R.ins(b) if R.memoff(b,i) is not None})
def sh(p): return {o:(o-8 if o<=-p else o) for o in offs}
def f(p): return (R.M(R.apply(b,sh(p))),p)
if __name__=='__main__':
    ps=list(range(2264,3200,8))
    with mp.Pool(6) as pool: res=sorted(pool.map(f,ps),reverse=True)
    print('base M',R.M(b)); print('top',res[:6])
    p=res[0][1]; b2=R.apply(b,sh(p))
    if os.path.exists(d+'/pei.mir'):
        sp={(o-8 if o<=-p else o) for o in R.spills(d+'/pei.mir')}|{-p}
        print('bestperm after insert at',p, R.bestperm(b2,sp,3)[0])
