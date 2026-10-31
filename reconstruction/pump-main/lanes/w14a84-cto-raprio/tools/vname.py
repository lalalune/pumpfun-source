#!/usr/bin/env python3
"""vname.py <ra.log> <pregreedy.mir> <postgreedy.mir> <vreg>...: name a greedy vreg (split products included): split ancestry
from the RAPRIO_LOG, root value's defining MIR instruction (pre-greedy), the vreg's own blocks (post-greedy), its queue
priority/size/hint bit and final register. Experiment only."""
import sys,re
log,pre,post=sys.argv[1:4]
par={}; seen=set(); prio={}; fin={}; evs={}
for l in open(log):
    f=l.split()
    if f[0]=='Q':
        v=int(f[1]); seen.add(v); prio.setdefault(v,(int(f[2][2:]),f[3],f[4]))
    elif f[0]=='R' and 'new:' in f:
        p=int(f[1]); 
        for x in f[f.index('new:')+1:]:
            x=int(x)
            if x!=p and x not in seen and x not in par: par[x]=p
    elif f[0]=='A': fin[int(f[1])]=f[2]
    elif f[0]=='E': evs.setdefault(int(f[1]),[]).append(f[3]+'<-'+f[5])
def rows(path):
    t=open(path).read(); t=t[t.index('\nbody:'):]; blk=None; out=[]
    for l in t.split('\n'):
        m=re.match(r'\s{2}(bb\.\d+[^:]*):',l)
        if m: blk=m.group(1); continue
        s=l.strip()
        if s and blk and not s.startswith(('successors','liveins',';')): out.append((blk,s))
    return out
PRE=rows(pre); POST=rows(post)
def defs(R,v):
    pat=re.compile(r'%'+str(v)+r'(?!\d)')
    return [(b,s) for b,s in R if '=' in s and pat.search(s.split('=')[0])]
def blocks(R,v):
    pat=re.compile(r'%'+str(v)+r'(?!\d)'); bl=[]
    for b,s in R:
        if pat.search(s) and b not in bl: bl.append(b)
    return bl
def short(b): 
    p=b.split('.',2); n=p[2] if len(p)>2 else ''
    n=re.sub(r'_ZN\d+.*?(\w+)17h[0-9a-f]+E',lambda m:m.group(1),n)
    return p[1]+'.'+n[:40]
for v in map(int,sys.argv[4:]):
    chain=[v]
    while chain[-1] in par: chain.append(par[chain[-1]])
    root=chain[-1]; d=defs(PRE,root)
    p=prio.get(v); bl=blocks(POST,v)
    print(f'%{v}: chain {"<".join(map(str,chain))} final={fin.get(v,"(split/spilled)")} prio={hex(p[0]) if p else "?"} {p[2] if p else ""} hint={(p[0]>>30)&1 if p else "?"} global={(p[0]>>29)&1 if p else "?"} evicted={evs.get(v,[])[:3]}')
    for b,s in d[:2]: print(f'   root def {short(b)} | {s[:140]}')
    print(f'   blocks({len(bl)}): {" ".join(short(b) for b in bl[:8])}{" ..." if len(bl)>8 else ""}')
