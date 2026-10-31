#!/usr/bin/env python3
"""bmap.py <x.s>: admin_cto execute block map: offset, insn count, IR name."""
import sys,re
L=open(sys.argv[1]).read().split('\n'); f=False; off=0; rows=[]; cur=None
for l in L:
    if re.match(r'^_ZN14pump_recovered9admin_cto7execute.*:',l): f=True; cur=['start',0,0]; rows.append(cur); continue
    if not f: continue
    if l.startswith('.Lfunc_end') or '-- End function' in l: break
    m=re.match(r'^(?:# %bb\.\d+:|LBB0_\d+:)\s*(?:#.*?%(\S+))?',l)
    if m:
        n=m.group(1) or '?'
        if 'to_string' in n: n=n.split('E.')[-1]
        cur=[n,off,0]; rows.append(cur); continue
    s=l.strip()
    if not s or s.startswith(('#','.')): continue
    k=16 if s.startswith('lddw') else 8
    off+=k; cur[2]+=k//8
for n,o,c in rows: print(f'{o:#06x} {c:4d} {n}')
