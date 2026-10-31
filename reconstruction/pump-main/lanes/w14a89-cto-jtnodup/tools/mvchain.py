#!/usr/bin/env python3
"""mvchain.py in.s out.s START END JALINE: cut lines from 'START:' up to (excl) 'END:' and paste them in place of the
'ja START' at 1-based line JALINE (so that block now falls through into the chain). Adds 'ja START' where the line before
START fell through, and 'ja <next>' if the chain's last insn falls through. Placement-only bound (experiment only)."""
import sys,re
src,dst,S,E,JL=sys.argv[1:6]; JL=int(JL)-1
L=open(src).read().split('\n')
def islab(l): return re.match(r'^(LBB0_\d+:|# %bb\.\d+:)',l) is not None
def lastins(seg):
    for l in reversed(seg):
        s=l.strip()
        if s and not s.startswith('#') and not islab(l) and not s.startswith('.'): return s
i=[k for k,l in enumerate(L) if l.startswith(S+':')][0]; j=[k for k,l in enumerate(L) if l.startswith(E+':')][0]
assert L[JL].strip()=='ja '+S,(L[JL])
chain=L[i:j]
li=lastins(chain)
if not (li.startswith('ja ') or li=='exit'): chain=chain+['\tja '+E]
pre=lastins(L[:i]); fix_pre=not (pre.startswith('ja ') or pre=='exit')
out=[]
for k,l in enumerate(L):
    if i<=k<j: continue
    if k==i-1 and fix_pre:
        out.append(l); continue
    if k==JL: out.extend(chain); continue
    out.append(l)
    if fix_pre and k==i-1: pass
if fix_pre:
    # insert 'ja S' right before E label position (where the chain was cut) i.e. at end of the block preceding START
    idx=[k for k,l in enumerate(out) if l.startswith(E+':')][0]
    out.insert(idx,'\tja '+S)
open(dst,'w').write('\n'.join(out))
print('fix_pre',fix_pre,'chain lines',len(chain))
