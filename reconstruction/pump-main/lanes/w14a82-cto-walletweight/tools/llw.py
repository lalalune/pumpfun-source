#!/usr/bin/env python3
"""llw.py <ra.log> [lo hi minov]: every root family with a final piece overlapping wallet slot range [lo,hi) by >= minov slots
(default: do_coin def .. +6800, 2000). For each piece: final reg or spill, weight at its last selectOrSplit, size, overlap.
Sorted by weight: this is the spill-weight order of the wallet's long-lived values."""
import sys,re,collections
L=sys.argv[1]; log=open(L).read(); lines=log.split('\n')
gi=log.index('********** GREEDY'); mi=log[:gi]; mi=mi[mi.rindex('********** MACHINEINSTRS'):]
m=re.search(r'(%\d+):gpr = COPY killed \$r0\n(\d+)B\t  (%\d+):gpr = MOV_ri 0\n\d+B\t  (%\d+):gpr = MOV_ri 0\n\d+B\t  JNE_ri \1:gpr, 0',mi)
lo=int(m.group(2)); hi=lo+6800; minov=2000
if len(sys.argv)>3: lo,hi=int(sys.argv[2]),int(sys.argv[3])
if len(sys.argv)>4: minov=int(sys.argv[4])
segre=re.compile(r'\[(\d+)[rBeRd],(\d+)[rBeRd]:\d+\)')
parent={}; seen=set(); cur=None; last={}; fate={}
for l in lines[lines.index('********** GREEDY REGISTER ALLOCATION **********') if '********** GREEDY REGISTER ALLOCATION **********' in lines else 0:]:
    m=re.match(r'selectOrSplit GPR:(%\d+) (.*?)\s+weight:(\S+)',l)
    if m:
        cur=m.group(1); seen.add(cur); last[cur]=( [(int(a),int(c)) for a,c in segre.findall(m.group(2))], float(m.group(3)) ); continue
    m=re.match(r'queuing new interval: (%\d+) (.*)',l)
    if m:
        v=m.group(1)
        if v not in seen and v not in parent and v!=cur: parent[v]=cur
        continue
    m=re.match(r'assigning (%\d+) to \$(r\d+)',l)
    if m: fate[m.group(1)]=m.group(2); continue
    m=re.match(r'unassigning (%\d+) from',l)
    if m: fate[m.group(1)]='evicted'; continue
    m=re.match(r'Inline spilling GPR:(%\d+)',l)
    if m: fate[m.group(1)]='SPILL'
def root(v):
    while v in parent: v=parent[v]
    return v
def d0(r):
    mm=re.search(r'\n(\d+)B\t  '+re.escape(r)+r':gpr = ([^\n]{0,70})',mi)
    return (mm.group(1)+' '+mm.group(2)) if mm else '?'
rows=[]
for v,(S,w) in last.items():
    f=fate.get(v,'?')
    if f=='evicted': continue
    o=sum(max(0,min(b,hi)-max(a,lo)) for a,b in S)
    if o>=minov: rows.append((w,v,root(v),f,sum(b-a for a,b in S),o))
print('wallet slots [%d,%d)'%(lo,hi))
for w,v,r,f,sz,o in sorted(rows,reverse=True):
    print('  w=%.3e %-6s root=%-6s %-6s sz=%6d ov=%5d  %s'%(w,v,r,f,sz,o,d0(r)))
