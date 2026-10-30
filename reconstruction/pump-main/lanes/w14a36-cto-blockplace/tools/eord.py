#!/usr/bin/env python3
"""eord.py <fn.bin>: error-site line order (stw [r10-X], line followed by From call) in a candidate function body."""
import sys,struct
b=open(sys.argv[1],'rb').read(); i=0; out=[]; last=None
while i<len(b):
    op=b[i]
    if op==0x62:  # stw imm
        imm=struct.unpack_from('<i',b,i+4)[0]
        if 250<imm<800: last=imm
    if op==0x85 and last: out.append(last); last=None
    i+=16 if op==0x18 else 8
print(' '.join(map(str,out)))
