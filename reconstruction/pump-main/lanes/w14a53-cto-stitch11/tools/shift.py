#!/usr/bin/env python3
"""shift.py <so|fn.bin> : synthetic size-pair oracle. Inserts a junk 8-B slot (+8) at a block start p and/or deletes one
unmatched instruction (-8) at q, fixes every jump offset that crosses, and scores M (rx tokens). Prints the best single
+8 / -8 positions and the best (p,q) pairs at the pinned size. Upper bound for a pure size knob pair (no codegen change)."""
import sys,os,difflib,struct,itertools,multiprocessing as mp
mp=mp.get_context("fork")
sa=sys.argv[:]; sys.argv=['x','n']
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'rx.py')).read().split('OUT=os.environ')[0])
p=sa[1]; raw=open(p,'rb').read() if p.endswith('.bin') else elf_fn(p,KEEP)
ins=[];i=0
while i<len(raw):
    n=16 if raw[i]==0x18 else 8; ins.append(bytearray(raw[i:i+n])); i+=n
def isj(b): op=b[0]; return (op&7) in (5,6) and op not in (0x85,0x95)
slot=[0]
for b in ins: slot.append(slot[-1]+len(b)//8)
OT=mask(orig_window())
def build(add=None,dele=None):
    # add: insn index before which a junk slot is inserted; dele: insn index removed
    out=[]; S=slot
    def newslot(k):  # new slot position of insn k's start
        s=S[k]
        if add is not None and k>=add: s+=1
        if dele is not None and k>dele: s-=1
        return s
    tgt_of={}
    for k,b in enumerate(ins):
        if dele is not None and k==dele: continue
        if add is not None and k==add: out.append(b'\xfe'*8)
        if isj(b):
            off=struct.unpack('<h',bytes(b[2:4]))[0]; t=S[k]+len(b)//8+off
            # find insn index with slot t
            import bisect; ti=bisect.bisect_left(S,t)
            ns=newslot(k)+len(b)//8; nt=newslot(ti)
            if add is not None and ti==add: nt=newslot(ti)-1  # jump to block start lands on the inserted slot? keep target = original insn
            if add is not None and ti==add: nt=newslot(ti)
            nb=bytearray(b); nb[2:4]=struct.pack('<h',nt-ns); b=nb
        out.append(bytes(b))
    return b''.join(out)
def M(c):
    sm=difflib.SequenceMatcher(None,OT,mask(c),autojunk=False); return sum(x.size for x in sm.get_matching_blocks())
def mm(args): a,d=args; return (a,d,M(build(a,d)))
if __name__=='__main__':
    base=M(build()); print('base M',base,len(raw))
    # block starts: jump targets and insns after jumps
    starts=set()
    for k,b in enumerate(ins):
        if isj(b):
            off=struct.unpack('<h',bytes(b[2:4]))[0]; t=slot[k]+len(b)//8+off
            import bisect; starts.add(bisect.bisect_left(slot,t)); starts.add(k+1)
    starts=sorted(x for x in starts if 0<x<len(ins))
    sm=difflib.SequenceMatcher(None,OT,mask(raw),autojunk=False); matched=set()
    # map token index -> insn index (mask tokens are per insn)
    for b in sm.get_matching_blocks():
        for k in range(b.size): matched.add(b.b+k)
    unm=[k for k in range(len(ins)) if k not in matched and not isj(ins[k])]
    STEP=int(os.environ.get('STEP','1'))
    starts=starts[::STEP]; unm=unm[::STEP]
    with mp.Pool(int(os.environ.get('NP','6'))) as P:
        A=P.map(mm,[(a,None) for a in starts]); D=P.map(mm,[(None,d) for d in unm])
    A.sort(key=lambda z:-z[2]); D.sort(key=lambda z:-z[2])
    print('best +8:',[('%05x'%(slot[a]*8),m-base) for a,_,m in A[:12]])
    print('best -8:',[('%05x'%(slot[d]*8),m-base) for _,d,m in D[:12]])
    G=int(os.environ.get('GRID','0'))
    if G:
        def grid(L):
            out=[];last=-10**9
            for k in sorted(L):
                if slot[k]*8-last>=G: out.append(k); last=slot[k]*8
            return out
        TA=grid([a for a,_,_ in A]); TD=grid([d for _,d,_ in D]); print('grid',len(TA),len(TD),flush=True)
    else:
        TA=[a for a,_,_ in A[:int(os.environ.get('TOPA','25'))]]; TD=[d for _,d,_ in D[:int(os.environ.get('TOPD','25'))]]
    with mp.Pool(int(os.environ.get('NP','6'))) as P:
        R=P.map(mm,[(a,d) for a in TA for d in TD])
    R.sort(key=lambda z:-z[2])
    print('best pairs:',[('+%05x'%(slot[a]*8),'-%05x'%(slot[d]*8),m-base) for a,d,m in R[:15]])
    import json; json.dump({'A':[(slot[a]*8,m-base) for a,_,m in A],'D':[(slot[d]*8,m-base) for _,d,m in D],'P':[(slot[a]*8,slot[d]*8,m-base) for a,d,m in R]},open(os.environ.get('SHOUT','/dev/null'),'w'))
