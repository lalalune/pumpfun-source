#!/usr/bin/env python3
"""pairdiff.py <a.bin> <b.bin> [minrun]: skeleton-masked (regs/frame/jumps) difflib between two candidate fn.bins; prints runs only in a / only in b."""
import sys,os,difflib
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a21-cto-s3cashflag/t2'); import oracle,xled,disw as D
a=open(sys.argv[1],'rb').read(); b=open(sys.argv[2],'rb').read(); mn=int(sys.argv[3]) if len(sys.argv)>3 else 2
ta,oa=xled.toks(a); tb,ob=xled.toks(b); fa=xled.fmask(ta); fb=xled.fmask(tb)
da=dict(D.d(a)); db=dict(D.d(b))
sm=difflib.SequenceMatcher(None,fa,fb,autojunk=False)
print('len',len(a),len(b),'match',sum(x.size for x in sm.get_matching_blocks()))
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal': continue
    if (i2-i1)<mn and (j2-j1)<mn: continue
    print(f'{tag} A {oa[i1] if i1<len(oa) else len(a):05x}+{i2-i1}  B {ob[j1] if j1<len(ob) else len(b):05x}+{j2-j1}')
    for k in range(i1,min(i2,i1+12)): print('   -',f'{oa[k]:05x}',da.get(oa[k]))
    for k in range(j1,min(j2,j1+12)): print('   +',f'{ob[k]:05x}',db.get(ob[k]))
