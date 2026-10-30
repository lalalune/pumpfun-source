#!/usr/bin/env python3
"""smap.py <m.o> [lo hi]: whole-function regs/frame-masked alignment; per orig frame slot, each access -> aligned cand slot (or '-')."""
import sys,re,difflib,os,collections
sys.path.insert(0,os.path.dirname(__file__))
from slots import orig_dis,cand_dis
def norm(s):
    if s.startswith('call'): return 'call'
    s=re.sub(r'^lddw (r\d+), .*',r'lddw \1',s)
    if s.startswith('j'): s=re.sub(r'([+-]0x[0-9a-f]+|[+-]\d+)$','J',s)
    s=re.sub(r'r10 - 0x[0-9a-f]+','r10-X',s); s=re.sub(r'\br\d\b','r',s)
    return s
def off(s):
    m=re.search(r'r10 - 0x([0-9a-f]+)',s); return int(m.group(1),16) if m else None
p=sys.argv[1]; lo=int(sys.argv[2],16) if len(sys.argv)>2 else 0x8d8; hi=int(sys.argv[3],16) if len(sys.argv)>3 else 0xc38
o=orig_dis(); c=cand_dis(p)
sm=difflib.SequenceMatcher(None,[norm(t) for _,t in o],[norm(t) for _,t in c],autojunk=False)
amap={}
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal':
        for k in range(i2-i1): amap[i1+k]=j1+k
def table(src,dst,amap):
    t=collections.defaultdict(list)
    for i,(pc,s) in enumerate(src):
        f=off(s)
        if f is None or not(lo<=f<=hi): continue
        j=amap.get(i); g=off(dst[j][1]) if j is not None else None
        t[f].append('%s%x>%s'%('S' if s.startswith('st') else 'L',pc,'%x'%g if g else '-'))
    return t
to=table(o,c,amap); inv={v:k for k,v in amap.items()}; tc=table(c,o,inv)
which=sys.argv[4] if len(sys.argv)>4 else 'o'
t=to if which=='o' else tc
for f in sorted(t): print('%x'%f,' '.join(t[f]))
