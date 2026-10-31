#!/usr/bin/env python3
"""chill.py fn.bin... : colour-order hill-climb (experiment only). Permutes the offsets of 8-byte direct-access spill
colours (slots.py: only ldxdw/stxdw/stdw at exactly that offset, never address-taken, no overlapping access), which
is always a legal frame for the same colouring. Moves: swap a colour with one of its top-3 L1-vote targets, or with any
colour (--all). Accepts strict plain-ratio gains (rx metric). Prints start/end ratio and M = matched orig insns."""
import sys,os,struct,difflib,collections,types,json
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import slots
g={'__name__':'x'}; s_=open(T+'/rx.py').read(); exec(s_[:s_.index("OUT=os.environ.get")],g)
C=types.ModuleType('C'); _s=open(T+'/cls.py').read(); C.__dict__['__file__']=T+'/cls.py'; exec(_s[:_s.index('def main')],C.__dict__)
O=g['orig_window'](); OI=C.insns(O)
def r10off(t):
    op=t[0]; dst=t[1]&15; src=t[1]>>4
    if op in (0x79,0x61,0x69,0x71) and src==10: return -struct.unpack('<h',t[2:4])[0]
    if op in (0x7b,0x7a,0x63,0x62,0x6b,0x6a,0x73,0x72) and dst==10: return -struct.unpack('<h',t[2:4])[0]
    return None
def votes(c):
    CI=C.insns(c); sm=difflib.SequenceMatcher(None,[C.mask(t,1) for _,t in OI],[C.mask(t,1) for _,t in CI],autojunk=False)
    v=collections.defaultdict(collections.Counter)
    for a,b,n in sm.get_matching_blocks():
        for k in range(n):
            oo=r10off(OI[a+k][1]); co=r10off(CI[b+k][1])
            if oo is not None and co is not None: v[co][oo]+=1
    return v
def apply(c,perm):
    b=bytearray(c); i=0
    while i<len(b):
        op=b[i]; n=16 if op==0x18 else 8; t=bytes(b[i:i+8]); o=r10off(t)
        if o is not None and o in perm: b[i+2:i+4]=struct.pack('<h',-perm[o])
        i+=n
    return bytes(b)
def score(c): return g['metric'](c,O)[0]
def M(c,r): return r*(len(OI)+len(C.insns(c)))/2
def climb(c,ALL=False,maxit=60):
    S=slots.spill_slots(c); S=[s for s in S if s<0xff0]; Sset=set(S)
    perm={s:s for s in S}; cur=score(c); r0=cur; it=0
    while it<maxit:
        it+=1; cc=apply(c,perm); v=votes(cc)
        inv={v_:k for k,v_ in perm.items()}  # current offset -> original colour key
        cands=[]
        for s in S:
            if ALL: targets=[x for x in S if x!=s]
            else: targets=[o for o,_ in v.get(s,collections.Counter()).most_common(3) if o in Sset and o!=s]
            for t in targets: cands.append((s,t))
        best=(cur,None)
        for s,t in cands:
            p=dict(perm); a,b_=inv[s],inv[t]; p[a],p[b_]=t,s
            r=score(apply(c,p))
            if r>best[0]+1e-9: best=(r,p)
        if best[1] is None: break
        cur,perm=best
    out=apply(c,perm)
    return r0,cur,it,out,sum(1 for k in perm if perm[k]!=k)
if __name__=='__main__':
    ALL='--all' in sys.argv
    for f in [a for a in sys.argv[1:] if not a.startswith('--')]:
        c=open(f,'rb').read(); r0,r1,it,out,nm=climb(c,ALL)
        open(f+'.chill','wb').write(out)
        print(json.dumps({'f':f,'bytes':len(c),'ratio':round(r0,5),'chill':round(r1,5),'M0':round(M(c,r0)),'M1':round(M(c,r1)),'iters':it,'moved':nm}),flush=True)
