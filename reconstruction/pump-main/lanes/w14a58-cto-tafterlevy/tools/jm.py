#!/usr/bin/env python3
"""jm.py <name...>: ratio with jump offsets masked (upper bound if jumps fixed) from rx/<n>/fn.bin."""
import sys,os,difflib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import oracle
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a58-cto-tafterlevy')
def jm(raw):
    t=oracle.mask(raw); out=[]
    for x in t:
        op=x[0]
        if (op&7) in (5,6) and op not in (0x85,0x95): x=x[:2]+b'\0\0'+x[4:]
        out.append(x)
    return out
o=jm(oracle.orig_window())
_A=sys.argv[1:] if __name__=="__main__" else []
for n in _A:
    c=jm(open(f'{O}/rx/{n}/fn.bin','rb').read())
    print(n, round(difflib.SequenceMatcher(None,o,c,autojunk=False).ratio(),5))
