#!/usr/bin/env python3
"""chunk.py ref_fn.bin cand_fn.bin... : matched masked tokens (call imm and lddw imm masked) of each candidate against the
original admin_cto::execute window, attributed to original 0x800 chunks; columns after the first are deltas vs the first."""
import sys,os,difflib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import dis as D
def mask(raw):
    m=bytearray(raw); i=0; toks=[]
    while i<len(raw):
        op=raw[i]; n=16 if op==0x18 else 8
        if op==0x85: m[i+1]&=0x0f; m[i+4:i+8]=b'\0'*4
        if op==0x18: m[i+4:i+8]=b'\0'*4; m[i+12:i+16]=b'\0'*4
        toks.append(bytes(m[i:i+n])); i+=n
    return toks
o=D.orig(); oo=[]; i=0
while i<len(o): oo.append(i); i+=16 if o[i]==0x18 else 8
def ch(c):
    sm=difflib.SequenceMatcher(None,mask(o),mask(c),autojunk=False); res=[0]*((len(o)+0x7ff)//0x800)
    for m in sm.get_matching_blocks():
        for k in range(m.size): res[oo[m.a+k]//0x800]+=1
    return res
fs=sys.argv[1:]; R=[ch(open(f,'rb').read()) for f in fs]
for i in range(len(R[0])): print('%05x  '%(i*0x800)+' '.join('%8d'%(r[i]-(R[0][i] if j else 0)) for j,r in enumerate(R)))
print('total  '+' '.join('%8d'%(sum(r)-(sum(R[0]) if j else 0)) for j,r in enumerate(R)))
