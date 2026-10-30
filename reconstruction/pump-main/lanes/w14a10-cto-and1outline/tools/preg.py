#!/usr/bin/env python3
"""preg.py names..: scorer-exact alignment (oracle.mask words), matched orig words per 0x800 region."""
import sys,os,difflib
sys.path.insert(0,os.path.dirname(__file__))
import oracle
O=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
orig=oracle.mask(oracle.orig_window())
cols=[]
for n in sys.argv[1:]:
    c=oracle.mask(open(O+'/rx/%s/fn.bin'%n,'rb').read())
    sm=difflib.SequenceMatcher(None,orig,c,autojunk=False); m=set()
    for a,b,s in sm.get_matching_blocks(): m.update(range(a,a+s))
    cols.append(m)
print('reg   '+' '.join('%9s'%n[-9:] for n in sys.argv[1:]))
for r in range(0,len(orig)*8,0x800):
    print('%5x '%r+' '.join('%9d'%sum(1 for i in c if r<=i*8<r+0x800) for c in cols))
print('total '+' '.join('%9d'%len(c) for c in cols))
