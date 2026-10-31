#!/usr/bin/env python3
"""mm.py <rxname|.so|.bin>...: bytes, M (scorer matched tokens), skM, ours-only/orig-only tokens"""
import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled
O=oracle.orig_window(); ot=oracle.mask(O)
for p in sys.argv[1:]:
    q=p if (p=='main' or '.' in p) else f'{os.path.dirname(T)}/rx/{p}/fn.bin'
    c=xled.load(q); ct=oracle.mask(c)
    sm=difflib.SequenceMatcher(None,ot,ct,autojunk=False); M=sum(b.size for b in sm.get_matching_blocks())
    r=xled.run(q,show=False)
    print(f"{os.path.basename(p):24s} bytes {len(c)} M {M} ratio {2*M/(len(ot)+len(ct)):.5f} skM {r['skM']} ours_only {r['ours_only_tok']} orig_only {r['orig_only_tok']}")
