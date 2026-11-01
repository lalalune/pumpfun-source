#!/usr/bin/env python3
"""climb2.py <m.ll> <out.log> gene...: greedy sticky RAPRIO climb over a given gene list, keeping 27400 B only
(--any allows any size). Experiment only."""
import sys,os,json,subprocess,hashlib
from concurrent.futures import ThreadPoolExecutor
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle,fscr
OUT=os.path.dirname(T)
a=sys.argv[1:]; anysz='--any' in a; a=[x for x in a if x!='--any']
m,logf=a[0],a[1]; genes=a[2:]
def run(forces):
    env=dict(os.environ,RAPRIO_STICKY='1',RAPRIO_FORCE=','.join(forces))
    k=hashlib.sha1(','.join(forces).encode()).hexdigest()[:10]; o=f'{OUT}/lx/c2_{k}.o'
    r=subprocess.run([fscr.LLC['p'],*fscr.LLCA,m,'-filetype=obj','-o',o],env=env,capture_output=True,text=True)
    if r.returncode: return None
    b=oracle.elf_fn(o,oracle.KEEP); os.remove(o)
    return {'forces':forces,'M':len(fscr.mset(fscr.toks(b))),'bytes':len(b)}
lg=open(logf,'w'); cur=[]; best=run([]); lg.write(json.dumps(best)+'\n'); lg.flush()
with ThreadPoolExecutor(6) as ex:
    while True:
        tr=[g for g in genes if g.split('=')[0] not in [c.split('=')[0] for c in cur]]
        res=[r for r in ex.map(run,[cur+[g] for g in tr]) if r]
        ok=[r for r in res if anysz or r['bytes']==27400]
        if not ok: break
        x=max(ok,key=lambda r:r['M'])
        if x['M']<=best['M']: break
        cur=x['forces']; best=x; lg.write(json.dumps(best)+'\n'); lg.flush()
lg.write(json.dumps({'final':best})+'\n')
