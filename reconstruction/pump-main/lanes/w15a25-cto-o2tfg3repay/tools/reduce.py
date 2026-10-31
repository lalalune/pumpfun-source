#!/usr/bin/env python3
"""reduce.py <raw.ll> <out.ll> [edits.py]: keep validate (made external) and its transitive callees; stub every other define
with `unreachable`. Fast oracle for validate's own CGSCC inline decisions (V). Experiment only."""
import sys,re,runpy
t=open(sys.argv[1]).read()
if len(sys.argv)>3:
    for e in runpy.run_path(sys.argv[3])['EDITS']:
        if callable(e): t=e(t); continue
        x,y=e; assert t.count(x)==1; t=t.replace(x,y)
lines=t.split('\n'); out=[]; i=0; defs={}
# pass 1: collect define blocks
blocks=[]  # (start,end,name)
while i<len(lines):
    l=lines[i]
    if l.startswith('define '):
        m=re.search(r'@("[^"]+"|[\w.$]+)\(',l); name=m.group(1).strip('"')
        j=i
        while lines[j]!='}': j+=1
        blocks.append((i,j,name)); i=j+1
    else: i+=1
names={b[2] for b in blocks}
body={b[2]:'\n'.join(lines[b[0]+1:b[1]]) for b in blocks}
ref=re.compile(r'@("[^"]+"|[\w.$]+)')
V=[n for n in names if 'admin_cto8validate' in n][0]
keep={V}; st=[V]
while st:
    n=st.pop()
    for m in ref.finditer(body[n]):
        x=m.group(1).strip('"')
        if x in names and x not in keep: keep.add(x); st.append(x)
res=[]; pos=0
for s,e,n in blocks:
    res.extend(lines[pos:s]); hdr=lines[s]
    if n==V: hdr=hdr.replace('define internal ','define ',1); res.append(hdr); res.extend(lines[s+1:e+1])
    elif n in keep: res.extend(lines[s:e+1])
    else: res.append(hdr); res.append('start:'); res.append('  unreachable'); res.append('}')
    pos=e+1
res.extend(lines[pos:])
open(sys.argv[2],'w').write('\n'.join(res))
print(V,len(keep),'kept of',len(names), file=sys.stderr)
