#!/usr/bin/env python3
"""ovl.py <greedy.log> <vreg> <physreg>: final intervals on physreg overlapping vreg's (first) range set; also all-time assigned"""
import sys,re
log=open(sys.argv[1]).read().split('\n'); V=sys.argv[2]; P=sys.argv[3]
def segs(r): return [(int(a),int(b)) for a,b in re.findall(r'\[(\d+)[a-zA-Z],(\d+)[a-zA-Z]:',r)]
vr=None; cur={}; rng={}
for l in log:
    if vr is None and l.startswith('selectOrSplit GPR:'+V+' '): vr=segs(l)
    m=re.match(r'assigning (%\d+) to (\$r\d+): \S+ (.*)',l)
    if m: cur[m.group(1)]=m.group(2); rng[m.group(1)]=m.group(3); continue
    m=re.match(r'unassigning (%\d+) from',l)
    if m: cur.pop(m.group(1),None)
print('vreg',V,'segs',len(vr),'span',vr[0][0],vr[-1][1])
for v,reg in cur.items():
    if reg!=P: continue
    o=[(a,b) for a,b in segs(rng[v]) for c,d in vr if a<d and c<b]
    if o: print(v,'overlap',o[:6],len(o))
