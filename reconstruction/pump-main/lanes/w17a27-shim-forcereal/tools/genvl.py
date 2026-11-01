#!/usr/bin/env python3
"""genvl.py <m.ll> <cells.jsonl>: one cell per load in the post-opt execute body: load -> load volatile (models
read_volatile of that field). Experiment only."""
import sys,re,json
m,outp=sys.argv[1],sys.argv[2]
L=open(m).read().split('\n')
s=[i for i,l in enumerate(L) if l.startswith('define ') and 'admin_cto7execute' in l][0]; e=s
while L[e]!='}': e+=1
cells=[]
for i in range(s+1,e):
    l=L[i]
    mm=re.match(r'^(\s+%[\w.$"-]+ = )load (?!volatile)(.*)$',l)
    if not mm: continue
    cells.append({'id':f'vl:{i}','ops':[['rep',i,mm.group(1)+'load volatile '+mm.group(2)]]})
with open(outp,'w') as f:
    for c in cells: f.write(json.dumps(c)+'\n')
print(len(cells),'cells',file=sys.stderr)
