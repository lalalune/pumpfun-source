#!/usr/bin/env python3
"""qcomp.py <rxdir> <out.jsonl> SITES...: M of each <rxdir>/*/fn.bin and of the qflip composition (experiment only)."""
import sys,os,json,glob
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import relab as R, qflip
from concurrent.futures import ProcessPoolExecutor
S=sys.argv[3:]
def ev(p):
    b=open(p,'rb').read(); r={'name':p.split('/')[-2],'bytes':len(b),'M':R.M(b)}
    c=qflip.apply(b,S)
    if c: r.update({'cbytes':len(c),'cM':R.M(c)})
    return r
if __name__=='__main__':
    ps=sorted(glob.glob(sys.argv[1]+'/*/fn.bin'))
    with ProcessPoolExecutor(int(os.environ.get('NP','4'))) as ex, open(sys.argv[2],'w') as f:
        for r in ex.map(ev,ps,chunksize=4): f.write(json.dumps(r)+'\n')
