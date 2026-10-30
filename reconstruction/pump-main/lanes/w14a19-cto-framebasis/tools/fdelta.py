#!/usr/bin/env python3
"""fdelta.py <ref xdir> <var xdir> : frame-object delta (MIR, post-PEI). Aligns object lists by (name-stem,size) in
frame-index (offset) order, prints inserted/removed objects and the running offset shift, plus the spill block start."""
import sys,re,difflib
def rd(x):
    R=[]
    for l in open(x+'/frame.txt'):
        p=l.split(); R.append((int(p[0],16),int(p[1]),int(p[2]),p[3]))
    return R
def key(o): n=re.sub(r'\d+$','',re.sub(r'^_\d+','_N',o[3])) if not o[3].startswith('#') else '#'; return (n,o[1])
a=rd(sys.argv[1]); b=rd(sys.argv[2]); ka=[key(o) for o in a]; kb=[key(o) for o in b]
first_sp=lambda R: next((o for o in R if o[3].startswith('#') and o[1]==8),None)
out=[]
for t,i1,i2,j1,j2 in difflib.SequenceMatcher(None,ka,kb,autojunk=False).get_opcodes():
    if t=='equal':
        sh=set(b[j][0]-a[i][0] for i,j in zip(range(i1,i2),range(j1,j2)))
        out.append(f"= {i2-i1:3d} objs {a[i1][3]}..{a[i2-1][3]} shift {sorted(sh)}")
    else:
        if i2>i1: out.append(f"- "+' '.join(f"{o[3]}:{o[1]}/{o[2]}@{o[0]:#x}" for o in a[i1:i2]))
        if j2>j1: out.append(f"+ "+' '.join(f"{o[3]}:{o[1]}/{o[2]}@{o[0]:#x}" for o in b[j1:j2]))
sa,sb=first_sp(a),first_sp(b)
print('\n'.join(out)); print(f"spill start {sa[0]:#x} -> {sb[0]:#x} ({sb[0]-sa[0]:+d}); nspill {sum(1 for o in a if o[3].startswith('#') and o[1]==8)} -> {sum(1 for o in b if o[3].startswith('#') and o[1]==8)}; n16 {sum(1 for o in a if o[1]==16 and o[3].startswith('#'))} -> {sum(1 for o in b if o[1]==16 and o[3].startswith('#'))}")
