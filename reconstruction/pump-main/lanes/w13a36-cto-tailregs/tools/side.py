#!/usr/bin/env python3
"""side.py orig.dis cand.dis [lo hi] : side-by-side alignment (regs+frame+jumps masked) of orig window range [lo,hi)."""
import sys,re,difflib
def load(p,base=None):
    out=[]
    for l in open(p):
        l=l.rstrip('\n')
        if not l.strip(): continue
        a,t=l.split(None,1); a=int(a,16)
        out.append([a,t.strip()])
    b=out[0][0]
    for x in out: x[0]-=b
    return out
def mask(t,lvl=3):
    s=t
    s=re.sub(r'call -?0x[0-9a-f]+|call \S+','call X',s)
    if lvl>=1: s=re.sub(r'\br\d+\b','R',s)
    if lvl>=2: s=re.sub(r'r10 [-+] 0x[0-9a-f]+','F',s).replace('[R - 0x','[R - 0x')
    if lvl>=3: s=re.sub(r'goto [-+]?0x[0-9a-f]+|goto [+-]?\d+|<\S+>','J',s); s=re.sub(r'(j\w+ R, (?:R|-?0x[0-9a-f]+|-?\d+)), .*',r'\1, J',s)
    return s
O=load(sys.argv[1]); C=load(sys.argv[2])
lo=int(sys.argv[3],16) if len(sys.argv)>3 else 0; hi=int(sys.argv[4],16) if len(sys.argv)>4 else 1<<30
sm=difflib.SequenceMatcher(None,[mask(t) for _,t in O],[mask(t) for _,t in C],autojunk=False)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    for k in range(max(i2-i1,j2-j1)):
        o=O[i1+k] if i1+k<i2 else None; c=C[j1+k] if j1+k<j2 else None
        oa=o[0] if o else (O[i1][0] if i1<len(O) else 0)
        if not(lo<=oa<hi): continue
        mk=' ' if (o and c and o[1]==c[1]) else ('~' if tag=='equal' else '!')
        print(f"{mk} {('%05x %-40s'%(o[0],o[1])) if o else ' '*46} | {('%05x %s'%(c[0],c[1])) if c else ''}")
