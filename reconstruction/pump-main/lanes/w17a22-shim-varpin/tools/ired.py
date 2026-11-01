#!/usr/bin/env python3
"""ired.py <base.s.ll> <edits.py> [names...]: apply named edit sets V[name] (lists of (old,new) single-occurrence
replacements or callables t->t) to a slim pre-opt module and score each with fx (experiment only).
Writes one JSON line per variant to $LANE_OUT/res/ired.jsonl. --keep keeps fx dirs (m.ll, fn.bin)."""
import sys,os,json,runpy
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import fx
DECL='declare void @llvm.var.annotation.p0.p0(ptr, ptr, ptr, i32, ptr)'
def apply(t,edits):
    for e in edits:
        if callable(e): t=e(t); continue
        x,y=e; c=t.count(x); assert c==1,(c,x[:160]); t=t.replace(x,y)
    if '@llvm.var.annotation.p0.p0(' in t and DECL not in t: t+='\n'+DECL+'\n'
    return t
if __name__=='__main__':
    a=sys.argv[1:]; keep='--keep' in a; a=[x for x in a if x!='--keep']
    base,ef=a[0],a[1]; g=runpy.run_path(ef); V=g['V']; names=a[2:] or list(V)
    t0=open(base).read(); out=os.path.join(fx.OUT,'res','ired.jsonl')
    for n in names:
        try: t=apply(t0,V[n])
        except AssertionError as e: r={'name':n,'err':'edit:'+str(e)[:200]}
        else:
            r=fx.run(t,n,keep=keep)
        r['set']=os.path.basename(ef); print(json.dumps(r),flush=True)
        with open(out,'a') as f: f.write(json.dumps(r)+'\n')
