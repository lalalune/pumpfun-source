#!/usr/bin/env python3
"""summ.py <prefix> [base_bytes base_M]: exact M for every results row whose name starts with prefix"""
import sys,os,json,glob,difflib
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a80-cto-stitch12')
T='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a80-cto-stitch12/reconstruction/pump-main/lanes/w14a80-cto-stitch12/tools'
exec(open(T+'/rx.py').read().split('OUT=os.environ')[0])
o=mask(orig_window())
pre=sys.argv[1]; bb=int(sys.argv[2]) if len(sys.argv)>2 else 27400; bm=int(sys.argv[3]) if len(sys.argv)>3 else 2220
rows=[]
for f in glob.glob(OUT+'/results-'+os.environ.get('SHA','*')+'.jsonl'):
    for l in open(f):
        r=json.loads(l)
        if not r['name'].startswith(pre): continue
        fb=f"{OUT}/t/{r['name']}/fn.bin"
        if not os.path.exists(fb): rows.append((r['name'],None,None,None,r.get('error','')[:60])); continue
        c=mask(open(fb,'rb').read()); M=sum(b.size for b in difflib.SequenceMatcher(None,o,c,autojunk=False).get_matching_blocks())
        b=len(open(fb,'rb').read()); cto=r.get('admin_cto') or {}
        rows.append((r['name'],b,M,cto.get('slots_diff'),f"L{len(r.get('losses') or [])}/{len(r.get('raw_losses') or [])}"))
rows.sort(key=lambda x:(-(x[2] or 0)+ (abs((x[1] or 0)-bb)/1000)))
for n,b,M,sd,ls in rows:
    if b is None: print(f'{n:28s} ERR {ls}'); continue
    print(f'{n:28s} {b:6d} {b-bb:+5d} M {M} {M-bm:+d} slots {sd} {ls}')
