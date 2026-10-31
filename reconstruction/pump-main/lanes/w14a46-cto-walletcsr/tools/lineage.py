#!/usr/bin/env python3
"""lineage.py <ra.log> <vreg>...: split-parent chain of each vreg up to its pre-RA root, and the root's defs/uses in the
pre-RA MIR (the MACHINEINSTRS dump just before GREEDY)."""
import sys,re
log=open(sys.argv[1]).read().split('\n')
g=next(i for i,l in enumerate(log) if l.startswith('********** GREEDY'))
mi=next(i for i in range(g,0,-1) if log[i].startswith('********** MACHINEINSTRS'))
pre=log[mi:g]
parent={}; cur=None; seen=set()
for l in log[g:]:
    m=re.match(r'selectOrSplit GPR:(%\d+)',l)
    if m: cur=m.group(1); seen.add(cur); continue
    m=re.match(r'queuing new interval: (%\d+)',l)
    if m and m.group(1) not in seen and m.group(1) not in parent and cur and m.group(1)!=cur: parent[m.group(1)]=cur
for v in sys.argv[2:]:
    ch=[v]
    while ch[-1] in parent: ch.append(parent[ch[-1]])
    r=ch[-1]
    print(' <- '.join(ch))
    pat=re.compile(re.escape(r)+r'(:gpr)?\b')
    hits=[l for l in pre if pat.search(l) and re.match(r'\d+B\t',l)]
    for l in hits[:6]: print('   ',l.strip()[:160])
    if len(hits)>6: print('    ... %d more'%(len(hits)-6)); [print('   ',l.strip()[:160]) for l in hits[-3:]]
