#!/usr/bin/env python3
"""autoswap.py <src.rs> <prefix> : for every `A==B` / `A!=B` comparison in lines 283..771 whose operands are simple
(no side-effecting calls other than key()/data_is_empty()/len()), write e/<prefix>NNN.py swapping the operands.
Experiment generator only; every gene keeps the newline count."""
import sys,re,os,json
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a42-cto-entrycopy3/'
src=open(sys.argv[1]).read(); pre=sys.argv[2]
lines=src.split('\n'); lo=sum(len(l)+1 for l in lines[:282]); hi=sum(len(l)+1 for l in lines[:771])
STOP_L=set('({;,=|&<>?') ; STOP_R=set(')};,|&?')
def left(i):
    j=i; depth=0
    while j>0:
        c=src[j-1]
        if c in ')]': depth+=1
        elif c in '([':
            if depth==0: break
            depth-=1
        elif depth==0 and (c in '{};,=|&<>?!' or c==' ' ): break
        j-=1
    return j
def right(i):
    j=i; depth=0
    while j<len(src) and src[j] in '&*': j+=1
    while j<len(src):
        c=src[j]
        if c in '([': depth+=1
        elif c in ')]':
            if depth==0: break
            depth-=1
        elif depth==0 and (c in '{};,|&?<>=' or c==' '): break
        j+=1
    return j
out=[]
for m in re.finditer(r'(?<![=!<>])(==|!=)(?!=)',src):
    p=m.start()
    if p<lo or p>hi: continue
    a0=left(p); b1=right(p+2)
    A=src[a0:p]; B=src[p+2:b1]
    if not A or not B or '\n' in A+B: continue
    calls=re.findall(r'\.(\w+)\(',A+B)
    if any(c not in ('key','data_is_empty','len','as_ref','unwrap_or','is_some','is_none') for c in calls): continue
    if A==B: continue
    old=A+m.group(1)+B; new='!('+A+('!=' if m.group(1)=='==' else '==')+B+')'
    # widen context until unique
    k=0
    while src.count(src[a0-k:b1+k])>1 and k<80: k+=1
    o=src[a0-k:b1+k]; n=src[a0-k:a0]+new+src[b1:b1+k]
    if src[a0-1:a0]=='!' : continue
    if src.count(o)!=1: continue
    out.append((old,new,o,n))
for i,(old,new,o,n) in enumerate(out):
    nm='%s%03d'%(pre,i)
    open(O+'e/'+nm+'.py','w').write('# %s -> %s\nEDITS=[(%r,%r)]\n'%(old,new,o,n))
    print(nm,old,'->',new)
