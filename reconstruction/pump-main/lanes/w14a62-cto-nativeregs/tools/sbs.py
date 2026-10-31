#!/usr/bin/env python3
"""sbs.py <so|o> <orig_lo> <orig_hi>: aligned side-by-side (sk alignment) of orig range vs candidate; '*' marks raw diff"""
import sys,os,difflib,re
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import absratio as A, amap
p=sys.argv[1]; lo=int(sys.argv[2],16); hi=int(sys.argv[3],16)
C=amap.lines(p); OL=amap.OL
a=[A.norm(x[1],True) for x in OL]; b=[A.norm(x[1],True) for x in C]
sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
def cl(s): return re.sub(r'\s+<[^>]*>','',s.strip())
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    n=max(i2-i1,j2-j1)
    for k in range(n):
        i=i1+k if i1+k<i2 else None; j=j1+k if j1+k<j2 else None
        oo=int(OL[i][0],16) if i is not None else None
        if oo is None:
            # print only if neighbours in range
            if i1<len(OL) and lo<=int(OL[min(i1,len(OL)-1)][0],16)<=hi: pass
            else: continue
        elif not(lo<=oo<=hi): continue
        ol=f"{OL[i][0]} {cl(OL[i][1])}" if i is not None else ''
        cc=f"{C[j][0]} {cl(C[j][1])}" if j is not None else ''
        mk=' ' if (i is not None and j is not None and A.norm(OL[i][1],False)==A.norm(C[j][1],False) and cl(OL[i][1])==cl(C[j][1])) else ('f' if (i is not None and j is not None and A.norm(OL[i][1],False)==A.norm(C[j][1],False)) else '*')
        print(f"{mk} {ol[:48]:48s} | {cc[:48]}")
