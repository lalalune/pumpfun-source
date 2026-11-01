#!/usr/bin/env python3
"""mirfix.py: helpers for the MIR (after two-address) round-trip oracle. fix(b): rebase the outgoing stack-arg stores
that the MIR round trip places at [r10+X] back to [r10-0x1000+X] (the only difference vs the direct pipeline)."""
import struct
def fix(b):
    b=bytearray(b); i=0
    while i<len(b):
        op=b[i]; n=16 if op==0x18 else 8; cl=op&7
        if cl in (2,3) and (b[i+1]&15)==10:
            off=struct.unpack_from('<h',b,i+2)[0]
            if off>=0: struct.pack_into('<h',b,i+2,off-0x1000)
        i+=n
    return bytes(b)
