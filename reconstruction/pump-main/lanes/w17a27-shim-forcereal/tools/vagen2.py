#!/usr/bin/env python3
"""vagen2.py <m.ll> <out.jsonl> <defblock>:<useblock>[,<useblock>..] ...: volatile ctx.accounts reload defined at the
head (or --tail: before the terminator) of defblock; uses of %_318 / its GEPs in the use blocks are rerouted to it."""
import sys,json,re
a=sys.argv[1:]; m,outp=a[0],a[1]; specs=a[2:]
L=open(m).read().split('\n')
geps={}
for i,l in enumerate(L):
    mm=re.match(r'^\s+(%[\w.$]+) = getelementptr inbounds i8, ptr %_318, i64 (\d+)$',l)
    if mm: geps[mm.group(1)]=int(mm.group(2))
def blk(b):
    s=[i for i,l in enumerate(L) if l.startswith(b+':')][0]; e=s+1
    while L[e].strip()!='' and not re.match(r'^[\w.$"-]+:',L[e]): e+=1
    p=s+1
    while ' = phi ' in L[p]: p+=1
    return s,p,e
cells=[]
for k,sp0 in enumerate(specs):
    tail=sp0.endswith('@tail'); sp=sp0.replace('@tail','')
    d,us=sp.split(':'); us=us.split(',')
    s,p,e=blk(d); ins=(e-1) if tail else p
    v=f'%accw{k}'; ops=[['ins',ins,f'  {v} = load volatile ptr, ptr %3, align 8, !nonnull !2, !noundef !2']]; used=[]
    for u in us:
        s2,p2,e2=blk(u)
        for i in range(p2,e2):
            l=L[i]; nl=re.sub(r'%_318(?![\w.$])',v,l)
            for g in geps:
                if re.search(re.escape(g)+r'(?![\w.$])',nl) and not nl.strip().startswith(g+' ='):
                    nn='%g'+g[1:].replace('.','_')+f'w{k}'; nl=re.sub(re.escape(g)+r'(?![\w.$])',nn,nl)
                    if g not in used: used.append(g)
            if nl!=l: ops.append(['rep',i,nl])
    for g in used: ops.append(['ins',ins,f"  %g{g[1:].replace('.','_')}w{k} = getelementptr inbounds i8, ptr {v}, i64 {geps[g]}"])
    cells.append({'id':'va2:'+sp0,'ops':ops,'save':'va2_%d'%k})
open(outp,'w').write('\n'.join(json.dumps(c) for c in cells)+'\n')
