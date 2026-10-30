#!/usr/bin/env python3
"""hbremat.py <m.ll> <out.ll> [which]: post-opt IR oracle for the lv3 register shift (experiment only).
Finds execute's holder i1 (`icmp ne (and i8 %holder,-3),0`) and gives its validate-region uses
(which: 'and' = the line-296 `or.cond.i` use, 'br' = the two arm-split branches, 'all' = both; default 'and')
their own `trunc i8 %holder to i1`, so RA sees a separate short vreg (as main's validate, whose holder is a
separate `icmp eq` value). Late uses (tree branch, curve store) are untouched."""
import sys,re
src,dst=sys.argv[1],sys.argv[2]; which=sys.argv[3] if len(sys.argv)>3 else 'and'
t=open(src).read(); L=t.split('\n')
k=next(i for i,l in enumerate(L) if re.match(r'\s*%\S+ = and i8 %holder, -3$',l)); a=L[k].split()[0]
v=L[k+1].split()[0]; assert re.match(r'\s*%\S+ = icmp ne i8 '+re.escape(a)+', 0',L[k+1]),L[k+1]
first_tree=next(i for i,l in enumerate(L) if i>k and re.match(r'\s*br i1 '+re.escape(v)+r', label %bb\d+, label %bb\d+$',l))
n=0
for i in range(k+2,first_tree):
    l=L[i]; isand=re.match(r'\s*%or\.cond[\w.]* = and i1 '+re.escape(v)+',',l); isbr=l.strip().startswith('br i1 '+v+',')
    if (which in('and','all') and isand) or (which in('br','all') and isbr):
        L[i]=f'  %hbr{n} = trunc i8 %holder to i1\n'+l.replace(v,f'%hbr{n}'); n+=1
open(dst,'w').write('\n'.join(L)); print(f'{v}: {n} uses rematerialized ({which})')
