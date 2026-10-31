#!/usr/bin/env python3
"""sub.py: subsets of B on a capture. order(path,spec)->names after B; emit full order with/without polarity flips.
Variant: keep blocks of set FIX at their main slots; other span blocks follow the B order."""
import sys,os,json,re
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import relayn, sc
R=relayn.R
HEAD=['bb10.i','bb3.i29.i','bb14.i','bb16.i','bb22.i','bb17.i','bb3.i22.i','exit23.i']
FLIPS=['bb7.i','bb14.i','bb16.i','bb23.i']
def resolve(path,spec_names):
    m=relayn.irmap(path); used=set(); out=[]; sp=','.join(spec_names)
    for x in spec_names:
        if x in m: out.append(m[x])
        else:
            y=relayn.alias(x,m,sp,used)
            if y: out.append(m[y]); used.add(y)
            else: out.append(None)
    return out
def border(path,specn):
    pre,blocks,post=R.parse(path); eb=R.explicit(blocks); names=[x[0] for x in eb]
    listed=[x for x in resolve(path,specn) if x]
    idx=[names.index(x) for x in listed]; lo,hi=min(idx),max(idx)
    span=names[lo:hi+1]; rest=[x for x in span if x not in listed]
    new=names[:lo]+listed+rest+names[hi+1:]
    return names,new,pre,eb,post
def emit(path,order,rev,allowflip=None):
    pre,blocks,post=R.parse(path); eb=R.explicit(blocks); m={x[0]:x for x in eb}
    eb2=[m[x] for x in order]
    if not rev: return R.emit(pre,eb2,post),0
    if allowflip is None:
        t=relayn.emit_rev(pre,eb2,post); return t,relayn.emit_rev.flips
    # selective flips: only blocks in allowflip (asm names) may flip; others get ja
    body=[]; fl=0
    for k,(nm,b,ft) in enumerate(eb2):
        b=list(b); nxt=eb2[k+1][0] if k+1<len(eb2) else None; ii=R.insns(b)
        if ft is not None and ft!=nxt:
            last=b[ii[-1]].strip() if ii else ''; op=last.split()[0] if last else ''
            if nm in allowflip and op in relayn.INV and nxt and last.endswith(', '+R.lab(nxt)):
                b[ii[-1]]='\t'+relayn.INV[op]+last[len(op):-len(R.lab(nxt))]+R.lab(ft); fl+=1
            else: b.append('\tja %s'%R.lab(ft))
        elif ft is None and ii:
            lastl=b[ii[-1]].strip()
            if nxt and lastl=='ja '+R.lab(nxt): del b[ii[-1]]
        body+=b
    return '\n'.join(pre+body+post),fl
def fixmix(main,new,fix):
    """blocks in fix keep main slot; others take new's relative order"""
    others=[x for x in new if x not in fix]; it=iter(others); out=[]
    for x in main: out.append(x if x in fix else next(it))
    return out
def score(t,o):
    open(o,'w').write(t); s=sc.score(o); s.pop('ch',None); return s
def sig(body):
    out=[]
    for j in R.insns(body):
        x=body[j].strip(); x=re.sub(r'LBB[X0]_\w+','L',x); out.append(x)
    return tuple(out)
def resolve_content(pm,pv,spec_names):
    """map main-spec block names to variant asm block names by instruction content; fallback by IR name."""
    am=resolve(pm,spec_names)
    _,blm,_=R.parse(pm); _,blv,_=R.parse(pv)
    sm={n:sig(b) for n,b in blm}; posm={n:i for i,(n,b) in enumerate(blm)}
    byv={}
    for i,(n,b) in enumerate(blv): byv.setdefault(sig(b),[]).append((i,n))
    vn=resolve(pv,spec_names); out=[]; used=set()
    for x,a,v in zip(spec_names,am,vn):
        c=[(abs(i-posm[a]),n) for i,n in byv.get(sm[a],[]) if n not in used] if a else []
        if c: c.sort(); out.append(c[0][1]); used.add(c[0][1])
        elif v and v not in used: out.append(v); used.add(v)
        else: out.append(None)
    return out
def border2(pm,pv,specn):
    pre,blocks,post=R.parse(pv); eb=R.explicit(blocks); names=[x[0] for x in eb]
    rs=resolve_content(pm,pv,specn); listed=[x for x in rs if x]
    idx=[names.index(x) for x in listed]; lo,hi=min(idx),max(idx)
    span=names[lo:hi+1]; rest=[x for x in span if x not in listed]
    return names,names[:lo]+listed+rest+names[hi+1:],[s for s,r in zip(specn,rs) if r is None]
