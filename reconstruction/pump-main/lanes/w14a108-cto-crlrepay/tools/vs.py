#!/usr/bin/env python3
"""vs.py <a> <b> [--full]: where b differs from a (fmask skeleton), per opcode with sizes; a/b = rxname|main|.bin"""
import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled
import dis as D
def ld(p): return xled.load(p if (p=='main' or '.' in p) else f'{os.path.dirname(T)}/rx/{p}/fn.bin')
A=ld(sys.argv[1]); B=ld(sys.argv[2]); full='--full' in sys.argv
at,ao=xled.toks(A); bt,bo=xled.toks(B); af=xled.fmask(at); bf=xled.fmask(bt)
da=dict(D.d(A)); db=dict(D.d(B))
sm=difflib.SequenceMatcher(None,af,bf,autojunk=False)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal': continue
    print(f'{tag:7s} a {ao[i1] if i1<len(ao) else len(A):05x} -{i2-i1}  b {bo[j1] if j1<len(bo) else len(B):05x} +{j2-j1}')
    if full or (i2-i1)+(j2-j1)<=24:
        for i in range(i1,i2): print('   -',da[ao[i]])
        for j in range(j1,j2): print('   +',db[bo[j]])
