#!/usr/bin/env python3
"""qflip.py: binary `?`-polarity flip composition oracle (experiment only). flip(raw,k): `jeq rX,2,+1; ja +X` at
instruction index k becomes `jne rX,2,+X`, jumps re-fixed. Sites: A6 = 660 AMM token_raw_amount test (second
[acc+0x88] call), SH = sharing-CPI `?` (ldxdw r8,[r10-X]; ldxdw r7,[r10-X-8]; jeq r7,2,+1; ja) = sh_iflet."""
import struct,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
def parse(raw):
    ins=[];i=0
    while i<len(raw):
        n=16 if raw[i]==0x18 else 8; ins.append(bytearray(raw[i:i+n])); i+=n
    return ins
def isj(b): op=b[0]; return (op&7) in (5,6) and op not in (0x85,0x95)
def off(b): return struct.unpack_from('<h',b,2)[0]
def flip(raw,k):
    I=parse(raw); slot=[0]
    for b in I: slot.append(slot[-1]+len(b)//8)
    ja=I[k+1]; tgt=slot[k+1]+1+off(ja); rm=slot[k+1]
    out=[]
    for idx,b in enumerate(I):
        if idx==k+1: continue
        b=bytearray(b); os_=slot[idx]
        if idx==k: b[0]=0x55; t=tgt
        elif isj(b): t=os_+1+off(b)
        else: out.append(bytes(b)); continue
        ns=os_-(1 if os_>rm else 0); nt=t-(1 if t>rm else 0)
        struct.pack_into('<h',b,2,nt-(ns+1)); out.append(bytes(b))
    return b''.join(out)
def isq(I,k):  # jeq rX,2,+1 ; ja
    c,d=I[k],I[k+1]
    return c[0]==0x15 and struct.unpack_from('<i',c,4)[0]==2 and off(c)==1 and d[0]==0x05
def site_A6(raw):
    I=parse(raw); s=[]
    for k in range(len(I)-8):
        b=I[k]
        if b[0]==0x79 and (b[1]&15)==2 and (b[1]>>4)!=10 and off(b)==0x88:
            for j in range(k+1,min(k+6,len(I)-3)):
                if I[j][0]==0x85:
                    a=I[j+1]
                    if a[0]==0x79 and (a[1]&15)==7 and off(a)==-0x2d0 and isq(I,j+2): s.append(j+2)
                    break
    return s[1] if len(s)>=2 else None
def site_SH(raw):
    I=parse(raw); s=[]
    for k in range(len(I)-4):
        a,b=I[k],I[k+1]
        if a[0]==0x79 and (a[1]&15)==8 and (a[1]>>4)==10 and b[0]==0x79 and (b[1]&15)==7 and (b[1]>>4)==10 and off(b)==off(a)-8 and isq(I,k+2): s.append(k+2)
    return s[0] if len(s)==1 else None
def apply(raw,sites):
    for nm in sites:
        k={'A6':site_A6,'SH':site_SH}[nm](raw)
        if k is None: return None
        raw=flip(raw,k)
    return raw
