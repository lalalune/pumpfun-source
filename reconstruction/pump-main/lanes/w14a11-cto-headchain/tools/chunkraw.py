#!/usr/bin/env python3
"""chunkraw.py <a.txt> <b.txt> [chunk]: like chunkfm but frame offsets kept (only jump targets/calls/lddw masked)."""
import sys,difflib,re
sys.path.insert(0,__import__('os').path.dirname(__file__)); import absratio as A
def nr(s):
    s=re.sub(r'\s+<[^>]*>','',s.strip())
    if s.startswith('call'): return 'call'
    s=re.sub(r'^lddw (r\d+), .*',r'lddw \1',s)
    if s.startswith('j'): s=re.sub(r'[+-]0x[0-9a-f]+$|[+-]\d+$','J',s)
    return s
O=[nr(x) for x in A.O]
def m(f):
    C=[nr(l) for l in open(f) if l.strip()]
    sm=difflib.SequenceMatcher(None,O,C,autojunk=False); hit=[0]*len(O)
    for b in sm.get_matching_blocks():
        for k in range(b.size): hit[b.a+k]=1
    return hit
ch=int(sys.argv[3]) if len(sys.argv)>3 else 256
ha,hb=m(sys.argv[1]),m(sys.argv[2])
for i in range(0,len(O),ch):
    a,b=sum(ha[i:i+ch]),sum(hb[i:i+ch]); print(f'{i*8:#07x} {a:4d} {b:4d} {b-a:+d}')
print('total',sum(ha),sum(hb),sum(hb)-sum(ha))
