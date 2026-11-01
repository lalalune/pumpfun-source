#!/usr/bin/env python3
"""tab.py [res.jsonl]: tabulate this lane's captures: M, bytes, abort profile (good/gt/gs), per-segment delta vs main
(TCF segs 0-24, gap 25, sharing 26-40), c2 marker (accounts+0xe8 load register; orig r6) and the hunk count vs main."""
import sys,os,json,glob
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w16a15-cto-tcfprofile/reconstruction/pump-main/lanes/w16a15-cto-tcfprofile/tools')
import mk, splice as S
EXCL={'hOKLD','hOKld','hokLD','pKDOL','pKdOL','pKDoL','gKOld','gkoLD','qLkD','qlkd','qLKd','qlKD'}  # case-insensitive rx/ collisions (macOS): superseded by x01..x13
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w16a15-cto-tcfprofile')
MAIN=open(OUT+'/an/main.bin','rb').read(); B=S.parse(MAIN)
off=[0]
for b in B: off.append(off[-1]+len(b))
def hunks(raw):
    v=S.Var(B,raw); return [(off[i1],off[i2]) for i1,i2,j1,j2 in v.hunks]
rows=[]
for f in sorted(glob.glob(OUT+'/res-*.jsonl')):
    for l in open(f):
        r=json.loads(l)
        if r['name'] in EXCL: continue
        if 'error' in r: rows.append((r['name'],r.get('genes'),None,r['error'][:80])); continue
        fb=f'{OUT}/rx/{r["name"]}/fn.bin'
        if not os.path.exists(fb): continue
        raw=open(fb,'rb').read(); a=mk.an(raw); h=hunks(raw)
        a['hunks']=len(h); a['hspan']=(hex(h[0][0]),hex(h[-1][1])) if h else None
        rows.append((r['name'],r.get('genes'),a,None))
for n,g,a,e in rows:
    if e: print(f'{n:10s} {g:28s} ERR {e}'); continue
    ds=a.get('dseg') or []
    nz=' '.join(f'{i}:{d:+d}' for i,d in enumerate(ds) if d)
    print(f"{n:10s} {g[:28]:28s} {a['bytes']} M {a['M']} ({a['M']-2251:+d}) good {a.get('good')} t{a.get('gt')} s{a.get('gs')} e8 {','.join(a['e8'])} 3370 {a['mk']['0x3370']} h{a['hunks']} {a['hspan']} | {nz}")
