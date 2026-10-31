#!/usr/bin/env python3
"""vname.py <pre.mir> <ralog> v1 v2 ...: defining instruction(s) (pre-greedy MIR, with block) and the Q line of each vreg."""
import sys,re
mir=open(sys.argv[1]).read(); body=mir[mir.index('\nbody:'):]
q={}
for l in open(sys.argv[2]):
    f=l.split()
    if f and f[0]=='Q': q.setdefault(int(f[1]),' '.join(f[2:]))
defs={}; uses={}; bb=None
for l in body.split('\n'):
    m=re.match(r'\s*(bb\.\d+[^:]*):',l)
    if m: bb=m.group(1); continue
    s=l.strip()
    m=re.match(r'((?:%\d+(?::\w+)?(?:\s*,\s*)?)+)\s*=\s*(.*)',s)
    if m:
        for v in re.findall(r'%(\d+)',m.group(1)): defs.setdefault(int(v),[]).append((bb,s[:160]))
        for v in re.findall(r'%(\d+)',m.group(2)): uses[int(v)]=uses.get(int(v),0)+1
    else:
        for v in re.findall(r'%(\d+)',s): uses[int(v)]=uses.get(int(v),0)+1
for a in sys.argv[3:]:
    v=int(a.lstrip('%'))
    print(f'%{v}: {q.get(v,"(not queued)")} uses={uses.get(v,0)}')
    for b,s in defs.get(v,[])[:4]: print(f'    [{b}] {s}')
