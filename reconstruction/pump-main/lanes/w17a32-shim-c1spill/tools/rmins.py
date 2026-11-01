#!/usr/bin/env python3
"""rmins.py <in.bin> <out.bin> off_hex...: delete 8-byte instructions at the given offsets and fix jump offsets
(class JMP/JMP32, not call/exit). Bound helper only (models 'this instruction would not be emitted')."""
import sys,struct
b=bytearray(open(sys.argv[1],'rb').read()); out=sys.argv[2]; rm=sorted(int(x,16) for x in sys.argv[3:])
ins=[];i=0
while i<len(b):
    n=16 if b[i]==0x18 else 8; ins.append((i,n)); i+=n
idx={o:k for k,(o,n) in enumerate(ins)}
# slot index (8-byte units) of each instruction start
slot={o:o//8 for o,n in ins}
rmset=set(rm)
def newslot(s):  # number of removed slots strictly before slot s
    return s-sum(1 for r in rm if r//8<s)
res=bytearray()
for o,n in ins:
    if o in rmset: continue
    x=bytearray(b[o:o+n]); op=x[0]; cl=op&7
    if cl in (5,6) and op not in (0x85,0x95,0x8d):
        off=struct.unpack_from('<h',x,2)[0]; s=o//8; t=s+1+off
        ns=newslot(s); nt=newslot(t)
        struct.pack_into('<h',x,2,nt-ns-1)
    res+=x
open(out,'wb').write(res); print(len(b),'->',len(res))
