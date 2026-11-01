#!/usr/bin/env python3
"""vagen.py <m.ll> <out.jsonl> <block> [<block>...]: emulate a read_volatile re-derivation of ctx.accounts at the head
of the given post-opt blocks: %accvN = load volatile ptr, ptr %3; uses of %_318 (and its GEPs) inside the block move to it."""
import sys,json,re
m,outp=sys.argv[1],sys.argv[2]; blocks=sys.argv[3:]
L=open(m).read().split('\n')
geps={}
for i,l in enumerate(L):
    mm=re.match(r'^\s+(%[\w.$]+) = getelementptr inbounds i8, ptr %_318, i64 (\d+)$',l)
    if mm: geps[mm.group(1)]=int(mm.group(2))
cells=[]
for bi,b in enumerate(blocks):
    s=[i for i,l in enumerate(L) if l.startswith(b+':')][0]; e=s+1
    while L[e].strip()!='' and not re.match(r'^[\w.$"-]+:',L[e]): e+=1
    p=s+1
    while ' = phi ' in L[p]: p+=1
    v=f'%accv{bi}'; ops=[['ins',p,f'  {v} = load volatile ptr, ptr %3, align 8, !nonnull !2, !noundef !2']]; used=[]
    for i in range(p,e):
        l=L[i]; nl=re.sub(r'%_318(?![\w.$])',v,l)
        for g in geps:
            if re.search(re.escape(g)+r'(?![\w.$])',nl) and not nl.strip().startswith(g+' ='):
                nn='%g'+g[1:].replace('.','_')+f'v{bi}'; nl=re.sub(re.escape(g)+r'(?![\w.$])',nn,nl)
                if g not in used: used.append(g)
        if nl!=l: ops.append(['rep',i,nl])
    for g in used: ops.append(['ins',p,f"  %g{g[1:].replace('.','_')}v{bi} = getelementptr inbounds i8, ptr {v}, i64 {geps[g]}"])
    cells.append({'id':'va:'+b,'ops':ops,'save':'va_'+b.replace('.','_')})
open(outp,'w').write('\n'.join(json.dumps(c) for c in cells)+'\n')
print(len(cells),file=sys.stderr)
