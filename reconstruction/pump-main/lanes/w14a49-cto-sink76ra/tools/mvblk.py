#!/usr/bin/env python3
"""mvblk.py <in.s> <out.s> <label> <after_label_or_line_marker>: cut the block starting at '<label>:' (up to the next
label line 'LBB...:' or '# %bb.'), and paste it right before the line of the block whose label is <before>. Placement-only
bound (registers/frame unchanged). Block must end in ja/exit (no fallthrough) and the block before it too."""
import sys,re
src,dst,lab,before=sys.argv[1:5]
L=open(src).read().split('\n')
def isstart(l): return re.match(r'^(LBB0_\d+:|# %bb\.\d+:)',l) is not None
i=[k for k,l in enumerate(L) if l.startswith(lab+':')][0]
j=i+1
while not isstart(L[j]) and not L[j].startswith('.Lfunc_end0'): j+=1
blk=L[i:j]
last=[l for l in blk if l.strip() and not l.strip().startswith('#')][-1].strip()
prev=[l for l in L[:i] if l.strip() and not l.strip().startswith('#') and not isstart(l)][-1].strip()
assert last.startswith('ja ') or last=='exit', last
assert prev.startswith('ja ') or prev=='exit', ('prev falls through',prev)
R=L[:i]+L[j:]
b=[k for k,l in enumerate(R) if l.startswith(before+':') or l.startswith('# '+before+':')][0]
# the block before the insertion point must not fall through into 'before'
pv=[l for l in R[:b] if l.strip() and not l.strip().startswith('#') and not isstart(l)][-1].strip()
if not (pv.startswith('ja ') or pv=='exit'):
    print('WARN: block before insertion falls through; adding ja',before, file=sys.stderr)
    blk=blk  # keep; fallthrough into blk would break semantics -> add explicit jump before blk
    if before.startswith('LBB'): blk=['\tja '+before]+blk
    else: raise SystemExit('cannot insert before unlabeled fallthrough block')
R=R[:b]+blk+R[b:]
open(dst,'w').write('\n'.join(R))
