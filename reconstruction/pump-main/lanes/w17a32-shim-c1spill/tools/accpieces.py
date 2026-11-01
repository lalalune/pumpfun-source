#!/usr/bin/env python3
"""accpieces.py <tag>: from ra/<tag>.s and ra/<tag>.log (RAPRIO), list the split pieces of %0 (accounts) with their
register, use count and candidate offset range. Experiment only."""
import sys,os,re
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import al, d as D
OUT=os.path.dirname(T); tag=sys.argv[1]
log=open(f'{OUT}/ra/{tag}.log').read().split('\nFN ')[0]
m=re.findall(r'^R 0 -> 0 st=2 new: ([\d ]+)$',log,re.M)
pieces=[int(x) for x in m[-1].split()] if m else []
# include descendants: R <p> -> 0 st=4 new: ...
kids={}
for p,new in re.findall(r'^R (\d+) -> \S+ st=\d+ new: ([\d ]+)$',log,re.M): kids.setdefault(int(p),[]).extend(int(x) for x in new.split())
tags=al.asm_tags(f'{OUT}/ra/{tag}.s'); cd=D.dis(D.load(f'{OUT}/ra/{tag}.bin'))
occ={}
for i,(off,s) in enumerate(cd):
    for mm in re.finditer(r'([du])(\d+)=(\w+)',tags[i] if i<len(tags) else ''):
        occ.setdefault(int(mm.group(2)),[]).append((off,mm.group(1),mm.group(3)))
A=dict(re.findall(r'^A (\d+) (\S+)$',log,re.M))
for p in pieces:
    L=occ.get(p,[])
    rng=f'{L[0][0]:#x}..{L[-1][0]:#x}' if L else '-'
    print(p,A.get(str(p),'?'),len(L),rng,'kids:'+','.join(map(str,kids.get(p,[])[:12])) if p in kids else '')
