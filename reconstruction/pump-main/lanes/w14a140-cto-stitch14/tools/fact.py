#!/usr/bin/env python3
"""fact.py <cand>... [--lo 0x3c00 --hi 0x4800]: factorial mask table (r=regs, f=frame offs, j=jump offs, + lea imm when f).
Prints matched orig tokens (whole fn and in orig range) under all 8 mask combinations; cand=rxname|.bin|main."""
import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled
def mk(r,f,j):
    def g(t):
        out=[]
        for x in t:
            x=bytearray(x); op=x[0]; cl=op&7
            if f:
                if (cl==1 and (x[1]>>4)==10) or (cl in (2,3) and (x[1]&15)==10): x[2:4]=b'\0\0'
                if op in (0x07,0x87): x[4:8]=b'\0'*4
            if r: x[1]=0
            if j and cl in (5,6) and op not in (0x85,0x95): x[2:4]=b'\0\0'
            out.append(bytes(x))
        return out
    return g
if __name__=='__main__':
    a=sys.argv[1:]; lo,hi=0x3c00,0x4800
    if '--lo' in a: i=a.index('--lo'); lo=int(a[i+1],16); del a[i:i+2]
    if '--hi' in a: i=a.index('--hi'); hi=int(a[i+1],16); del a[i:i+2]
    O=oracle.orig_window(); ot,oo=xled.toks(O)
    combos=[(r,f,j) for r in (0,1) for f in (0,1) for j in (0,1)]
    print('cand'.ljust(22),' '.join(('r' if r else '-')+('f' if f else '-')+('j' if j else '-') for r,f,j in combos).replace(' ','      '))
    for p in a:
        C=xled.load(p if (p=='main' or '.' in p) else f'{os.path.dirname(T)}/rx/{p}/fn.bin'); ct,_=xled.toks(C)
        s=[];s2=[]
        for r,f,j in combos:
            g=mk(r,f,j); A=g(ot); B=g(ct); h=[0]*len(A)
            for bl in difflib.SequenceMatcher(None,A,B,autojunk=False).get_matching_blocks():
                for k in range(bl.size): h[bl.a+k]=1
            s.append(sum(h)); s2.append(sum(h[i] for i in range(len(h)) if lo<=oo[i]<hi))
        print(p[:22].ljust(22),' '.join(f'{x:4d}/{y:3d}' for x,y in zip(s,s2)), len(C))
