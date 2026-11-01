#!/usr/bin/env python3
# slots.py <a> <b>: aligned frame-slot mapping table for spill slots (a slot -> b slot : count, first offs)
import sys,os,difflib,re
from collections import Counter,defaultdict
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w19b13-cto-v1-holder-and1')
sys.path.insert(0,OUT+'/tools')
import dis as D
W=D.W
def L(n):
    if n=='orig':
        import oracle
        return list(D.dis(oracle.orig_window()))
    return list(D.dis(open(f'{OUT}/fx/{n}/fn.bin','rb').read()))
def ab(t):
    t=re.sub(r'\[r10 - 0x[0-9a-f]+\]','[FP]',t)
    t=re.sub(r'\br\d+\b','R',t)
    if t.startswith('j'): t=re.sub(r'[-+]0x[0-9a-f]+$','J',t)
    if t.startswith('call'): t='call'
    if t.startswith('lddw'): t=t.split(',')[0]
    return t
a,b=sys.argv[1],sys.argv[2]; lo=int(sys.argv[3],16) if len(sys.argv)>3 else 0x8d0
A=L(a);B=L(b)
sm=difflib.SequenceMatcher(None,[ab(t) for _,t in A],[ab(t) for _,t in B],autojunk=False)
M=defaultdict(Counter); F=defaultdict(list)
for m in sm.get_matching_blocks():
    for k in range(m.size):
        oa,ta=A[m.a+k]; ob,tb=B[m.b+k]
        fa=re.findall(r'\[r10 - (0x[0-9a-f]+)\]',ta); fb=re.findall(r'\[r10 - (0x[0-9a-f]+)\]',tb)
        for x,y in zip(fa,fb):
            if int(x,16)>=lo:
                M[int(x,16)][y]+=1; F[int(x,16)].append(oa-W)
for s in sorted(M):
    print(f'-{s:#x}: '+' '.join(f'{k}x{v}' for k,v in M[s].most_common(5))+'  @'+','.join(hex(x) for x in F[s][:6]))
