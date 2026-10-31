#!/usr/bin/env python3
"""ftagn.py in.ll out.ll MODE: fee-tag phis of constants in bb76 (Some exit bb58.i=1, None exits 0).
MODE a: one i64 phi -> 757 only (=ftag); b: i64 phi -> 757, i1 phi -> CPI tag (zext); c: i64 phi -> both;
d: i64 -> 757 + i8 phi (2 on Some) dummy-used via CPI tag (tag = zext(i8)!=0)"""
import sys,re
src,dst,mode=sys.argv[1:4]
t=open(src).read()
i=t.index('\nbb76:'); e=t.index('\n',i+1)
preds=re.search(r'; preds = (.*)',t[i:e]).group(1).replace('%','').split(', ')
def phi(nm,ty,one): return f'  %{nm} = phi {ty} '+', '.join(f'[ {one if p.startswith("bb58.i") else 0}, %{p} ]' for p in preds)+'\n'
add=phi('ftag','i64',1)
if mode in('b',): add+=phi('ftagb','i1','true').replace('[ 0,','[ false,')
t=t[:e+1]+add+t[e+1:]
t=t.replace('%switch48 = icmp eq i64 %0, 1','%switch48 = icmp eq i64 %ftag, 1')
L=t.split('\n'); k=[j for j,l in enumerate(L) if 'admin_cto_pool17h' in l and 'call' in l and 'i64 noundef %0' in l]; assert len(k)==1
if mode=='b':
    L[k[0]]=L[k[0]].replace('i64 noundef %0','i64 noundef %ftbz'); L.insert(k[0],'  %ftbz = zext i1 %ftagb to i64')
if mode=='c': L[k[0]]=L[k[0]].replace('i64 noundef %0','i64 noundef %ftag')
open(dst,'w').write('\n'.join(L))
