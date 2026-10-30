#!/usr/bin/env python3
"""frame2.py <module.ll> <spec> <tag>: apply iredit spec, run debug llc, print named frame map (0x400-0x700 region by default)."""
import sys,re,subprocess,os
from pathlib import Path
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import iredit
D=os.path.expanduser('~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin/llc')
mod=Path(sys.argv[1]).read_text(); spec=sys.argv[2]; tag=sys.argv[3]
lo=int(sys.argv[4],16) if len(sys.argv)>4 else 0x400; hi=int(sys.argv[5],16) if len(sys.argv)>5 else 0x700
m=iredit.apply(mod,spec) if spec else mod
p='/tmp/frame2_%s.ll'%tag; open(p,'w').write(m)
r=subprocess.run([D,'-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',p,'-filetype=obj','-o','/dev/null','-debug-only=prologepilog,stack-coloring'],capture_output=True,text=True)
log=r.stderr; os.remove(p)
s=m.index('admin_cto7execute'); s=m.rfind('\ndefine',0,s); e=m.index('\n}\n',s); fn=m[s:e]
al=re.findall(r'^\s+%([\w.$"]+) = alloca \[(\d+) x i8\]', fn, re.M)
merge={}
for l,r_ in re.findall(r'Merging #(\d+) and slots #(\d+) together',log): merge[int(r_)]=int(l)
offs={int(i):int(o) for i,o in re.findall(r'alloc FI\((\d+)\) at SP\[(-?\d+)\]',log)}
def root(i):
    while i in merge: i=merge[i]
    return i
rows=sorted((-offs.get(root(k),0),k,n,sz,root(k)) for k,(n,sz) in enumerate(al))
for o,k,n,sz,r in rows:
    if lo<=o<hi and r==k: print(hex(o),k,n,sz, ' + '+' '.join('%s(%s)'%(al[j][0],al[j][1]) for j in range(len(al)) if root(j)==k and j!=k)[:200])
