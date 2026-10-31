#!/usr/bin/env python3
"""csrmap.py <ra.log> <lo> <hi> [regs=r6,r7,r8,r9]: every final vreg assigned to a callee-saved reg whose live range
overlaps slot range [lo,hi), with overlap, its split root and the root's first def (pre-RA MIR)."""
import sys,re,collections
log=open(sys.argv[1]).read().split('\n'); lo,hi=int(sys.argv[2]),int(sys.argv[3])
regs=(sys.argv[4] if len(sys.argv)>4 else 'r6,r7,r8,r9').split(',')
g=next(i for i,l in enumerate(log) if l.startswith('********** GREEDY'))
mi=next(i for i in range(g,0,-1) if log[i].startswith('********** MACHINEINSTRS'))
pre=log[mi:g]
segre=re.compile(r'\[(\d+)[rBeRd],(\d+)[rBeRd]:\d+\)')
iv={}; asg={}; parent={}; cur=None; seen=set()
for l in log[g:]:
    m=re.match(r'selectOrSplit GPR:(%\d+) (.*)',l)
    if m: cur=m.group(1); seen.add(cur); iv[cur]=[(int(a),int(c)) for a,c in segre.findall(m.group(2))]; continue
    m=re.match(r'queuing new interval: (%\d+) (.*)',l)
    if m:
        v=m.group(1); iv[v]=[(int(a),int(c)) for a,c in segre.findall(m.group(2))]
        if v not in seen and v not in parent and cur and v!=cur: parent[v]=cur
    m=re.match(r'assigning (%\d+) to \$(r\d+): \w+ (.*)',l)
    if m: asg[m.group(1)]=m.group(2); iv[m.group(1)]=[(int(a),int(c)) for a,c in segre.findall(m.group(3))]
    m=re.match(r'unassigning (%\d+) from \$(r\d+)',l)
    if m: asg.pop(m.group(1),None)
def root(v):
    while v in parent: v=parent[v]
    return v
def d0(r):
    pat=re.compile(re.escape(r)+r':gpr = ')
    for l in pre:
        if pat.search(l): return l.strip()[:110]
    return '?'
def nuses(r):
    pat=re.compile(re.escape(r)+r'(:gpr)?\b'); return sum(1 for l in pre if re.match(r'\d+B\t',l) and pat.search(l))
out=collections.defaultdict(list)
for v,p in asg.items():
    if p not in regs: continue
    o=sum(max(0,min(b,hi)-max(a,lo)) for a,b in iv.get(v,[]))
    if o>0: out[p].append((o,v,iv[v][0][0],iv[v][-1][1]))
for p in regs:
    print(p)
    for o,v,a,b in sorted(out[p],reverse=True)[:8]:
        r=root(v); print('  %5d %-6s [%d,%d) root %-6s uses=%d  %s'%(o,v,a,b,r,nuses(r),d0(r)))
