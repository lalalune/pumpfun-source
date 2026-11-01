#!/usr/bin/env python3
"""binrestore.py <in fn.bin> <out fn.bin> [W=64] [k=6]: binary-level layout-restore oracle toward the ORIGINAL's order
(experiment only). Generalises w16-strategy placenorm.py so that the result is a real, re-linked instruction stream:
anchor variant instructions to the original by unique rfj k-grams, smooth the anchor shift, cut segments where it moves
by more than W instructions (cuts snapped to a nearby ja/exit), sort segments by median original anchor, then re-link
every jump (16-bit slot offsets) and add a `ja` where a moved segment loses its fall-through. Prints one JSON line."""
import sys,os,struct,bisect,json
from collections import defaultdict
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
_args=sys.argv[1:]; sys.argv=sys.argv[:1]
exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/w16-strategy/ceilings/collapse.py').read().split("O = toks(ws['raw'])")[0])
O=toks(ws['raw']); OA=[ab(t,'rfj') for t in O]
JC={0x05,0x15,0x1d,0x25,0x2d,0x35,0x3d,0x45,0x4d,0x55,0x5d,0x65,0x6d,0x75,0x7d,0xa5,0xad,0xb5,0xbd,0xc5,0xcd,0xd5,0xdd,
    0x16,0x1e,0x26,0x2e,0x36,0x3e,0x46,0x4e,0x56,0x5e,0x66,0x6e,0x76,0x7e,0xa6,0xae,0xb6,0xbe,0xc6,0xce,0xd6,0xde}
def restore(raw,W=64,k=6,snap=12):
    C=toks(raw); n=len(C); CA=[ab(t,'rfj') for t in C]
    oidx=defaultdict(list)
    for i in range(len(OA)-k+1): oidx[tuple(OA[i:i+k])].append(i)
    anchor=[None]*n
    for j in range(n-k+1):
        hs=oidx.get(tuple(CA[j:j+k]),[])
        if len(hs)==1:
            for q in range(k):
                if anchor[j+q] is None: anchor[j+q]=hs[0]+q
    anc=[(j,anchor[j]-j) for j in range(n) if anchor[j] is not None]; pos=[a for a,_ in anc]; sm=[]
    for j in range(n):
        lo=bisect.bisect_left(pos,j-20); hi=bisect.bisect_right(pos,j+20); w=sorted(d for _,d in anc[lo:hi])
        sm.append(w[len(w)//2] if w else (sm[-1] if sm else 0))
    cuts=[0]
    for j in range(1,n):
        if abs(sm[j]-sm[cuts[-1]])>W:
            # snap the cut to just after a ja/exit within +-snap
            best=None
            for d in range(0,snap+1):
                for c in (j-d,j+d):
                    if cuts[-1]<c<n and C[c-1][0] in (0x05,0x95): best=c; break
                if best: break
            c=best or j
            if c>cuts[-1]: cuts.append(c)
    cuts.append(n); segs=[list(range(cuts[i],cuts[i+1])) for i in range(len(cuts)-1) if cuts[i]<cuts[i+1]]
    def key(sg):
        a=sorted(anchor[j] for j in sg if anchor[j] is not None); return a[len(a)//2] if a else None
    ks=[]; prev=-1
    for sg in segs:
        x=key(sg); x=prev+0.001 if x is None else x; ks.append(x); prev=x
    order=sorted(range(len(segs)),key=lambda i:(ks[i],i))
    if order[0]!=0: order.remove(0); order.insert(0,0)
    # old slot addresses
    slot=[0]*(n+1)
    for j in range(n): slot[j+1]=slot[j]+len(C[j])//8
    s2i={slot[j]:j for j in range(n)}; s2i[slot[n]]=n
    # build new stream of (old index or ('ja',target old index))
    seq=[]
    for p,si in enumerate(order):
        sg=segs[si]; seq+= [('i',j) for j in sg]
        last=sg[-1]; nxt=last+1
        follows=(p+1<len(order) and segs[order[p+1]][0]==nxt)
        if nxt<n and not follows and C[last][0] not in (0x05,0x95): seq.append(('ja',nxt))
    # new slots
    nslot={}; addr=0; newpos=[]
    for e in seq:
        newpos.append(addr)
        if e[0]=='i': nslot[e[1]]=addr; addr+=len(C[e[1]])//8
        else: addr+=1
    nslot[n]=addr
    out=bytearray(); bad=0
    for e,a in zip(seq,newpos):
        if e[0]=='ja':
            off=nslot[e[1]]-(a+1); out+=struct.pack('<BBhi',0x05,0,off,0); continue
        j=e[1]; t=bytearray(C[j])
        if t[0] in JC:
            o=struct.unpack_from('<h',t,2)[0]; tgt=slot[j]+1+o
            if tgt in s2i:
                no=nslot[s2i[tgt]]-(a+1)
                if -32768<=no<=32767: struct.pack_into('<h',t,2,no)
                else: bad+=1
            else: bad+=1
        out+=t
    moved=sum(1 for p,si in enumerate(order) if p!=si)
    return bytes(out),{'segs':len(segs),'moved_segs':moved,'ja_added':sum(1 for e in seq if e[0]=='ja'),'bad':bad}
if __name__=='__main__':
    a=_args; raw=open(a[0],'rb').read(); W=int(a[2]) if len(a)>2 else 64; k=int(a[3]) if len(a)>3 else 6
    b,info=restore(raw,W,k); open(a[1],'wb').write(b); info.update({'in':a[0],'bytes_in':len(raw),'bytes_out':len(b)}); print(json.dumps(info))
