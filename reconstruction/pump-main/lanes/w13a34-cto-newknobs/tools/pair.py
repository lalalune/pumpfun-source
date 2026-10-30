#!/usr/bin/env python3
"""pair.py <results.jsonl> [--top N] [--emit prefix] : size-balanced pairs/triples of single knobs vs base (27400, base ratio)."""
import json,sys,itertools,runpy,os
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a34-cto-newknobs'
SRC='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w13a34-cto-newknobs/programs/pump/src/creator/admin_cto.rs'
a=sys.argv[1:]; R=a.pop(0); top=40; emit=None; base_ratio=float(os.environ.get('BASE_RATIO','0.57669'))
while a:
    x=a.pop(0)
    if x=='--top': top=int(a.pop(0))
    elif x=='--emit': emit=a.pop(0)
rows={}
for l in open(R):
    try: r=json.loads(l)
    except: continue
    if 'ratio' in r and not r['name'].startswith(('P_','T_')): rows[r['name']]=r
s=open(SRC).read()
def edits(n): return runpy.run_path(f'{O}/edits/{n}.py')['EDITS']
def compatible(ns):
    t=s
    for n in ns:
        for e in edits(n):
            a_,b_=e
            if t.count(a_)!=1: return False
            t=t.replace(a_,b_)
    return t
S=[(n,r['bytes']-27400,r['ratio']-base_ratio) for n,r in rows.items() if not r.get('eq_main')]
cands=[]
for k in (2,3):
    for c in itertools.combinations(S,k):
        db=sum(x[1] for x in c); dr=sum(x[2] for x in c)
        if db==0 and dr>0 and all(x[1]!=0 for x in c): cands.append((dr,[x[0] for x in c],[(x[1],round(x[2],5)) for x in c]))
for n,db,dr in S:
    if db==0 and dr>0: cands.append((dr,[n],[(db,round(dr,5))]))
cands.sort(key=lambda x:-x[0])
out=[]
for dr,ns,info in cands:
    if len(out)>=top: break
    if compatible(ns) is False: continue
    out.append((dr,ns,info)); print(round(dr,5),'+'.join(ns),info)
if emit:
    L=[]
    for i,(dr,ns,info) in enumerate(out):
        nm=f'{emit}{i:02d}'; E=[e for n in ns for e in edits(n)]
        open(f'{O}/edits/{nm}.py','w').write('# '+'+'.join(ns)+'\nEDITS='+repr(E)+'\n'); L.append(nm)
    open(f'{O}/hc/{emit}list.txt','w').write('\n'.join(L)+'\n')
