#!/usr/bin/env python3
"""opdiff.py <fn.bin> [minlen]: difflib opcodes (masked tokens) between orig window and candidate, with disassembly."""
import sys,os,difflib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import oracle, sbpfdis
o=oracle.orig_window(); c=open(sys.argv[1],'rb').read(); mn=int(sys.argv[2]) if len(sys.argv)>2 else 1
O=oracle.mask(o); Cm=oracle.mask(c)
do=sbpfdis.d(o); dc=sbpfdis.d(c)
sm=difflib.SequenceMatcher(None,O,Cm,autojunk=False)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal': continue
    if max(i2-i1,j2-j1)<mn: continue
    print(f'== {tag} orig[{i1}:{i2}] @{do[i1][0] if i1<len(do) else -1:#x}  ours[{j1}:{j2}] @{dc[j1][0] if j1<len(dc) else -1:#x}')
    for k in range(i1,min(i2,i1+12)): print('   -',f'{do[k][0]:#6x}',do[k][1])
    for k in range(j1,min(j2,j1+12)): print('   +',f'{dc[k][0]:#6x}',dc[k][1])
