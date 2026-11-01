#!/usr/bin/env python3
"""blk.py <cfg.json> <lo> <hi>: block list with calls and successors; error blocks tagged by the PumpError k_u32 constant
loaded before PumpError::name (from the .lst lddw comments)."""
import sys,json,re
d=json.load(open(sys.argv[1])); lo=int(sys.argv[2],16); hi=int(sys.argv[3],16)
lst=open(sys.argv[1].replace('.cfg.json','.lst')).read().split('\n')
err={}
for i,l in enumerate(lst):
    m=re.search(r"\+([0-9a-f]{5})\s+LDDW R2,0x[0-9a-f]+\s+; u32: u32 (\d+)",l)
    if m and i+1<len(lst) and 'PumpError::name' in lst[i+1]:
        err[int(m.group(1),16)]=m.group(2)
for b in d['blocks']:
    if not (lo<=b['off']<hi): continue
    tags=[f'E{v}' for k,v in err.items() if b['off']<=k<b['end']]
    s=' '.join(f"{x['kind'][0]}:{x['to']:x}" for x in b['succ'])
    c=','.join(x.split('::')[-1][:18] for x in b['calls'])
    print(f"{b['off']:5x}-{b['end']:5x} n{b['insns']:3d} {s:24s} {c:40s} {' '.join(tags)}")
