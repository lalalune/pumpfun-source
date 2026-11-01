#!/usr/bin/env python3
# jm.py <name>: jumps aligned (full mask) with a different displacement, grouped; prints orig off, target, delta (orig-cand, in instructions)
import sys,os,difflib,re
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w19b13-cto-v1-holder-and1')
sys.path.insert(0,OUT+'/tools')
import dis as D, oracle
W=D.W
def toks(raw):
    i=0; L=[]
    while i<len(raw):
        n=16 if raw[i]==0x18 else 8
        L.append((i,raw[i:i+n])); i+=n
    return L
JMP={0x05,0x15,0x1d,0x25,0x2d,0x35,0x3d,0x45,0x4d,0x55,0x5d,0x65,0x6d,0x75,0x7d,0xa5,0xad,0xb5,0xbd,0xc5,0xcd,0xd5,0xdd}
def ab(t):
    t=bytearray(t); op=t[0]
    if op==0x85: t[1]&=0x0f; t[4:8]=b'\0'*4
    if op==0x18: t[4:8]=b'\0'*4; t[12:16]=b'\0'*4
    if op in JMP: t[2:4]=b'\0\0'
    return bytes(t)
def ab2(t):
    t=bytearray(ab(t)); op=t[0]
    # frame + regs
    t[1]=0
    if op in (0x79,0x71,0x69,0x61,0x7b,0x73,0x6b,0x63,0x7a,0x72,0x6a,0x62):
        pass
    return bytes(t)
n=sys.argv[1]
O=toks(oracle.orig_window()); C=toks(open(f'{OUT}/fx/{n}/fn.bin','rb').read())
ao=[ab(t) for _,t in O]; ac=[ab(t) for _,t in C]
sm=difflib.SequenceMatcher(None,ao,ac,autojunk=False)
rows=[]
for m in sm.get_matching_blocks():
    for k in range(m.size):
        oo,to=O[m.a+k]; oc,tc=C[m.b+k]
        if to[0] in JMP and to!=tc:
            do=int.from_bytes(to[2:4],'little',signed=True); dc=int.from_bytes(tc[2:4],'little',signed=True)
            rows.append((oo,oc,do,dc))
print(len(rows),'jump-only mismatches at exact-minus-jump alignment')
for oo,oc,do,dc in rows:
    print(f'o{oo:#06x}->{oo+8+do*8:#06x} c{oc:#06x}->{oc+8+dc*8:#06x} d {do-dc:+d}')
