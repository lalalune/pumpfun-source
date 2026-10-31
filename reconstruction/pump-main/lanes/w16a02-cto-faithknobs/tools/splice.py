#!/usr/bin/env python3
"""splice.py: binary splice oracle for composites (experiment only, analysis bound, never a source proposal).
splice(base, [var1, var2, ...]) applies each variant's instruction-level diff against base (difflib on jump-normalised
tokens) to base and re-resolves every jump displacement, so the composite is what a combined build gives when the
variants' changes are local and do not interact through register allocation. Overlapping hunks -> None.
CLI: splice.py <base fn.bin> <var fn.bin>... prints bytes and M of the splice; --check <combined fn.bin> compares."""
import sys,os,struct,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
from oracle import mask,orig_window
def parse(raw):
    ins=[];i=0
    while i<len(raw):
        n=16 if raw[i]==0x18 else 8; ins.append(bytes(raw[i:i+n])); i+=n
    return ins
def isj(b): op=b[0]; return (op&7) in (5,6) and op not in (0x85,0x95)
def targets(ins):
    slot=[0]
    for b in ins: slot.append(slot[-1]+len(b)//8)
    s2i={s:k for k,s in enumerate(slot[:-1])}
    tg=[]
    for k,b in enumerate(ins):
        if isj(b):
            off=struct.unpack('<h',b[2:4])[0]; tg.append(s2i.get(slot[k]+1+off))
        else: tg.append(None)
    return tg
def norm(b):
    if isj(b): bb=bytearray(b); bb[2:4]=b'\0\0'; b=bytes(bb)
    if b[0]==0x85: bb=bytearray(b); bb[1]&=0x0f; bb[4:8]=b'\0'*4; b=bytes(bb)
    if b[0]==0x18: bb=bytearray(b); bb[4:8]=b'\0'*4; bb[12:16]=b'\0'*4; b=bytes(bb)
    return b
class Var:
    def __init__(s,base_ins,raw):
        s.ins=parse(raw); s.tg=targets(s.ins)
        sm=difflib.SequenceMatcher(None,[norm(x) for x in base_ins],[norm(x) for x in s.ins],autojunk=False)
        s.hunks=[(i1,i2,j1,j2) for t,i1,i2,j1,j2 in sm.get_opcodes() if t!='equal']
        s.v2b={}   # variant index -> base index for equal regions
        for t,i1,i2,j1,j2 in sm.get_opcodes():
            if t=='equal':
                for d in range(i2-i1): s.v2b[j1+d]=i1+d
def splice(base_raw,var_raws,B=None,BT=None):
    if B is None: B=parse(base_raw); BT=targets(B)
    vs=[r if isinstance(r,Var) else Var(B,r) for r in var_raws]
    # collect hunks with owner, check overlap (touching insertions at the same point also conflict)
    hs=[]
    for vi,v in enumerate(vs):
        for (i1,i2,j1,j2) in v.hunks: hs.append((i1,i2,j1,j2,vi))
    hs.sort()
    for a,b in zip(hs,hs[1:]):
        if b[0]<a[1] or (b[0]==a[0] and a[4]!=b[4]): return None
    out=[]   # list of (bytes, ('b',idx) | ('v',vi,idx))
    b2o={}; v2o={}
    k=0; hi=0
    while k<=len(B):
        while hi<len(hs) and hs[hi][0]==k:
            i1,i2,j1,j2,vi=hs[hi]
            first=len(out)
            for j in range(j1,j2): v2o[(vi,j)]=len(out); out.append((vs[vi].ins[j],('v',vi,j)))
            for i in range(i1,i2): b2o[i]=first if j2>j1 else None   # deleted/replaced base insn -> start of hunk output
            k=i2 if i2>i1 else k; hi+=1
            if i2>i1: break
        else:
            if k==len(B): break
            if k not in b2o: b2o[k]=len(out); out.append((B[k],('b',k)))
            k+=1
            continue
        if k==len(B): break
    # fill None for deleted base insns: map to next output position
    for i in range(len(B)):
        if b2o.get(i) is None:
            j=i+1
            while j<len(B) and b2o.get(j) is None: j+=1
            b2o[i]=b2o.get(j,len(out)) if j<len(B) else len(out)
    slot=[0]
    for b,_ in out: slot.append(slot[-1]+len(b)//8)
    res=[]
    for o,(b,src) in enumerate(out):
        if isj(b):
            if src[0]=='b': t=BT[src[1]]; to=b2o.get(t)
            else:
                vi,j=src[1],src[2]; tv=vs[vi].tg[j]
                to=v2o.get((vi,tv))
                if to is None:
                    tb=vs[vi].v2b.get(tv); to=b2o.get(tb) if tb is not None else None
            if to is None: return None
            bb=bytearray(b); bb[2:4]=struct.pack('<h',slot[to]-(slot[o]+1)); b=bytes(bb)
        res.append(b)
    return b''.join(res)
OT=None
def M(raw):
    global OT
    if OT is None: OT=mask(orig_window())
    return sum(x.size for x in difflib.SequenceMatcher(None,OT,mask(raw),autojunk=False).get_matching_blocks())
if __name__=='__main__':
    a=sys.argv[1:]; chk=None
    if '--check' in a: i=a.index('--check'); chk=a[i+1]; del a[i:i+2]
    base=open(a[0],'rb').read(); vs=[open(x,'rb').read() for x in a[1:]]
    s=splice(base,vs)
    if s is None: print('conflict'); sys.exit(1)
    print('bytes',len(s),'M',M(s))
    if chk:
        c=open(chk,'rb').read(); print('check: identical' if mask(c)==mask(s) else f'check: differs (combined bytes {len(c)} M {M(c)})')
