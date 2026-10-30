#!/usr/bin/env python3
"""genld.py <unstripped.so> <ref.json> <link.map> <default.ld> <out.ld> [--mode ud|all]
Inputs come from a default-order build (fastbuild with link/ordered.ld = sbf_default.ld).
Emit a .text ordering script: U (upstream generic instances in the root CGU) and D (dependency
objects) in the original's order, L (root local items) kept in rustc order via one glob."""
import sys,re,json
sys.path.insert(0,__file__.rsplit('/',1)[0])
from m13 import *
so,ref,mp,dflt,outp=sys.argv[1:6]
mode=sys.argv[sys.argv.index('--mode')+1] if '--mode' in sys.argv else 'ud'
assert mode in ('ud','all'), mode
M=model(so,ref)
R={a:M.region(a) for a in M.cst}
rx=re.compile(r'^\s+([0-9a-f]+)\s+[0-9a-f]+\s+([0-9a-f]+)\s+\d+\s+(\S.*?):\((\.text[^)]*)\)$')
sec={}
for line in open(mp):
    m=rx.match(line)
    if m: sec[int(m.group(1),16)]=(m.group(3),m.group(4),int(m.group(2),16))
assert set(sec)==set(M.cst),(len(sec),len(M.cst))
def fsel(obj):
    name=obj.rsplit('/',1)[-1]
    m=re.match(r'^lib([A-Za-z0-9_]+)-[0-9a-f]{16}\.rlib\((.*)\)$',name)
    if m: return '*lib%s-*.rlib:*'%m.group(1)
    m=re.match(r'^([A-Za-z0-9_]+)\.\1\.[0-9a-f]+-cgu\.0\.rcgu\.o$',name)
    if m: return '*%s.%s.*-cgu.0.rcgu.o'%(m.group(1),m.group(1))
    if re.match(r'^[A-Za-z0-9_]+\.[a-z0-9]+\.rcgu\.o$',name): return '*'  # allocator shim (random name)
    raise SystemExit('unknown object '+name)
def srt(reg):
    xs=[a for a in M.cst if R[a]==reg]
    paired=sorted([a for a in xs if a in M.inv],key=lambda a:M.inv[a]); out=list(paired)
    for i,a in enumerate(xs):
        if a in M.inv: continue
        prev=next((xs[j] for j in range(i-1,-1,-1) if xs[j] in M.inv),None)
        out.insert(out.index(prev)+1 if prev else 0,a)
    return out
def sel(a):
    o,s,_=sec[a]; return '    %s("%s")'%(fsel(o),s)
lines=[sel(a) for a in srt('U')]
mainobj=fsel(sec[M.cst[0]][0])
if mode=='all': lines+=[sel(a) for a in srt('L')]
lines.append('    %s(.text*)'%mainobj)
lines+=[sel(a) for a in srt('D')]
d=open(dflt).read(); rule='  .text : { *(.text*) } :text'
assert d.count(rule)==1
body='  .text : {\n'+'\n'.join(lines)+'\n    *(.text*)\n  } :text'
open(outp,'w').write(d.replace(rule,body))
print(len(lines),'selectors')
