#!/usr/bin/env python3
"""overlap.py <dir> <class vreg>: MIR blocks (pre-RA dump after coalescing) where %0 has a use and the class vreg is live."""
import sys,re
d,cv=sys.argv[1],sys.argv[2]
L=open(d+'/ra.log').read().split('\n')
# pre-greedy MIR = 2nd MACHINEINSTRS dump
idx=[i for i,l in enumerate(L) if l.startswith('********** MACHINEINSTRS')]
mi=L[idx[1]:]
blocks=[];cur=None
for l in mi:
    m=re.match(r'^(\d+)B\t(bb\.\d+\S*):',l)
    if m: cur=[m.group(2),int(m.group(1)),None,[]]; blocks.append(cur); continue
    m=re.match(r'^(\d+)B\t',l)
    if m and cur is not None:
        cur[2]=int(m.group(1))
        if re.search(r'%0:gpr(?!\d)',l) and not re.search(r'^\d+B\t\s*%0:gpr = ',l): cur[3].append(int(m.group(1)))
    if l.startswith('# End machine code'): break
seg=None
for l in L:
    if l.startswith('selectOrSplit GPR:%'+cv+' '):
        seg=[(int(a),int(b)) for a,b in re.findall(r'\[(\d+)[rBd],(\d+)[rBd]',l)]; break
tot=0
for name,s,e,uses in blocks:
    if not uses: continue
    ov=[x for x in seg if x[0]<e and x[1]>s]
    if ov: tot+=1; print(name,s,e,'uses',uses[:3],'class',ov[:3])
print('blocks with %0 uses and class live:',tot)
