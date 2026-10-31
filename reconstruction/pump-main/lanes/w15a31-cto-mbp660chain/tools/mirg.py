#!/usr/bin/env python3
"""mirg.py <pre.mir> <blockname-regex>...: print block number, name, successors(prob) and preds for matching blocks."""
import sys,re
t=open(sys.argv[1]).read()
blks=re.findall(r'^  bb\.(\d+)\.?([^ :\n]*)[^\n]*:\n((?:    [^\n]*\n|  \n|\n)*?)(?=^  bb\.|\Z)',t,re.M)
B={};P={}
for n,nm,body in blks:
    m=re.search(r'successors: ([^\n]*)',body); s=re.findall(r'%bb\.(\d+)\((0x[0-9a-f]+)\)',m[1]) if m else []
    B[n]=(nm,s,body)
    for x,p in s: P.setdefault(x,[]).append((n,p))
def nm(n): x=B[n][0]; return re.sub(r'_ZN.*?(to_string|clone|inc_strong)\w*?E(\.[\w.]*)?$',r'\1\2',x)
for rx in sys.argv[2:]:
    for n,(name,s,body) in B.items():
        if re.fullmatch(rx,name) or rx==n:
            print(f'bb.{n} {nm(n)}  succ: '+', '.join(f'{x}:{nm(x)}({int(p,16)/2**31:.3f})' for x,p in s)+'  preds: '+', '.join(f'{x}:{nm(x)}' for x,p in P.get(n,[])))
