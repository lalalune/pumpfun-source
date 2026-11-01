#!/usr/bin/env python3
import sys,os,struct
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle, sc
def seqoff(b):
    r=[];i=0
    while i<len(b):
        op=b[i]
        if op==0x62:
            imm=struct.unpack_from('<i',b,i+4)[0]
            if 280<=imm<=780: r.append((imm,i))
        i+=16 if op==0x18 else 8
    return r
o=dict((k,v) for k,v in seqoff(oracle.orig_window())[:11])
print('%-14s'%'orig',' '.join('%d@%x'%(k,v) for k,v in seqoff(oracle.orig_window())[:11]))
for p in sys.argv[1:]:
    b=sc.fn(p) if (p.endswith('.s') or p.endswith('.o')) else open(p,'rb').read()
    s=seqoff(b)[:11]
    print('%-14s'%os.path.basename(os.path.dirname(p))[:14],' '.join('%d@%x(%+d)'%(k,v,v-o.get(k,0)) for k,v in s), len(b))
