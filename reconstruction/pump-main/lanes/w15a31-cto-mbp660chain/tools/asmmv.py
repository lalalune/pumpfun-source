#!/usr/bin/env python3
"""asmmv.py in.s out.s START END BEFORE: placement-only asm oracle (experiment only). Cut the lines from label START up to
(excl) label END and paste them right before label BEFORE. Adds 'ja X' where a cut or paste would change a fallthrough, and
drops a 'ja L' that becomes a jump to the next label. Labels are given as the text before ':' (e.g. LBB0_205)."""
import sys,re
src,dst,S,E,B=sys.argv[1:6]
L=open(src).read().split('\n')
def islab(l): return re.match(r'^(LBB\d+_\d+:|# %bb\.\d+:)',l) is not None
def lab(l):
    m=re.match(r'^(LBB\d+_\d+):',l); return m[1] if m else None
def lastins(seg):
    for l in reversed(seg):
        s=l.strip()
        if s and not s.startswith('#') and not islab(l) and not s.startswith('.'): return s
    return ''
def falls(seg):
    li=lastins(seg); return not (li.startswith('ja ') or li=='exit' or li.startswith('ja\t'))
idx=lambda name:[k for k,l in enumerate(L) if l.startswith(name+':')][0]
i,j,b=idx(S),idx(E),idx(B)
chain=L[i:j]; rest=L[:i]+L[j:]
if falls(chain): chain=chain+['\tja '+E]
pre_cut=L[:i]
add_cut = falls(pre_cut)  # block before START fell into START; now it would fall into END
b2=[k for k,l in enumerate(rest) if l.startswith(B+':')][0]
pre_ins=rest[:b2]
add_ins = falls(pre_ins)
out=rest[:b2]+(['\tja '+B] if add_ins else [])+chain+rest[b2:]
if add_cut:
    k=[t for t,l in enumerate(out) if l.startswith(E+':')][0]; out.insert(k,'\tja '+S)
# drop 'ja X' immediately followed (ignoring comments/labels-less lines) by label X
res=[]
for k,l in enumerate(out):
    s=l.strip()
    m=re.match(r'^ja\s+(LBB\d+_\d+)$',s)
    if m:
        n=k+1
        while n<len(out) and (out[n].strip()=='' or out[n].strip().startswith('#') or out[n].strip().startswith('.p2align')): n+=1
        if n<len(out) and out[n].startswith(m[1]+':'): continue
    res.append(l)
open(dst,'w').write('\n'.join(res))
print('add_cut',add_cut,'add_ins',add_ins,'chain_lines',len(chain))
