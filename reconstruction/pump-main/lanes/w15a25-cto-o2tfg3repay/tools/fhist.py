#!/usr/bin/env python3
"""fhist.py <cand>...: over true-LCS rfj-matched pairs, histogram of r10 offset deltas (orig-cand) and reg-equal count, per region."""
import sys,os,struct,collections
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled
from fact import mk
from lcschunk_m import matched_ops
O=oracle.orig_window(); ot,oo=xled.toks(O)
def r10off(t):
    op=t[0]; cl=op&7
    if (cl==1 and (t[1]>>4)==10) or (cl in (2,3) and (t[1]&15)==10): return struct.unpack_from('<h',t,2)[0]
    if op==0x07 : return ('lea',struct.unpack_from('<i',t,4)[0])
    return None
if __name__=="__main__":
 for p in sys.argv[1:]:
     C=xled.load(p if (p=='main' or '.' in p) else f'{os.path.dirname(T)}/rx/{p}/fn.bin'); ct,co=xled.toks(C)
     f=mk(1,1,1); ops=matched_ops(f(ot),f(ct)); H=collections.Counter(); eq=0; n=0; regeq=0
     for op,i,j in ops:
         if op!='=': continue
         a,b=r10off(ot[i]),r10off(ct[j])
         if ot[i][1]==ct[j][1]: regeq+=1
         if a is None or b is None or isinstance(a,tuple) or isinstance(b,tuple): continue
         n+=1; H[a-b]+=1
     print(p,'r10 matched',n,'equal',H[0],'regs-equal',regeq,'top deltas',H.most_common(8))
