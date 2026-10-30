#!/usr/bin/env python3
"""tagbound.py <fn.bin|unstripped.so> <dis.txt> [tagslot]: ratio bound if the sharing_update tag lived in r6 exactly like the original.
(1) every ours token FR-aligned to an orig token that reads/writes r6 inside the original's tag-in-r6 ranges takes the orig token;
(2) ours-only tag spill/reload instructions (ldxdw/stxdw at the tag slot, not aligned) are deleted.
Reports base ratio, bound(1), bound(1+2). Experiment only."""
import sys,os,re,difflib,json
T=os.path.dirname(os.path.abspath(__file__)); src=open(T+'/rx.py').read(); g={}; exec(src.split("OUT=os.environ")[0],g)
p,dp=sys.argv[1],sys.argv[2]; slot=int(sys.argv[3],16) if len(sys.argv)>3 else 0x8e8
raw=g['elf_fn'](p,g['KEEP']) if p.endswith('.so') or p.endswith('.o') else open(p,'rb').read()
orig=g['orig_window']()
def split(r):
    out=[];i=0
    while i<len(r):
        n=16 if r[i]==0x18 else 8; out.append(bytes(r[i:i+n])); i+=n
    return out
def mask(t):
    b=bytearray(t)
    if b[0]==0x85: b[1]&=0x0f; b[4:8]=b'\0'*4
    if b[0]==0x18: b[4:8]=b'\0'*4; b[12:16]=b'\0'*4
    return bytes(b)
def fr(t):
    b=bytearray(mask(t)); r=b[1]
    if (r&0xf)==10 or (r>>4)==10: b[2:4]=b'\0\0'
    if b[0]&7 in (5,6) or b[0]==0x05: b[2:4]=b'\0\0'  # jump offsets
    b[1]=(0xa0 if (r>>4)==10 else 0)|(0x0a if (r&0xf)==10 else 0); return bytes(b)
OT=split(orig); CT=split(raw)
OFF=[];o=0
for t in OT: OFF.append(o); o+=len(t)
COFF=[];o=0
for t in CT: COFF.append(o); o+=len(t)
R6=[(0x1d30,0x20f0),(0x3c58,0x3d28),(0x4a90,0x4c50),(0x4d48,0x4f38),(0x60d8,0x60f8)]
def inr6(a): return any(lo<=a<hi for lo,hi in R6)
def uses_r6(t): return (t[1]&0xf)==6 or (t[1]>>4)==6
def ratio(a,b): return difflib.SequenceMatcher(None,[mask(x) for x in a],[mask(x) for x in b],autojunk=False).ratio()
base=ratio(OT,CT)
sm=difflib.SequenceMatcher(None,[fr(t) for t in OT],[fr(t) for t in CT],autojunk=False)
c=list(CT); aligned=set(); n1=0
for a,b,s in sm.get_matching_blocks():
    for k in range(s):
        aligned.add(b+k)
        if inr6(OFF[a+k]) and uses_r6(OT[a+k]) and c[b+k]!=OT[a+k]: c[b+k]=OT[a+k]; n1+=1
b1=ratio(OT,c)
dis={int(l.split()[0],16):l.split(None,1)[1].strip() for l in open(dp) if l.strip()}
pat=re.compile(r'(ldxdw r\d, \[r10 - 0x%x\]|stxdw \[r10 - 0x%x\], r\d)$'%(slot,slot))
dele=[i for i in range(len(CT)) if i not in aligned and COFF[i]>=int(os.environ.get("DELLO","0"),16) and pat.search(dis.get(COFF[i],""))]
c2=[t for i,t in enumerate(c) if i not in set(dele)]
b2=ratio(OT,c2)
print(json.dumps({'base':round(base,5),'r6_fixed':n1,'bound_r6':round(b1,5),'deleted':len(dele),'bound_r6_del':round(b2,5),'del_at':[hex(COFF[i]) for i in dele]}))
