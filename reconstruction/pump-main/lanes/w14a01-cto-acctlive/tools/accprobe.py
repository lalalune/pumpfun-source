#!/usr/bin/env python3
"""accprobe.py <m.ll> <out.ll> <lo> <hi>: post-opt IR probe (experiment only). Stores the accounts pointer %_247 to a
fresh alloca at entry and, for every load in lines [lo,hi] whose address is %_247 or a constant GEP of it, reloads the
accounts pointer from that alloca right before the load (emulates the original's per-use [r10-0x8d8] reloads)."""
import sys,re
src,dst,lo,hi=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4]); blk=len(sys.argv)>5 and sys.argv[5]=="blk"
L=open(src).read().split('\n')
acc='%_247'
geps={}
for l in L:
    m=re.match(r'\s*(%[\w.]+) = getelementptr inbounds i8, ptr '+re.escape(acc)+r', i64 (\d+)$',l)
    if m: geps[m.group(1)]=int(m.group(2))
geps[acc]=0
out=[];k=0;n=0;cur=None
for i,l in enumerate(L,1):
    if re.match(r'^[\w.$"-]+:',l): cur=None
    if lo<=i<=hi:
        m=re.match(r'(\s*%[\w.]+ = load \w+, ptr )(%[\w.]+)(,.*)$',l)
        if m and m.group(2) in geps:
            k+=1; off=geps[m.group(2)]
            if blk and cur: 
                out.append(f'  %acg.{k} = getelementptr inbounds i8, ptr {cur}, i64 {off}')
                out.append(m.group(1)+f'%acg.{k}'+m.group(3)); continue
            cur=f'%acr.{k}'
            out.append(f'  %acr.{k} = load ptr, ptr %accslot, align 8')
            out.append(f'  %acg.{k} = getelementptr inbounds i8, ptr %acr.{k}, i64 {off}')
            out.append(m.group(1)+f'%acg.{k}'+m.group(3)); continue
    out.append(l)
    if l.strip().startswith(acc+' = load ptr, ptr %2'):
        out.append(f'  store ptr {acc}, ptr %accslot, align 8')
    if l=='start:' and not n:
        out.append('  %accslot = alloca ptr, align 8'); n=1
open(dst,'w').write('\n'.join(out)); print('replaced',k)
