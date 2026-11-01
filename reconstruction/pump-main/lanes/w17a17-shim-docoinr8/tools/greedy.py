#!/usr/bin/env python3
"""greedy.py <seed ids comma> <cands file: one id per line> <target bytes> <out.jsonl> [rounds]: greedy add edits maximizing M
(tie: closer to target bytes); stops when no improvement. Experiment only."""
import sys,os,json
OUT='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w17a17-shim-docoinr8'
sys.path.insert(0,OUT+'/tools'); os.environ['LANE_OUT']=OUT
import fx
from screenpt import apply
from concurrent.futures import ThreadPoolExecutor
L=open(OUT+'/ir/m0.s.ll').read().split('\n')
E={}
for l in open(OUT+'/scr/ed_m0.jsonl'):
    e=json.loads(l); E[e['id']]=e
seed=sys.argv[1].split(','); C=[x.strip() for x in open(sys.argv[2]) if x.strip()]; TB=int(sys.argv[3]); outf=sys.argv[4]; R=int(sys.argv[5]) if len(sys.argv)>5 else 6
def ev(ids):
    t=apply(L,[E[i] for i in ids])
    if t is None: return None
    nm='g'+str(abs(hash('+'.join(ids)))%10**9); r=fx.run(t,nm)
    import shutil; shutil.rmtree(os.path.join(fx.OUT,'fx',nm),ignore_errors=True)
    r['id']='+'.join(ids); return r
cur=seed; base=ev(cur); print('seed',base,flush=True)
def score(r): return (r['M'] - 0.05*abs(r['bytes']-TB)/8)
for rnd in range(R):
    jobs=[cur+[c] for c in C if c not in cur]
    with ThreadPoolExecutor(3) as ex: res=[r for r in ex.map(ev,jobs) if r and 'M' in r]
    with open(outf,'a') as f:
        for r in res: f.write(json.dumps(r)+'\n')
    ok=[r for r in res if r['bytes']<=TB+64]
    if not ok: break
    best=max(ok,key=lambda r:(score(r)))
    print('round',rnd,best['id'],best['M'],best['bytes'],flush=True)
    if score(best)<=score(base): break
    cur=best['id'].split('+'); base=best
print('final',base,flush=True)
