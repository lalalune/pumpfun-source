#!/usr/bin/env python3
"""scan.py <out.tsv> <fn.bin>...: true-LCS (---, --j, -fj, r--, rf-, rfj) for many captures (dedup by content hash)."""
import sys,os,hashlib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled
from fact import mk
from lcs import lcs
O=oracle.orig_window(); ot,oo=xled.toks(O)
ms=['---','--j','-fj','r--','rf-','rfj']; F={m:mk(m[0]=='r',m[1]=='f',m[2]=='j') for m in ms}; OA={m:F[m](ot) for m in ms}
seen=set(); out=open(sys.argv[1],'w')
for p in sys.argv[2:]:
    try: C=open(p,'rb').read()
    except Exception: continue
    h=hashlib.sha1(C).hexdigest()[:12]
    if h in seen: continue
    seen.add(h)
    try: ct,_=xled.toks(C)
    except Exception: continue
    r=[lcs(OA[m],F[m](ct)) for m in ms]
    out.write('\t'.join([p,h,str(len(C))]+[str(x) for x in r])+'\n'); out.flush()
