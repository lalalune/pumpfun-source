#!/usr/bin/env python3
"""payreg.py <x.ann>...: count Err-site payload registers (ldxdw rX,[r10-..]; ldxdw r7,[r10-..] pairs)."""
import sys,re,collections
for fn in sys.argv[1:]:
    L=[l.split(None,1)[1].split(';')[0].strip() for l in open(fn) if len(l.split(None,1))>1]
    c=collections.Counter()
    for i in range(len(L)-1):
        m=re.match(r'ldxdw (r\d), \[r10 - 0x[0-9a-f]+\]',L[i]); n=re.match(r'ldxdw r7, \[r10 - 0x[0-9a-f]+\]',L[i+1])
        if m and n: c[m.group(1)]+=1
    print(fn,dict(c))
