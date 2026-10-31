#!/usr/bin/env python3
"""reload.py <in.ll> <out.ll> <block> [<block>...]: in each named block, re-load ctx.accounts (load ptr %3) after the phis and use
it for every %_271 use in that block (post-opt IR experiment; volatile=1 env makes the load volatile)."""
import sys,re,os
src,dst=sys.argv[1:3]; blocks=set(sys.argv[3:]); L=open(src).read().split('\n'); out=[]; cur=None; ins=False; k=0
vol='volatile ' if os.environ.get('VOL') else ''
for l in L:
    m=re.match(r'^([\w.$"]+):',l)
    if m: cur=m.group(1); ins=cur in blocks; done=False; k+=1; out.append(l); continue
    if ins and not done and l.strip() and not l.strip().startswith('%') or (ins and not done and l.strip().startswith('%') and ' = phi ' not in l):
        out.append(f'  %_271.r{k} = load {vol}ptr, ptr %3, align 8, !nonnull !2, !align !3, !noundef !2'); done=True
    if ins and done: l=re.sub(r'%_271(?![\w.])',f'%_271.r{k}',l)
    out.append(l)
open(dst,'w').write('\n'.join(out))
