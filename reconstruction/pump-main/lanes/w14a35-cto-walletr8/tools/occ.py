#!/usr/bin/env python3
"""occ.py <ra.log> <vreg> [regs]: for each physreg, which assigned vregs (final assignment) overlap <vreg>'s segments."""
import sys,re,collections
log=open(sys.argv[1]).read().split('\n'); v=sys.argv[2]; regs=sys.argv[3].split(',') if len(sys.argv)>3 else None
iv={}; cur=None; asg={}
segre=re.compile(r'\[(\d+)([rBeRd]),(\d+)([rBeRd]):\d+\)')
for l in log:
    m=re.match(r'selectOrSplit GPR:(%\d+) (.*)',l)
    if m: iv[m.group(1)]=[(int(a),int(c)) for a,_,c,_ in segre.findall(m.group(2))]; continue
    m=re.match(r'assigning (%\d+) to \$(r\d+)',l)
    if m: asg[m.group(1)]=m.group(2)
    m=re.match(r'unassigning (%\d+) from \$(r\d+)',l)
    if m: asg.pop(m.group(1),None)
    m=re.match(r'queuing new interval: (%\d+) (.*)',l)
    if m: iv[m.group(1)]=[(int(a),int(c)) for a,_,c,_ in segre.findall(m.group(2))]
S=iv[v]
def ov(a,b):
    return sum(max(0,min(x2,y2)-max(x1,y1)) for x1,x2 in a for y1,y2 in b)
by=collections.defaultdict(list)
for r,p in asg.items():
    if r in iv:
        o=ov(S,iv[r])
        if o: by[p].append((o,r,iv[r][0][0],iv[r][-1][1]))
for p in sorted(by):
    if regs and p not in regs: continue
    print(p, sorted(by[p],reverse=True)[:8])
