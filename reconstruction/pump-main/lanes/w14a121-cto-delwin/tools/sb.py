#!/usr/bin/env python3
"""sb.py fn.bin...: list adjacent reload/store-back pairs (ldxdw rX,[r10+o]; stxdw [r10+o],rX)"""
import sys,os,re
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from bdis import decode
for f in sys.argv[1:]:
    I=decode(open(f,'rb').read()); out=[]
    for a,b in zip(I,I[1:]):
        m=re.match(r'ldxdw r(\d+), \[r10(-\d+)\]',a['txt']); n=re.match(r'stxdw \[r10(-\d+)\], r(\d+)',b['txt'])
        if m and n and m.group(1)==n.group(2) and m.group(2)==n.group(1): out.append('%x:%s'%(a['off'],m.group(2)))
    print(f.split('/')[-2] if '/' in f else f, len(out), ' '.join(out))
