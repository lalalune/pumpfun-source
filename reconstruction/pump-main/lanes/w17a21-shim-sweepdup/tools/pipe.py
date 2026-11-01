#!/usr/bin/env python3
"""pipe.py: pre-opt slim edit -> opt -O3 -> slim -> optional post-opt transforms -> llc -> score (experiment only)."""
import sys,os,subprocess,json
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle,lx,dup2
OUT=os.path.dirname(T)
OPT=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/rust/lib/rustlib/aarch64-apple-darwin/bin/opt')
def apply(t,edits):
    for e in edits:
        if callable(e): t=e(t); continue
        a,b=e; c=t.count(a); assert c==1,(c,a[:120]); t=t.replace(a,b)
    return t
def opt(pre,name):
    d=os.path.join(OUT,'pp',name); os.makedirs(d,exist_ok=True)
    open(d+'/in.ll','w').write(pre)
    r=subprocess.run(['nice','-n','5',OPT,'-O3',d+'/in.ll','-S','-o',d+'/o3.ll'],capture_output=True,text=True)
    if r.returncode: raise SystemExit('opt:'+r.stderr[-500:])
    m=oracle.slim(open(d+'/o3.ll').read()); os.remove(d+'/in.ll'); os.remove(d+'/o3.ll')
    open(d+'/m.ll','w').write(m); return m
def N2(t):
    dup2.setnames(t); t=dup2.dup(t,dup2.S648,ne=True,place='end'); return dup2.dup(t,dup2.S660,ne=True,place='end')
def run(name,pre_edits=(),post=(),base=OUT+'/fx/m1/in.ll',llc='sdk'):
    t=apply(open(base).read(),pre_edits)
    m=opt(t,name)
    res={}
    r=lx.run(OUT+'/pp/%s/m.ll'%name,name+'.0',llc); res['plain']={k:r.get(k) for k in ('M','bytes','err')}
    for pn,pf in post:
        m2=pf(m); p=OUT+'/pp/%s/%s.ll'%(name,pn); open(p,'w').write(m2)
        r=lx.run(p,name+'.'+pn,llc); res[pn]={k:r.get(k) for k in ('M','bytes','err')}
    return res
import j60 as _j60
def MV(t,blk,before):
    def f(B,order):
        order.remove(blk); order.insert(order.index(before),blk); return B,order
    return dup2.edit_fn(t,f)
def O3(t):
    dup2.setnames(t); J57=dup2.J57; J60=dup2.J60
    return MV(_j60.j60(t),J57,J60)
