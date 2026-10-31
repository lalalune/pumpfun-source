#!/usr/bin/env python3
"""whyins.py <fn.bin> <cand_off_hex> [N]: which original tokens become matched/unmatched when N junk 8-byte slots are
inserted before the instruction at cand_off (jumps re-fixed, as insmapn.py). Prints the gained/lost aligned pairs."""
import sys,os,struct,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
from oracle import mask,orig_window
from bdis import dis
raw=open(sys.argv[1],'rb').read(); at=int(sys.argv[2],16); N=int(sys.argv[3]) if len(sys.argv)>3 else 1
OR=orig_window(); OT=mask(OR); JUNK=bytes([0xff,0,0,0,0,0,0,0])
def parse(raw):
    ins=[];i=0
    while i<len(raw):
        n=16 if raw[i]==0x18 else 8; ins.append(bytes(raw[i:i+n])); i+=n
    return ins
def isj(b): op=b[0]; return (op&7) in (5,6) and op not in (0x85,0x95)
INS=parse(raw); SLOT=[0]
for b in INS: SLOT.append(SLOT[-1]+len(b)//8)
k=[j for j in range(len(INS)) if SLOT[j]*8==at][0]
out=[]
for j,b in enumerate(INS):
    if j==k: out.extend([JUNK]*N)
    if isj(b):
        off=struct.unpack('<h',b[2:4])[0]; t=SLOT[j]+1+off
        ns=SLOT[j]+(N if j>=k else 0)+1; nt=t+(N if t>=SLOT[k] else 0)
        bb=bytearray(b); bb[2:4]=struct.pack('<h',nt-ns); b=bytes(bb)
    out.append(b)
new=b''.join(out)
def pairs(c):
    ct=mask(c); sm=difflib.SequenceMatcher(None,OT,ct,autojunk=False); s=set()
    for a,b2,n in sm.get_matching_blocks():
        for i in range(n): s.add(a+i)
    return s
p0=pairs(raw); p1=pairs(new)
od=dict(dis(OR)); ooff=[]; i=0
while i<len(OR): ooff.append(i); i+=16 if OR[i]==0x18 else 8
print('M',len(p0),'->',len(p1))
print('gained orig tokens:',[(hex(ooff[x]),od[ooff[x]]) for x in sorted(p1-p0)][:30])
print('lost orig tokens:',[(hex(ooff[x]),od[ooff[x]]) for x in sorted(p0-p1)][:30])
