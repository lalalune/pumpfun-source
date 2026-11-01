#!/usr/bin/env python3
"""qcompl.py <listfile> <out.jsonl> SITES...: qflip composition over a list of fn.bin paths (experiment only)."""
import sys,os,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import relab as R, qflip
from concurrent.futures import ProcessPoolExecutor
S=sys.argv[3:]
def ev(p):
    try:
        b=open(p,'rb').read(); r={'p':p,'bytes':len(b),'M':R.M(b)}
        c=qflip.apply(b,S)
        if c: r.update({'cbytes':len(c),'cM':R.M(c)})
        return r
    except Exception as e: return {'p':p,'error':repr(e)[:100]}
if __name__=='__main__':
    ps=[l.strip() for l in open(sys.argv[1]) if l.strip()]
    with ProcessPoolExecutor(int(os.environ.get('NP','4'))) as ex, open(sys.argv[2],'w') as f:
        for r in ex.map(ev,ps,chunksize=2): f.write(json.dumps(r)+'\n'); f.flush()
