#!/usr/bin/env python3
"""fmap.py <fn.bin>: align orig vs cand on frame+reg+jump-masked tokens; tabulate r10 offset pairs (orig->cand) and reg pairs."""
import sys,os,difflib,collections,struct
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import oracle, mmask
O=oracle.orig_window()
def dec(raw):
    out=[];i=0
    while i<len(raw):
        op=raw[i]; n=16 if op==0x18 else 8; t=raw[i:i+n]
        dst=t[1]&0xf; src=t[1]>>4; off=struct.unpack_from('<h',t,2)[0]; cls=op&7
        fo=None
        if cls==1 and src==10: fo=off
        if cls in (2,3) and dst==10: fo=off
        out.append((i,op,dst,src,fo)); i+=n
    return out
def run(c,lo=0,hi=1<<30):
    a=mmask.toks(O,frame=True,regs=True,jumps=True); b=mmask.toks(c,frame=True,regs=True,jumps=True)
    da=dec(O); db=dec(c)
    sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
    F=collections.Counter(); Rg=collections.Counter()
    for x,y,n in sm.get_matching_blocks():
        for k in range(n):
            oa=da[x+k]; ob=db[y+k]
            if not (lo<=oa[0]<hi): continue
            if oa[4] is not None: F[(oa[4],ob[4])]+=1
    return F
if __name__=='__main__':
    c=open(sys.argv[1],'rb').read()
    lo=int(sys.argv[2],16) if len(sys.argv)>2 else 0; hi=int(sys.argv[3],16) if len(sys.argv)>3 else 1<<30
    F=run(c,lo,hi)
    same=sum(v for (p,q),v in F.items() if p==q); diff=sum(v for (p,q),v in F.items() if p!=q)
    print('frame accesses aligned: same',same,'diff',diff)
    for (p,q),v in sorted([kv for kv in F.items() if kv[0][0]!=kv[0][1]],key=lambda kv:-kv[1])[:40]:
        if 1: print(f"  orig {p:#x} -> cand {q:#x}  x{v}")
