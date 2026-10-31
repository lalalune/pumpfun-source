#!/usr/bin/env python3
"""fbound.py <x.s|x.o|rxname>...: legal-frame bound. Align skeleton tokens (regs+frame+jumps masked) against the original,
vote candidate frame offset -> original offset over aligned r10 accesses (ld/st [r10+off] and mov rX,r10;add64 rX,imm leas),
take a greedy max-vote bijection, rewrite the candidate's offsets, report M (raw scorer tokens) after the remap = fR."""
import sys,os,difflib,json,struct
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import sc, oracle
def offs(t):
    """per token: frame offset key or None (and kind)"""
    r=[None]*len(t); lea={}
    for i,x in enumerate(t):
        op=x[0]; cl=op&7; d=x[1]&15; s=x[1]>>4
        off=struct.unpack_from('<h',x,2)[0]; imm=struct.unpack_from('<i',x,4)[0]
        if (cl==1 and s==10) or (cl in (2,3) and d==10): r[i]=('m',off)
        elif op==0xbf and s==10: lea[d]=i
        elif op==0x07 and d in lea and lea[d]==i-1: r[i]=('a',imm)
        if op!=0xbf and cl in (4,7) and d in lea and lea[d]!=i: lea.pop(d,None)
    return r
def setoff(x,kind,v):
    x=bytearray(x)
    if kind=='m': struct.pack_into('<h',x,2,v)
    else: struct.pack_into('<i',x,4,v)
    return bytes(x)
OT=sc.OT; OO=offs(OT)
def bound(p):
    c=sc.fn(p); ct=oracle.mask(c); co=offs(ct)
    sm=difflib.SequenceMatcher(None,sc.OS,sc.fmask(ct,True),autojunk=False); V={}
    for b in sm.get_matching_blocks():
        for k in range(b.size):
            a,q=OO[b.a+k],co[b.b+k]
            if a and q and a[0]==q[0]: V[(q[1],a[1])]=V.get((q[1],a[1]),0)+1
    mp={}; used=set()
    for (q,a),n in sorted(V.items(),key=lambda kv:-kv[1]):
        if q in mp or a in used: continue
        mp[q]=a; used.add(a)
    # unmapped candidate offsets keep their value unless it collides with a used orig offset: then leave (counts as miss anyway)
    nt=[setoff(x,co[i][0],mp[co[i][1]]) if co[i] and co[i][1] in mp else x for i,x in enumerate(ct)]
    M=sum(sc.hits(OT,nt)); M0=sum(sc.hits(OT,ct))
    rm=lambda t:[bytes([x[0],0])+x[2:] for x in t]
    RF=sum(sc.hits(rm(OT),rm(nt))); RJ=sum(sc.hits(sc.jmask(rm(OT)),sc.jmask(rm(nt))))
    return {'M':M0,'fR':M,'rfR':RF,'rfjR':RJ,'mapped':len(mp),'bytes':len(c)}
if __name__=='__main__':
    for p in sys.argv[1:]: print(os.path.basename(p) if '/' in p else p, json.dumps(bound(p)))
