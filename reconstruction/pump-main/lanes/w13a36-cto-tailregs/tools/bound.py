#!/usr/bin/env python3
"""bound.py <fn.bin|so> [lo hi]: ratio if register (R) / frame+register (FR) differences inside orig [lo,hi) were fixed.
Candidate tokens aligned (reg- or frame+reg-masked difflib) to orig tokens in range are replaced by the orig token when
their masked forms agree; the plain ratio is then recomputed."""
import sys,os,difflib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),"../../w12a02-cto-iroracle/scripts"))
import tail, ctoracle as co
p=sys.argv[1]; lo=int(sys.argv[2],16) if len(sys.argv)>2 else tail.LO; hi=int(sys.argv[3],16) if len(sys.argv)>3 else tail.HI
OT=tail.OT; OFF=tail.OFF; ct=tail.toks(p)
def fixed(f):
    c=list(ct); sm=difflib.SequenceMatcher(None,[f(t) for t in OT],[f(t) for t in c],autojunk=False)
    for a,b,s in sm.get_matching_blocks():
        for k in range(s):
            if lo<=OFF[a+k]<hi: c[b+k]=OT[a+k]
    return co.metrics(OT,c,sum(len(t) for t in c),27400)['ratio']
print(p, 'base', co.metrics(OT,ct,sum(len(t) for t in ct),27400)['ratio'], 'R-bound', fixed(tail.regmask), 'FR-bound', fixed(lambda t: co.abstract(tail.regmask(t))))
