#!/usr/bin/env python3
"""rdiff.py <fn.bin> lo hi [mode]: show m<mode>-masked diff ops between orig[lo,hi) and the aligned candidate span."""
import sys,os,difflib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import skel,oracle,d as D
O=oracle.orig_window(); b=D.load(sys.argv[1]); lo=int(sys.argv[2],16); hi=int(sys.argv[3],16); mode=int(sys.argv[4]) if len(sys.argv)>4 else 3
od=D.dis(O); bd=D.dis(b)
to=skel.toks(O,mode); tb=skel.toks(b,mode)
sm=difflib.SequenceMatcher(None,to,tb,autojunk=False)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if od[i1 if i1<len(od) else -1][0]<lo and (i2>=len(od) or od[i2-1][0]<lo): continue
    if i1<len(od) and od[i1][0]>=hi: break
    if tag=='equal': print('   = %d tokens orig %#x cand %#x'%(i2-i1,od[i1][0],bd[j1][0])); continue
    print('  %s orig[%d] cand[%d]'%(tag,i2-i1,j2-j1))
    for k in range(i1,i2): print('     - %#06x %s'%od[k])
    for k in range(j1,j2): print('     + %#06x %s'%bd[k])
