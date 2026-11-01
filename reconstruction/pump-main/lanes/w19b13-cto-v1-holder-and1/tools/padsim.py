#!/usr/bin/env python3
"""padsim.py <fn.bin> <n_total_pads> [--keep-size]: simulate moving volatile holder_key byte reads (pads) without llc.
Removes pads, then greedily places n pads at block boundaries to maximise LCS with the original (rapidfuzz proxy), difflib confirm.
Assumes register allocation is unaffected by pads (validate with llc)."""
import sys,os,re,difflib,json,random
from rapidfuzz.distance import LCSseq
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w19b13-cto-v1-holder-and1')
sys.path.insert(0,OUT+'/tools')
import oracle
JMP={0x05,0x15,0x1d,0x25,0x2d,0x35,0x3d,0x45,0x4d,0x55,0x5d,0x65,0x6d,0x75,0x7d,0xa5,0xad,0xb5,0xbd,0xc5,0xcd,0xd5,0xdd}
PADOFF=-0x6a0
def parse(raw):
    i=0; L=[]
    while i<len(raw):
        n=16 if raw[i]==0x18 else 8
        L.append(bytearray(raw[i:i+n])); i+=n
    return L
def is_pad(t):
    return t[0]==0x71 and (t[1]>>4)==10 and int.from_bytes(t[2:4],'little',signed=True)==PADOFF
class Sim:
    def __init__(s,raw):
        s.toks=parse(raw)
        # slot offsets
        s.slot=[]; k=0
        for t in s.toks:
            s.slot.append(k); k+=len(t)//8
        s.total=k
        s.slot2idx={sl:i for i,sl in enumerate(s.slot)}
        # target index for jumps
        s.tgt={}
        for i,t in enumerate(s.toks):
            if t[0] in JMP:
                d=int.from_bytes(t[2:4],'little',signed=True)
                sl=s.slot[i]+1+d
                s.tgt[i]=s.slot2idx.get(sl)
        s.heads=set(v for v in s.tgt.values() if v is not None)
        for i,t in enumerate(s.toks):
            if t[0] in JMP and i+1<len(s.toks): s.heads.add(i+1)
    def build(s,removed,pads):
        """removed: set of token idx to drop; pads: dict idx->count of pads inserted before token idx"""
        # new index
        out=[]; newidx={}
        pad=bytearray(b'\x71\xa1'+(PADOFF&0xffff).to_bytes(2,'little')+b'\0\0\0\0')
        k=0; slot=[]
        for i,t in enumerate(s.toks):
            newidx[i]=len(out)  # jump to i lands before inserted pads? see below
            for _ in range(pads.get(i,0)):
                out.append(bytes(pad))
            if i in removed: continue
            out.append(t)
        # slots of new stream
        sl=[]; k=0
        for t in out:
            sl.append(k); k+=len(t)//8
        # map: position of token i (after its pads)
        pos={}
        j=0
        for i,t in enumerate(s.toks):
            j+=pads.get(i,0)
            pos[i]=j
            if i not in removed: j+=1
        # pads belong to the block of the target: a jump to token i lands on first pad before i
        res=[]
        for i,t in enumerate(s.toks):
            pass
        final=[bytes(x) for x in out]
        for i,t in enumerate(s.toks):
            if i in removed or t[0] not in JMP: continue
            ti=s.tgt.get(i)
            if ti is None: continue
            me=pos[i]
            tj=pos[ti]-pads.get(ti,0)
            d=sl[tj]-(sl[me]+1)
            b=bytearray(t); b[2:4]=(d&0xffff).to_bytes(2,'little')
            final[me]=bytes(b)
        return final
    def maskt(s,t):
        t=bytearray(t); op=t[0]
        if op==0x85: t[1]&=0x0f; t[4:8]=b'\0'*4
        if op==0x18: t[4:8]=b'\0'*4; t[12:16]=b'\0'*4
        return bytes(t)
O=[bytes(t) for t in oracle.mask(oracle.orig_window())]
OH=[hash(t) for t in O]
def lcs(sim,final):
    return LCSseq.similarity(OH,[hash(sim.maskt(t)) for t in final])
def dl(sim,final):
    c=[sim.maskt(t) for t in final]
    sm=difflib.SequenceMatcher(None,O,c,autojunk=False)
    return sum(x.size for x in sm.get_matching_blocks())
if __name__=='__main__':
    raw=open(sys.argv[1],'rb').read(); n=int(sys.argv[2])
    S=Sim(raw)
    pads0=[i for i,t in enumerate(S.toks) if is_pad(t)]
    print('tokens',len(S.toks),'slots',S.total,'pads',len(pads0),[hex(S.slot[i]*8) for i in pads0])
    base=lcs(S,S.build(set(),{})); print('base lcs',base,'difflib',dl(S,S.build(set(),{})))
    rem=set(pads0)
    b0=S.build(rem,{}); print('no pads: lcs',lcs(S,b0),'difflib',dl(S,b0),'slots',sum(len(t)//8 for t in b0))
    cand=sorted(S.heads)
    if '--all' in sys.argv: cand=list(range(len(S.toks)))
    pads={}
    cur=lcs(S,S.build(rem,pads)); hist=[]
    for r in range(n):
        best=None
        for p in cand:
            q=dict(pads); q[p]=q.get(p,0)+1
            m=lcs(S,S.build(rem,q))
            if best is None or m>best[0]: best=(m,p)
        pads[best[1]]=pads.get(best[1],0)+1
        cur=best[0]; hist.append((cur,hex(S.slot[best[1]]*8)))
        print('round',r+1,'lcs',cur,'at cand off',hex(S.slot[best[1]]*8),flush=True)
    f=S.build(rem,pads); print('final lcs',lcs(S,f),'difflib',dl(S,f),'slots',sum(len(t)//8 for t in f))
    json.dump({'pads':{hex(S.slot[k]*8):v for k,v in pads.items()}},open(OUT+'/res/padsim.json','w'))
