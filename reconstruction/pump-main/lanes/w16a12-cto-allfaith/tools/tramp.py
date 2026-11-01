#!/usr/bin/env python3
"""tramp.py <fn.bin|orig>...: count the original's CPI-result trampoline shape (call; ldxdw r1,[r10-X]; ldxdw rA,[r10-Y]; mov64 r9,r1; ja)
and list `mov64 r9, r1` sites in the tail (>= 0x4000). Experiment only."""
import sys,os,re
sys.path.insert(0,os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'w15'))
import dis as D
for p in sys.argv[1:]:
    b=D.orig() if p=='orig' else open(p,'rb').read()
    L=D.d(b); s=[x[1] for x in L]
    tr=[L[i][0] for i in range(4,len(L)) if s[i]=='mov64 r9, r1' and s[i-3].startswith('call') and s[i-2].startswith('ldxdw r1,') and s[i-1].startswith('ldxdw') and s[i+1].startswith('ja')]
    m9=[hex(o) for o,x in L if x=='mov64 r9, r1' and o>=0x4000]
    print(p.split('/')[-2] if '/' in p else p,'trampolines',[hex(x) for x in tr],'mov64 r9,r1 @tail',m9)
