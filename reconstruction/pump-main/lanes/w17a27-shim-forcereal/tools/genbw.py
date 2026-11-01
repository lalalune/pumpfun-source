#!/usr/bin/env python3
"""genbw.py <m.ll> <cells.jsonl> [p,p,..]: one cell per (conditional br in execute, p): set the br's !prof to
branch_weights round(p*2^31):round((1-p)*2^31) (p = probability of the TRUE successor). Experiment only."""
import sys,re,json
m,outp=sys.argv[1],sys.argv[2]
P=[float(x) for x in sys.argv[3].split(',')] if len(sys.argv)>3 else [0.0005,0.01,0.1,0.3,0.5,0.7,0.9,0.99,0.9995]
L=open(m).read().split('\n')
a=[i for i,l in enumerate(L) if l.startswith('define ') and 'admin_cto7execute' in l][0]; b=a
while L[b]!='}': b+=1
mx=max(int(x) for x in re.findall(r'^!(\d+) = ','\n'.join(L),re.M))
cells=[]; nb=0
for i in range(a,b):
    l=L[i]
    mm=re.match(r'^(\s+br i1 [^,]+, label %[^,]+, label %[^,\s]+)(, !prof !\d+)?(.*)$',l)
    if not mm: continue
    nb+=1
    for k,p in enumerate(P):
        wt=max(1,round(p*2**31)); wf=max(1,round((1-p)*2**31))
        nid=mx+1+k
        cells.append({'id':f'bw:{i}:{p}','ops':[['rep',i,mm.group(1)+f', !prof !{nid}'+mm.group(3)],['meta',f'!{nid} = !{{!"branch_weights", i32 {wt}, i32 {wf}}}']]})
with open(outp,'w') as f:
    for c in cells: f.write(json.dumps(c)+'\n')
print(nb,'branches',len(cells),'cells',file=sys.stderr)
