#!/usr/bin/env python3
"""fmap.py <a.bin> <b.bin>: for two frame-only variants (same length, same masked code), print the r10 offset mapping a->b"""
import sys,struct,collections
a=open(sys.argv[1],'rb').read(); b=open(sys.argv[2],'rb').read(); assert len(a)==len(b)
m=collections.defaultdict(collections.Counter)
for i in range(0,len(a),8):
    x=a[i:i+8]; y=b[i:i+8]; op=x[0]; cl=op&7
    if (cl==1 and (x[1]>>4)==10) or (cl in (2,3) and (x[1]&15)==10):
        m[struct.unpack('<h',x[2:4])[0]][struct.unpack('<h',y[2:4])[0]]+=1
    elif op==0x07 and (x[1]&15)==10 or (op==0x07):
        pass
sh=collections.Counter()
for k in sorted(m):
    v=m[k].most_common(1)[0][0]; sh[v-k]+=sum(m[k].values())
    if v!=k: print(f'{k:6d} -> {v:6d} ({v-k:+d}) n={sum(m[k].values())}' + ('' if len(m[k])==1 else f' multi {dict(m[k])}'))
print('shift histogram (by uses):',sh.most_common(8))
