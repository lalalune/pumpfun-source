#!/usr/bin/env python3
"""layout.py <pe.log> [module.ll]: frame layout from debug llc -debug-only=prologepilog,stack-coloring: FI, name, size, SP offset."""
import re,sys
t=open(sys.argv[1]).read()
name={}
for m in re.finditer(r'slot #(\d+) with allocation: (\S+)',t): name[int(m.group(1))]=m.group(2)
for m in re.finditer(r'lifetime (?:start|end) marker for slot #(\d+) with allocation: (\S+)',t): name[int(m.group(1))]=m.group(2)
sz={}
if len(sys.argv)>2:
    sys.path.insert(0,__import__('os').path.dirname(__file__)); import iredit
    _,fn,_=iredit.split_fn(open(sys.argv[2]).read())
    al=re.findall(r'^\s*%(\S+) = alloca \[(\d+) x i8\]',fn,re.M)
    for i,(a,n) in enumerate(al): sz[i]=int(n); name.setdefault(i,a)
merged={}
for m in re.finditer(r'Merging #(\d+) and slots #(\d+) together',t): merged[int(m.group(2))]=int(m.group(1))
offs=[(int(m.group(2)),int(m.group(1))) for m in re.finditer(r'alloc FI\((\d+)\) at SP\[(-?\d+)\]',t)]
for off,fi in sorted(offs,reverse=True):
    ms=[name.get(k,'#%d'%k) for k,v in merged.items() if v==fi]
    print(f'{-off:#6x} FI{fi:<4} {name.get(fi,"spill/fixed"):28s} {sz.get(fi,"")!s:>4}  {" ".join(ms)[:90]}')
