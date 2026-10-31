#!/usr/bin/env python3
"""absratio.py <m.dis>...: ratio vs orig with (a) frame offsets masked, (b) frame+regs masked (skeleton). Jumps relative masked."""
import sys,re,difflib
def norm(s,regs):
    s=re.sub(r'\s+<[^>]*>','',s.strip())
    if s.startswith('call'): s='call'
    s=re.sub(r'^lddw (r\d+), .*',r'lddw \1',s)
    if s.startswith('j'): s=re.sub(r'[+-]0x[0-9a-f]+$|[+-]\d+$','J',s)
    s=re.sub(r'r10 - 0x[0-9a-f]+','r10-X',s); s=re.sub(r'(add64 r\d+), -0x[0-9a-f]+',r'\1, -X',s)
    if regs: s=re.sub(r'\br[0-9]\b','R',s)
    return s
O=[l.split(None,1)[1] for l in open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a62-cto-nativeregs/orig.rel') if len(l.split(None,1))>1]
if __name__=='__main__':
  for f in sys.argv[1:]:
    C=[l.split(None,1)[1] for l in open(f) if len(l.split(None,1))>1]
    r=[]
    for regs in (False,True):
        a=[norm(x,regs) for x in O]; b=[norm(x,regs) for x in C]
        r.append(difflib.SequenceMatcher(None,a,b,autojunk=False).ratio())
    print(f'{f}: frame-masked {r[0]:.5f} skeleton {r[1]:.5f} n={len(C)}')
