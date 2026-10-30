#!/usr/bin/env python3
"""absdiff.py orig_r.txt cand_r.txt [--min N] [--show]: align abstracted insns (stack offsets, jump targets,
call targets, lddw imms masked) and print non-equal regions with orig/cand offset ranges."""
import sys,re,difflib,argparse
ap=argparse.ArgumentParser(); ap.add_argument('o'); ap.add_argument('c'); ap.add_argument('--min',type=int,default=1)
ap.add_argument('--show',action='store_true'); ap.add_argument('--exact',action='store_true')
a=ap.parse_args()
def load(p):
    out=[]
    for l in open(p):
        m=re.match(r'0x([0-9a-f]+)\s+(.*)',l.strip())
        if m: out.append((int(m.group(1),16),m.group(2)))
    return out
def ab(t):
    if a.exact: 
        t=re.sub(r'call -?0x[0-9a-f]+','call X',t); t=re.sub(r'lddw (r\d+), 0x[0-9a-f]+',r'lddw \1, X',t)
        t=re.sub(r'(j\w+ .*?)[+-]?0x[0-9a-f]+$',r'\1 L',t) if t.startswith('j') else t
        return t
    t=re.sub(r'\[r10 - 0x[0-9a-f]+\]','[r10-S]',t)
    t=re.sub(r'r10, -0x[0-9a-f]+','r10, -S',t)
    t=re.sub(r'add64 (r\d+), -0x[0-9a-f]+$',r'add64 \1, -S',t)
    t=re.sub(r'call -?0x[0-9a-f]+','call X',t)
    t=re.sub(r'lddw (r\d+), 0x[0-9a-f]+',r'lddw \1, X',t)
    if t.startswith('j'): t=re.sub(r'[+-]?0x[0-9a-f]+$','L',t); t=re.sub(r' -?\d+$',' L',t)
    return t
o=load(a.o); c=load(a.c)
ot=[ab(x[1]) for x in o]; ct=[ab(x[1]) for x in c]
sm=difflib.SequenceMatcher(None,ot,ct,autojunk=False)
print('abstract ratio',round(sm.ratio(),5),'orig',len(o),'cand',len(c))
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal':
        if a.show: print('= %4d  orig %05x-%05x cand %05x-%05x'%(i2-i1,o[i1][0],o[i2-1][0],c[j1][0],c[j2-1][0]))
        continue
    n=max(i2-i1,j2-j1)
    if n<a.min: continue
    os_=('%05x-%05x'%(o[i1][0],o[i2-1][0])) if i2>i1 else ('@%05x'%(o[i1][0] if i1<len(o) else -1))
    cs_=('%05x-%05x'%(c[j1][0],c[j2-1][0])) if j2>j1 else ('@%05x'%(c[j1][0] if j1<len(c) else -1))
    print('%s %4d/%4d orig %-13s cand %-13s'%(tag[0],i2-i1,j2-j1,os_,cs_))
