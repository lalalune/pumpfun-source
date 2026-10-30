#!/usr/bin/env python3
"""sbs.py orig_j.txt cand_j.txt olo ohi : side-by-side abstract alignment of an orig range, printing actual insns of non-equal ops."""
import sys,re,difflib
def load(p):
    out=[]
    for l in open(p):
        m=re.match(r'([0-9a-f]{5})\s+(.*?)\s*(<==.*)?$',l.rstrip())
        if m: out.append((int(m.group(1),16),m.group(2)))
    return out
def ab(t):
    t=re.sub(r'\s+-> [0-9a-f]+$','',t)
    t=re.sub(r'\[r10 - 0x[0-9a-f]+\]','[r10-S]',t)
    t=re.sub(r'add64 (r\d+), -0x[0-9a-f]+$',r'add64 \1, -S',t)
    t=re.sub(r'call -?0x[0-9a-f]+','call X',t)
    t=re.sub(r'lddw (r\d+), 0x[0-9a-f]+',r'lddw \1, X',t)
    if t.startswith('j'): t=re.sub(r'[+-]?0x[0-9a-f]+$','L',t)
    return t
o=load(sys.argv[1]); c=load(sys.argv[2]); lo,hi=int(sys.argv[3],16),int(sys.argv[4],16)
sm=difflib.SequenceMatcher(None,[ab(x[1]) for x in o],[ab(x[1]) for x in c],autojunk=False)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if i2>i1 and (o[i2-1][0]<lo or o[i1][0]>hi): continue
    if i2==i1 and (i1>=len(o) or o[i1][0]<lo or o[i1][0]>hi): continue
    if tag=='equal':
        for k in range(i2-i1):
            print('  %05x %-44s | %05x %s'%(o[i1+k][0],o[i1+k][1][:44],c[j1+k][0],c[j1+k][1][:44]))
        continue
    for k in range(max(i2-i1,j2-j1)):
        x=o[i1+k] if i1+k<i2 else None; y=c[j1+k] if j1+k<j2 else None
        print('%s %s | %s'%(tag[0], ('%05x %-44s'%(x[0],x[1][:44])) if x else ' '*50, ('%05x %s'%(y[0],y[1][:44])) if y else ''))
