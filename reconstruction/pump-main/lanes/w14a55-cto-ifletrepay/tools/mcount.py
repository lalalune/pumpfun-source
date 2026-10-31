#!/usr/bin/env python3
"""mcount.py fn.bin...: M (matched masked tokens vs original) for each rx fn.bin."""
import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__)); exec(open(T+'/rx.py').read().split('OUT=os.environ')[0])
o=mask(orig_window())
for p in sys.argv[1:]:
    c=mask(open(p,'rb').read()); sm=difflib.SequenceMatcher(None,o,c,autojunk=False)
    M=sum(b.size for b in sm.get_matching_blocks()); print(p.split('/')[-2], len(c)*8 if False else len(open(p,'rb').read()), M, round(2*M/(len(o)+len(c)),5))
