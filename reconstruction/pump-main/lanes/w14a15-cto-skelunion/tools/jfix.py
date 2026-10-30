#!/usr/bin/env python3
"""jfix.py name..: raw masked ratio after copying orig jump offsets into jm-aligned cand jumps (ideal jumps), vs plain."""
import sys,os,difflib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import oracle
from jdiag import toks,jm,ot,O
o=oracle.mask(oracle.orig_window())
for n in sys.argv[1:]:
    raw=open(f'{O}/rx/{n}/fn.bin','rb').read(); ct=toks(raw)
    A=[jm(x)[0] for _,x in ot]; B=[jm(x)[0] for _,x in ct]; fixed=bytearray(raw)
    for a,b,s in difflib.SequenceMatcher(None,A,B,autojunk=False).get_matching_blocks():
        for k in range(s):
            (oa,ox),(ca,cx)=ot[a+k],ct[b+k]
            if jm(ox)[1]: fixed[ca+2:ca+4]=ox[2:4]
    c0=oracle.mask(raw); c1=oracle.mask(bytes(fixed))
    print(n, round(difflib.SequenceMatcher(None,o,c0,autojunk=False).ratio(),5), 'jfix', round(difflib.SequenceMatcher(None,o,c1,autojunk=False).ratio(),5))
