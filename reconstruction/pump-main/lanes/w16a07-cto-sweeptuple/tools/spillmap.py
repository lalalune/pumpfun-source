#!/usr/bin/env python3
"""spillmap.py <orig.bin> <cand.bin> [lo hi] : sweep-body spill map (experiment only).
For every 8 B spill-slot store in orig[lo,hi): the stored value's def (backward scan), the slot, its reload pcs, and the
frame-masked aligned candidate instruction (slot/def there). Spill set = relab.binspills."""
import sys,os,struct,difflib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import relab as R, bdis
def dec(b):
    I=[];i=0
    while i<len(b):
        op,r,off,imm=struct.unpack_from('<BBhi',b,i); n=16 if op==0x18 else 8; I.append((i,op,r&15,r>>4,off,imm)); i+=n
    return I
TXT=lambda b:{o:t for o,t in bdis.dis(b)}
def writes(ins):
    o,op,d,s,off,imm=ins; c=op&7
    if op==0x85: return 0
    if c in (1,4,7) or op==0x18: return d
    return None
def defof(I,k,reg,T,lim=160):
    for j in range(k-1,max(-1,k-lim),-1):
        w=writes(I[j])
        if w==reg: return f'{I[j][0]:04x} {T[I[j][0]]}'
        if I[j][1] in (0x05,0x95): return 'join/'+f'{I[j][0]:04x}'
    return '?'
def stores(b,sp,lo,hi):
    I=dec(b); T=TXT(b); out=[]
    for k,ins in enumerate(I):
        o,op,d,s,off,imm=ins
        if lo<=o<hi and op==0x7b and d==10 and off in sp:
            out.append((o,off,s,defof(I,k,s,T)))
    return out
def reloads(b,off):
    return [o for (o,op,d,s,of,imm) in dec(b) if op==0x79 and s==10 and of==off]
def align(a,b):
    ai=R.ins(a); bi=R.ins(b)
    sm=difflib.SequenceMatcher(None,R.g['mask'](R.fmask(a)),R.g['mask'](R.fmask(b)),autojunk=False)
    m={}
    for x,y,n in sm.get_matching_blocks():
        for k in range(n): m[ai[x+k][0]]=bi[y+k][0]
    return m
if __name__=='__main__':
    A=open(sys.argv[1],'rb').read(); B=open(sys.argv[2],'rb').read()
    lo=int(sys.argv[3],16) if len(sys.argv)>3 else 0; hi=int(sys.argv[4],16) if len(sys.argv)>4 else 1<<30
    spA=R.binspills(A); spB=R.binspills(B); TB=TXT(B); m=align(A,B)
    for o,off,s,d in stores(A,spA,lo,hi):
        rl=[f'{x:04x}' for x in reloads(A,off) if x>o][:6]
        c=m.get(o); ct=f'{c:04x} {TB[c]}' if c is not None else '-'
        print(f'{o:04x} [{-off:#x}] r{s} <= {d:42s} | reloads {",".join(rl):34s} | cand {ct}')
