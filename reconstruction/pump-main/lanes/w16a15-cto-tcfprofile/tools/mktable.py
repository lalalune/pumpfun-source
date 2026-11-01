#!/usr/bin/env python3
"""mktable.py: markdown table of this lane's captures (name, genes, bytes, M, dM, abort good total/TCF/sharing,
per-segment delta vs main, c2 marker at orig 0x3078 / 0x3370) + JSON dump."""
import sys,os,json,glob
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w16a15-cto-tcfprofile/reconstruction/pump-main/lanes/w16a15-cto-tcfprofile/tools')
import mk
EXCL={'hOKLD','hOKld','hokLD','pKDOL','pKdOL','pKDoL','gKOld','gkoLD','qLkD','qlkd','qLKd','qlKD'}  # case-insensitive rx/ collisions (macOS): superseded by x01..x13
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w16a15-cto-tcfprofile')
rows=[]
for f in sorted(glob.glob(OUT+'/res-*.jsonl')):
    for l in open(f):
        r=json.loads(l)
        if r['name'] in EXCL: continue
        if 'error' in r: rows.append({'name':r['name'],'genes':r.get('genes'),'error':r['error'][:60].replace('\n',' ')}); continue
        a=mk.an(open(f'{OUT}/rx/{r["name"]}/fn.bin','rb').read())
        rows.append({'name':r['name'],'genes':r.get('genes'),'bytes':a['bytes'],'M':a['M'],'dM':a['M']-2251,'good':a.get('good'),'gt':a.get('gt'),'gs':a.get('gs'),
                     'dseg':{i:d for i,d in enumerate(a.get('dseg') or []) if d},'m3078':a['mk']['0x3078'],'m3370':a['mk']['0x3370'],'eq_main':r.get('eq_main')})
json.dump(rows,open(sys.argv[1],'w'),indent=0)
L=['| name | genes | bytes | M (dM) | abort good (TCF/sh) | segment deltas vs main (seg:B) | 0x3078 / 0x3370 |','| --- | --- | ---: | ---: | --- | --- | --- |']
for r in rows:
    if 'error' in r: L.append(f"| {r['name']} | `{r['genes']}` | | compile error | | | |"); continue
    ds=' '.join(f'{k}:{v:+d}' for k,v in r['dseg'].items()) or ('= main' if r['eq_main'] else '-')
    L.append(f"| {r['name']} | `{r['genes']}` | {r['bytes']} | {r['M']} ({r['dM']:+d}) | {r['good']} ({r['gt']}/{r['gs']}) | {ds} | {r['m3078']} / {r['m3370']} |")
open(sys.argv[2],'w').write('\n'.join(L)+'\n'); print(len(rows),'rows')
