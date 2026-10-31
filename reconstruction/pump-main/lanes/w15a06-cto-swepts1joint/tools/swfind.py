#!/usr/bin/env python3
"""swfind.py <prc.mir>: print '<vreg> <bb>' for swept: the last STD into _55.* +184 and the block of its single def"""
import sys,re
L=open(sys.argv[1]).read().split('\n')
st=[l for l in L if re.match(r'\s+STD_V1 (killed )?%\d+, %stack\.\d+\._55\.i\d+, 184 ',l)][-1]
v=re.search(r'STD_V1 (?:killed )?(%\d+)',st).group(1)
bb=None; defs=[]
for l in L:
    m=re.match(r'^  bb\.(\d+)',l)
    if m: bb=m.group(1)
    if re.match(r'^\s+'+re.escape(v)+r':gpr = ',l): defs.append((bb,l.strip()))
assert len(defs)==1,defs
print(v,defs[0][0]); print(defs[0][1],file=sys.stderr)
