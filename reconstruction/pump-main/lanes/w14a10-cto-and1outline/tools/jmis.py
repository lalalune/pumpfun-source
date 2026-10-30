#!/usr/bin/env python3
"""jmis.py names..: jump-masked alignment; count aligned jumps whose offset differs, per 0x800 orig region (src) and by target region."""
import sys,os,difflib,struct,collections
sys.path.insert(0,os.path.dirname(__file__))
import oracle
from jr import jm
O=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
orig=oracle.mask(oracle.orig_window()); jo=jm(orig)
for n in sys.argv[1:]:
    c=oracle.mask(open(O+'/rx/%s/fn.bin'%n,'rb').read()); jc=jm(c)
    sm=difflib.SequenceMatcher(None,jo,jc,autojunk=False)
    bad=collections.Counter(); badt=collections.Counter(); tot=0
    for a,b,s in sm.get_matching_blocks():
        for i in range(s):
            if orig[a+i]!=c[b+i]:
                tot+=1; bad[(a+i)*8//0x800]+=1
                off=struct.unpack('<h',orig[a+i][2:4])[0]; badt[((a+i+1+off)*8)//0x800]+=1
    print(n,'mismatched jumps',tot,' by src:',' '.join('%x:%d'%(k*0x800,v) for k,v in sorted(bad.items())))
    print('   by orig target:',' '.join('%x:%d'%(k*0x800,v) for k,v in sorted(badt.items())))
