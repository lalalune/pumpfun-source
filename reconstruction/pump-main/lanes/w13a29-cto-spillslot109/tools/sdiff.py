#!/usr/bin/env python3
"""sdiff.py <m.o> olo ohi clo chi: side-by-side aligned diff (frame offsets kept, regs kept) of orig vs cand ranges."""
import sys,re,difflib,os
sys.path.insert(0,os.path.dirname(__file__))
from slots import orig_dis,cand_dis
def norm(s):
    if s.startswith('call'): return 'call'
    s=re.sub(r'^lddw (r\d+), .*',r'lddw \1',s)
    if s.startswith('j'): s=re.sub(r'([+-]0x[0-9a-f]+|[+-]\d+)$','J',s)
    s=re.sub(r'r10 - 0x[0-9a-f]+','r10-X',s); s=re.sub(r'\br\d\b','r',s)
    return s
p=sys.argv[1]; ol,oh,cl,ch=[int(x,16) for x in sys.argv[2:6]]
o=[x for x in orig_dis() if ol<=x[0]<oh]; c=[x for x in cand_dis(p) if cl<=x[0]<ch]
sm=difflib.SequenceMatcher(None,[norm(t) for _,t in o],[norm(t) for _,t in c],autojunk=False)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    n=max(i2-i1,j2-j1)
    for k in range(n):
        a=o[i1+k] if i1+k<i2 else None; b=c[j1+k] if j1+k<j2 else None
        print('%s %5s %-34s | %5s %s'%(' ' if tag=='equal' else '*', '%x'%a[0] if a else '', a[1] if a else '', '%x'%b[0] if b else '', b[1] if b else ''))
