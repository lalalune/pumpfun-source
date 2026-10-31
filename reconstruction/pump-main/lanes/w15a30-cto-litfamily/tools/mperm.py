#!/usr/bin/env python3
"""mperm.py <name>... : M and Mperm (spill-slot relabel bound, relab.binspills+bestperm) for rx/<name>/fn.bin. Experiment only."""
import sys,os,json,multiprocessing as mp
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import relab
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w15a30-cto-litfamily')
def one(n):
    f=f'{OUT}/rx/{n}/fn.bin'
    if not os.path.exists(f): return {'name':n,'error':'nofn'}
    b=open(f,'rb').read(); sp=relab.binspills(b)
    m=relab.M(b); mb,pm=relab.bestperm(b,sp,3)
    return {'name':n,'bytes':len(b),'M':m,'Mperm':mb,'nspill':len(sp)}
if __name__=='__main__':
    names=sys.argv[1:]
    with mp.get_context('fork').Pool(int(os.environ.get('NP','4'))) as P:
        for r in P.imap_unordered(one,names):
            print(json.dumps(r),flush=True)
