#!/usr/bin/env python3
"""jfixone.py name: for each jump aligned (jump-masked) to orig with a wrong offset, ratio gain if that one jump were right."""
import sys,os,difflib,struct,io,contextlib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import oracle
with contextlib.redirect_stdout(io.StringIO()):
    sys.argv=[sys.argv[0]]+sys.argv[1:2]; import jm as J
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a21-cto-helperbound')
n=sys.argv[1]; orw=oracle.orig_window(); ot=oracle.mask(orw); o=J.jm(orw)
raw=open(f'{O}/rx/{n}/fn.bin','rb').read(); ct=oracle.mask(raw); c=J.jm(raw)
def offs(t):
    r=[];x=0
    for q in t: r.append(x); x+=len(q)
    return r
oo=offs(ot); co=offs(ct)
base=difflib.SequenceMatcher(None,ot,ct,autojunk=False).ratio()
sm=difflib.SequenceMatcher(None,o,c,autojunk=False); res=[]
allfix=list(ct)
for a,b,s in sm.get_matching_blocks():
    for k in range(s):
        x=ot[a+k]; y=ct[b+k]
        if x!=y and (x[0]&7) in (5,6) and x[0] not in (0x85,0x95):
            t=list(ct); t[b+k]=x; allfix[b+k]=x
            r=difflib.SequenceMatcher(None,ot,t,autojunk=False).ratio()
            res.append((r-base,oo[a+k],co[b+k]))
res.sort(reverse=True)
print(n,'base',round(base,5),'allfix',round(difflib.SequenceMatcher(None,ot,allfix,autojunk=False).ratio(),5))
import collections
B=collections.Counter(); G=collections.Counter()
for d,x,y in res: B[x//0x800*0x800]+=1; G[x//0x800*0x800]+=d
print(" ".join(f"{k:x}:{B[k]}/{G[k]:.4f}" for k in sorted(B)))
