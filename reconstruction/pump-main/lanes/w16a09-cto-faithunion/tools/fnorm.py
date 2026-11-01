#!/usr/bin/env python3
"""fnorm.py <fn.bin> <var pei.mir> <ref pei.mir> [--out f.bin] [--noperm]: frame-normalisation oracle (experiment only).
Generalises w15a19 shperm.py (one band shift) to any alloca layout change: every r10 access, and every `mov rX,r10;
add rX,imm` lea, that falls inside a variant non-spill frame object is rebased to the reference object of the same IR
name (unnamed objects are paired in offset order within each size). Variant objects with no reference partner keep their
offset. Then the variant's own spill slots take the best colour permutation plus the vote swap climb (relab.bestperm), as
Mperm/Mhc do. Prints one JSON line: M (input), Mfn (allocas rebased), Mfnperm, Mfnhc, nmatched, nextra."""
import sys,os,re,struct,json
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import relab as R
def objs(p):
    t=open(p).read(); st=t[t.index('\nstack:'):]; st=st[:st.index('\ncallSites:')] if '\ncallSites:' in st else st[:80000]
    out=[]
    for blk in re.split(r'\n  - \{ ',st)[1:]:
        d=dict(re.findall(r"(\w[\w-]*): ('[^']*'|[^,}]+)",blk))
        out.append((int(d.get('offset','0')),int(d.get('size','0')),d.get('type',''),d.get('name','').strip("'")))
    return out
def pairing(vo,ro):
    V=[x for x in vo if x[2]!='spill-slot']; Rr=[x for x in ro if x[2]!='spill-slot']
    from collections import Counter,defaultdict
    cv=Counter(x[3] for x in V if x[3]); cr=Counter(x[3] for x in Rr if x[3])
    rn={x[3]:x for x in Rr if x[3] and cr[x[3]]==1}
    mp=[]; used=set(); extra=[]
    for x in V:
        if x[3] and cv[x[3]]==1 and x[3] in rn: mp.append((x,rn[x[3]])); used.add(rn[x[3]])
    # unnamed (or ambiguous) objects: pair in offset order per size
    lv=defaultdict(list); lr=defaultdict(list)
    for x in sorted(V,reverse=True):
        if not any(x is a for a,_ in mp): lv[x[1]].append(x)
    for x in sorted(Rr,reverse=True):
        if x not in used: lr[x[1]].append(x)
    for sz,xs in lv.items():
        ys=lr.get(sz,[])
        for k,x in enumerate(xs):
            if k<len(ys): mp.append((x,ys[k]))
            else: extra.append(x)
    return mp,extra
def rebase(b,mp,sp):
    def f(o):
        if o in sp: return o
        for (vo,vs,_,_),(ro,_,_,_) in mp:
            if vo<=o<vo+vs: return ro+(o-vo)
        return o
    c=bytearray(b); lea={}
    for i,k in R.ins(b):
        op=b[i]; dst=b[i+1]&15; src=b[i+1]>>4
        if op==0xbf and src==10: lea[dst]=i; continue
        if op==0x07 and dst in lea and lea[dst]==i-8:
            v=struct.unpack_from('<i',b,i+4)[0]; struct.pack_into('<i',c,i+4,f(v)); lea.pop(dst,None); continue
        o=R.memoff(b,i)
        if o is not None: struct.pack_into('<h',c,i+2,f(o))
        lea.pop(dst,None)
    return bytes(c)
def main():
    a=sys.argv[1:]; fb,vp,rp=a[0],a[1],a[2]; out=a[a.index('--out')+1] if '--out' in a else None
    b=open(fb,'rb').read(); vo=objs(vp); ro=objs(rp); sp={x[0] for x in vo if x[2]=='spill-slot'}
    mp,extra=pairing(vo,ro); c=rebase(b,mp,sp)
    res={'f':fb,'bytes':len(b),'M':R.M(b),'Mfn':R.M(c),'nmatched':len(mp),'nextra':len(extra),
         'nmoved':sum(1 for x,y in mp if x[0]!=y[0]),'extra':[x[3] or str(x[1]) for x in extra][:12]}
    if '--noperm' not in a:
        mpm,pm=R.bestperm(c,sp,3); cur=dict(pm); best=mpm
        for rnd in range(2):
            bb=R.apply(c,cur); V=R.votes(bb,set(cur.values())); inv={v:k for k,v in cur.items()}; cand=set(); imp=0
            for y,dd in V.items():
                for x in dd:
                    if x in inv and x!=y: cand.add(tuple(sorted((y,x))))
            for y,x in sorted(cand):
                p,q=inv[y],inv[x]; t=dict(cur); t[p],t[q]=cur[q],cur[p]; m=R.M(R.apply(c,t))
                if m>best: best=m; cur=t; inv={v:k for k,v in cur.items()}; imp+=1
            if not imp: break
        res.update({'Mfnperm':mpm,'Mfnhc':best,'ratio_fnhc':R.ratio(R.apply(c,cur))})
        if out: open(out,'wb').write(R.apply(c,cur))
    elif out: open(out,'wb').write(c)
    print(json.dumps(res),flush=True)
main()
