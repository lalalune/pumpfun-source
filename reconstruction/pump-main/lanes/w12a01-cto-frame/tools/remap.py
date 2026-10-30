#!/usr/bin/env python3
"""remap.py <so> <map-spec>: remap r10 offsets of our admin_cto window by piecewise rules and report masked ratio.
map-spec: comma list of lo-hi:+d (offsets in [lo,hi] shift by d), hex."""
import sys, struct, difflib
sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w12a01-cto-frame/reconstruction/pump-main/lanes/w4-frame-oracle')
av=sys.argv; sys.argv=av[:1]
import frameoracle as fo
from pathlib import Path
sc=fo.load_score()
W={x['start']:x for x in sc.original_windows()}; orig=W[0x22a10]['raw']
src=av[1]; cs=Path(src).read_bytes(); secs=sc.sections(cs)
f=next(x for x in sc.candidate_functions(Path(src)) if 'admin_cto7execute' in x[2]); cand=sc.body(cs,secs,f[0],f[1])
rules=[]
if len(av)>2 and av[2]:
    for r in av[2].split(','):
        rng,d=r.split(':'); lo,hi=rng.split('-'); rules.append((int(lo,16),int(hi,16),int(d,16) if not d.startswith('-') else -int(d[1:],16)))
def mp(o):
    for lo,hi,d in rules:
        if lo<=o<=hi: return o+d
    return o
b=bytearray(cand); ins=fo.decode(cand)
for j,x in enumerate(ins):
    so=fo.stack_off(x)
    if so is not None:
        struct.pack_into('<h',b,x['i']+2,-mp(so))
    elif x['op']==0x07 and j>0 and ins[j-1]['op']==0xbf and ins[j-1]['src']==10 and ins[j-1]['dst']==x['dst']:
        struct.pack_into('<i',b,x['i']+4,-mp(-x['imm']))
def mtok(raw): return [fo.norm_calls(raw[x['i']:x['i']+x['k']]) for x in fo.decode(raw)]
print(f'{difflib.SequenceMatcher(None,mtok(orig),mtok(bytes(b)),autojunk=False).ratio():.5f}')
