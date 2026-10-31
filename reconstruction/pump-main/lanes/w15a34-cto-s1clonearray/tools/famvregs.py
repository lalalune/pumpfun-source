#!/usr/bin/env python3
"""famvregs.py <pre.mir>: vregs defined in the sharing-CPI arm (contiguous clone/inc_strong blocks before the
admin_cto_sharing_config JAL, plus the 2 blocks before them and the call block). Prints space-separated vreg numbers."""
import sys,re
t=open(sys.argv[1]).read().split('\n')
body=max(i for i,l in enumerate(t) if l.startswith('body:'))
call=[i for i,l in enumerate(t) if i>body and 'JAL @' in l and 'admin_cto_sharing_config' in l][0]
blocks=[i for i,l in enumerate(t) if i>body and re.match(r'^  bb\.\d+',l)]
cb=max(b for b in blocks if b<call)
idx=blocks.index(cb); k=idx
def clonish(l): return any(s in l for s in ('clone17h','inc_strong','bb4.i'))
while k>0 and clonish(t[blocks[k-1]]): k-=1
k=max(0,k-2)
start=blocks[k]; end=blocks[idx+1] if idx+1<len(blocks) else len(t)
V=set()
for l in t[start:end]:
    m=re.match(r'\s+(%\d+)(?::\w+)?\s*=',l)
    if m: V.add(int(m.group(1)[1:]))
    for m in re.finditer(r'(%\d+)(?::\w+)?(?:,\s*(%\d+)(?::\w+)?)*\s*=',l): pass
print(' '.join(map(str,sorted(V))))
print(len(V),'vregs, lines',start,end,file=sys.stderr)
