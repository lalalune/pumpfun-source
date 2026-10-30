#!/usr/bin/env python3
"""sscmap.py <ssc.log> <pre_idx.txt> [lo hi]: stack-slot-coloring map. For each colour (FI -> r10 offset 0x8d0+8*(FI-177)),
list the spill intervals assigned to it that overlap slot-index window [lo,hi), with weight, def/use sites (from MIR)."""
import sys,re,collections
log=open(sys.argv[1]).read().split('Color spill slot intervals:')
iv={};w={}
for l in log[0].splitlines():
    m=re.match(r'SS#(\d+) (.*) 0@\S+\s+weight:(\S+)',l)
    if m:
        s=int(m.group(1)); w[s]=float(m.group(3))
        iv[s]=[(int(a),int(b)) for a,b in re.findall(r'\[(\d+)[rBed],(\d+)[rBed]',m.group(2))]
col={}
for a,b in re.findall(r'Assigning fi#(\d+) to fi#(\d+)',log[1]): col[int(a)]=int(b)
for s in iv: col.setdefault(s,s)
sites=collections.defaultdict(list)
for l in open(sys.argv[2]):
    m=re.match(r'(\d+)B\s+(.*%stack\.(\d+)\b.*)',l)
    if m: sites[int(m.group(3))].append((int(m.group(1)),m.group(2).strip()[:60]))
lo=int(sys.argv[3]) if len(sys.argv)>3 else 0; hi=int(sys.argv[4]) if len(sys.argv)>4 else 10**9
def ov(s): return any(a<hi and b>lo for a,b in iv[s])
bycol=collections.defaultdict(list)
for s,c in col.items():
    if s in iv and ov(s): bycol[c].append(s)
for c in sorted(bycol):
    for s in sorted(bycol[c],key=lambda s:-w[s]):
        st=sites.get(s,[]); 
        first=st[0] if st else ('-','');
        inwin=[x for x in st if lo<=x[0]<hi]
        print('col %d off 0x%x  SS#%d w=%.3g  span %d-%d  nsites %d inwin %d  first %s %s'%(c,0x8d0+8*(c-177),s,w[s],iv[s][0][0],iv[s][-1][1],len(st),len(inwin),first[0],first[1]))
