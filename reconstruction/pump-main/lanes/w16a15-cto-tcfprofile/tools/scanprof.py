#!/usr/bin/env python3
"""scanprof.py <out.jsonl>: abort-profile scan of every cached fn.bin capture (all lanes)."""
import sys,os,glob,json,hashlib
from multiprocessing import Pool
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from prof import rel
def ev(fb):
    try:
        raw=open(fb,'rb').read()
        d,t,js=rel(raw)
        r={'fb':fb,'bytes':len(raw),'h':hashlib.md5(raw).hexdigest()[:12]}
        if d is None: r['err']=f'cl{len(js)}'; return r
        r['cum']=d; r['good']=sum(1 for x in d if x==0); r['gt']=sum(1 for x in d[:25] if x==0); r['gs']=sum(1 for x in d[25:] if x==0)
        # TCF region hash (abort block .. last tcf jump + 8), masked call imm only
        r['th']=hashlib.md5(raw[t:js[24]+8]).hexdigest()[:12]; r['tlen']=js[24]+8-t
        return r
    except Exception as e: return {'fb':fb,'err':repr(e)[:100]}
if __name__=='__main__':
    fs=sorted(glob.glob(os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/*/rx/*/fn.bin')))
    with Pool(6) as p, open(sys.argv[1],'w') as f:
        for r in p.imap_unordered(ev,fs,chunksize=32): f.write(json.dumps(r)+'\n')
