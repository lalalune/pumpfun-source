#!/usr/bin/env python3
"""dbgocc.py <ra.txt (llc -debug-only=regalloc)> <vreg> [regs...]: at the selectOrSplit of <vreg> (first, or --nth N),
replay assigning/unassigning lines and list per register the assigned intervals overlapping <vreg>'s segments,
with weights. Experiment only."""
import sys,re,collections
a=sys.argv[1:]; f=a.pop(0); v=a.pop(0); nth=1
if '--nth' in a: i=a.index('--nth'); nth=int(a[i+1]); del a[i:i+2]
regs=a or ['$r6','$r7','$r8','$r9']
SL={'B':0,'e':1,'r':2,'d':3}
def segs(s):
    return [(int(x)*4+SL[p],int(y)*4+SL[q]) for x,p,y,q in re.findall(r'\[(\d+)([Berd]),(\d+)([Berd]):\d+\)',s)]
asg={}; W={}; seen=0; tgt=None
for ln,l in enumerate(open(f),1):
    m=re.match(r'selectOrSplit GPR:%(\d+) (.*) w=(\S+)',l)
    if m:
        W[m.group(1)]=m.group(3)
        if m.group(1)==v:
            seen+=1
            if seen==nth: tgt=segs(m.group(2)); stopline=ln; break
    m=re.match(r'assigning %(\d+) to (\$r\d+): \S+ (.*)',l)
    if m: asg[m.group(1)]=(m.group(2),segs(m.group(3))); continue
    m=re.match(r'unassigning %(\d+) from (\$r\d+)',l)
    if m: asg.pop(m.group(1),None)
if tgt is None: sys.exit('not found')
print('target %%%s segs %s (line %d)'%(v,[(x//4,y//4) for x,y in tgt][:6],stopline))
def ov(s,t):
    for x,y in s:
        for p,q in t:
            if x<q and p<y: return (max(x,p)//4,min(y,q)//4)
    return None
for r in regs:
    hits=[]
    for k,(rr,s) in asg.items():
        if rr!=r: continue
        o=ov(s,tgt)
        if o: hits.append((k,o,W.get(k,'?'),s[0][0]//4,s[-1][1]//4))
    print(r,' '.join('%%%s@%s w=%s [%d..%d]'%(k,o,w,b,e) for k,o,w,b,e in hits) or 'FREE')
