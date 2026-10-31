#!/usr/bin/env python3
"""jmiss.py fn.bin...: jumps aligned under jump-masking whose offset differs from the original; histogram by orig 0x400 bucket"""
import sys,os,difflib,collections
sys.path.insert(0,os.path.dirname(__file__)); import bwx
o=bwx.orig_toks(); oj=bwx.xtoks(o,1)
oo=[];p=0
for t in o: oo.append(p); p+=len(t)
for f in sys.argv[1:]:
    c=bwx.mask(open(f,'rb').read()); cj=bwx.xtoks(c,1)
    sm=difflib.SequenceMatcher(None,oj,cj,autojunk=False); h=collections.Counter(); n=0; tot=0
    for a,b,k in sm.get_matching_blocks():
        for i in range(k):
            if o[a+i][0]&7==5 and o[a+i][0] not in (0x85,0x95):
                tot+=1
                if o[a+i]!=c[b+i]: n+=1; h[oo[a+i]//0x400]+=1
    print(f, 'jm-matched jumps',tot,'offset-miss',n, ' '.join(f'{k*0x400:#x}:{v}' for k,v in sorted(h.items())))
