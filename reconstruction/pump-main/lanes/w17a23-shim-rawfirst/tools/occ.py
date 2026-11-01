#!/usr/bin/env python3
"""occ.py <ra.txt> <stop_line> <lo> <hi> [regs]: replay greedy assign/unassign up to stop_line; list vregs whose
assigned ranges overlap [lo,hi) per physreg."""
import sys,re
p=sys.argv[1]; stop=int(sys.argv[2]); lo=int(sys.argv[3]); hi=int(sys.argv[4])
regs=sys.argv[5].split(',') if len(sys.argv)>5 else ['r6','r7','r8','r9']
def rng(s):
    out=[]
    for a,b in re.findall(r'\[(\d+)[rBed](?:-phi)?,(\d+)[rBed]',s): out.append((int(a),int(b)))
    return out
cur={}  # vreg -> (reg, ranges)
for i,l in enumerate(open(p)):
    if i+1>=stop: break
    m=re.match(r'assigning (%\d+) to \$(r\d+): \w+ (.*)',l)
    if m: cur[m.group(1)]=(m.group(2),rng(m.group(3))); continue
    m=re.match(r'unassigning (%\d+) from \$(r\d+)',l)
    if m: cur.pop(m.group(1),None)
for r in regs:
    hits=[]
    for v,(rr,R) in cur.items():
        if rr!=r: continue
        ov=[(a,b) for a,b in R if a<hi and b>lo]
        if ov: hits.append((v,ov[:4]))
    print(r,hits)
