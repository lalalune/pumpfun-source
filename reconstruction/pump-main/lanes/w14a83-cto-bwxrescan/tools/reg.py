#!/usr/bin/env python3
"""reg.py [--jm] fn.bin...: matched orig tokens per 0x800 orig region (plain or jump-masked alignment)"""
import sys,os,difflib,collections
sys.path.insert(0,os.path.dirname(__file__)); import bwx
jm='--jm' in sys.argv; fs=[f for f in sys.argv[1:] if f!='--jm']
o=bwx.orig_toks(); oo=[];p=0
for t in o: oo.append(p); p+=len(t)
for f in fs:
    c=bwx.mask(open(f,'rb').read())
    A=bwx.xtoks(o,jm); B=bwx.xtoks(c,jm)
    sm=difflib.SequenceMatcher(None,A,B,autojunk=False); h=collections.Counter()
    for a,b,k in sm.get_matching_blocks():
        for i in range(k): h[oo[a+i]//0x800]+=1
    print(f'{f.split("/")[-2]:8}', sum(h.values()), ' '.join(f'{h[k]:4}' for k in range(14)))
