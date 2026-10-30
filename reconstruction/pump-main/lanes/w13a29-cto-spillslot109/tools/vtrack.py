#!/usr/bin/env python3
"""vtrack.py <m.o> which lo hi accreg: name register values (acct K field f) in a straight-line range; print spill stores/loads with value names."""
import sys,re,os
sys.path.insert(0,os.path.dirname(__file__))
from slots import orig_dis,cand_dis
p,which,lo,hi,acc=sys.argv[1],sys.argv[2],int(sys.argv[3],16),int(sys.argv[4],16),sys.argv[5]
d=orig_dis() if which=='o' else cand_dis(p)
FN={0:'key',8:'lam',0x10:'dat',0x18:'own',0x20:'rent',0x28:'sig',0x29:'wr',0x2a:'exe'}
R={acc:'ACC'}; slot={}
out=[]
for pc,s in d:
    if not(lo<=pc<hi): continue
    m=re.match(r'(ldx\w+) (r\d), \[(r\d+) ([+-]) 0x([0-9a-f]+)\]',s)
    if m:
        op,dst,base,sg,o=m.groups(); o=int(o,16)
        if base=='r10':
            v=slot.get(o,'?%x'%o); R[dst]=v; out.append('%x L %-4x %s -> %s'%(pc,o,v,dst)); continue
        bv=R.get(base,'?')
        if bv=='ACC': R[dst]='A%x'%o
        elif bv.startswith('A') and '.' not in bv: R[dst]='%s.%s'%(bv,FN.get(o,hex(o)))
        else: R[dst]='*%s+%x'%(bv,o)
        continue
    m=re.match(r'stxdw \[r10 - 0x([0-9a-f]+)\], (r\d)',s)
    if m:
        o=int(m.group(1),16); v=R.get(m.group(2),'?'); slot[o]=v
        if o>=0x8d8: out.append('%x S %-4x %s (%s)'%(pc,o,v,m.group(2)))
        continue
    m=re.match(r'mov64 (r\d), (r\d+)$',s)
    if m: R[m.group(1)]=R.get(m.group(2),'?'); continue
    m=re.match(r'(\w+) (r\d)',s)
    if m and not s.startswith(('st','j','call')): R[m.group(2)]='t'
print('\n'.join(out))
