#!/usr/bin/env python3
"""occat.py <ra.log> <vreg> <line>: physreg occupancy overlapping <vreg> (its interval at <line>) as of log line <line>."""
import sys,re,collections
log=open(sys.argv[1]).read().split('\n'); v=sys.argv[2]; upto=int(sys.argv[3])
segre=re.compile(r'\[(\d+)[rBeRd],(\d+)[rBeRd]:\d+\)')
iv={}; asg={}
for k,l in enumerate(log[:upto]):
    m=re.match(r'(?:selectOrSplit GPR:|queuing new interval: )(%\d+) (.*)',l)
    if m: iv[m.group(1)]=[(int(a),int(c)) for a,c in segre.findall(m.group(2))]
    m=re.match(r'assigning (%\d+) to \$(r\d+): \w+ (.*)',l)
    if m: asg[m.group(1)]=m.group(2); iv[m.group(1)]=[(int(a),int(c)) for a,c in segre.findall(m.group(3))]
    m=re.match(r'unassigning (%\d+) from \$(r\d+)',l)
    if m: asg.pop(m.group(1),None)
m=re.match(r'selectOrSplit GPR:(%\d+) (.*)',log[upto-1]) 
S=iv[v]
by=collections.defaultdict(list)
for r,p in asg.items():
    o=[(max(x1,y1),min(x2,y2)) for x1,x2 in S for y1,y2 in iv.get(r,[]) if min(x2,y2)>max(x1,y1)]
    if o: by[p].append((sum(b-a for a,b in o),r,o[0][0],o[-1][1]))
for p in ['r0','r1','r2','r3','r4','r5','r6','r7','r8','r9']:
    print(p, sorted(by.get(p,[]),reverse=True)[:6])
