#!/usr/bin/env python3
"""rg.py <fn.bin|.so> [ref.bin] [--all]: per-region exact/full-mask matches via regap (no build), with deltas vs ref."""
import sys,os,re,json
os.environ.setdefault('PUMP_HARNESS','/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w19b13-cto-v1-holder-and1/reconstruction/harness')
sys.path.insert(0,os.path.expanduser('~/.cache/pumpfun-reconstruction/rea'))
import regap
from regap import *
def loadb(path):
    ws=[w for w in original_windows() if w['start']==W][0]
    def mk(raw):
        i=0; toks=[]
        while i<len(raw):
            n=16 if raw[i]==0x18 else 8
            t=bytearray(raw[i:i+n])
            if t[0]==0x85: t[1]&=0x0f; t[4:8]=b'\0'*4
            if t[0]==0x18: t[4:8]=b'\0'*4; t[12:16]=b'\0'*4
            toks.append(bytes(t)); i+=n
        return toks
    otoks=mk(ws['raw'])
    if path.endswith('.bin'):
        raw=open(path,'rb').read()
        return otoks,mk(raw),len(raw)
    from win import Cand,demangle
    c=Cand(path); s,n,nm=[(s,n,nm) for s,n,nm in c.funcs if re.search(r'admin_cto.*execute',demangle(nm))][0]
    return otoks,mk(bytes(c.fn(s,n))),n
def tab(path):
    otoks,ctoks,n=loadb(path)
    # check masks of orig the same way
    oo=offs(otoks); r={}
    glob={}
    for name,m in MASKS:
        A,B=abstract(otoks,m),abstract(ctoks,m); sm=sm_of(A,B); mt=[0]*len(otoks)
        for b in sm.get_matching_blocks():
            for k in range(b.size): mt[b.a+k]=1
        glob[name]=sum(mt)
        for rid,lo,hi,_ in REGIONS:
            r.setdefault(rid,{})[name]=sum(mt[k] for k in range(len(otoks)) if lo<=oo[k]<hi)
    return glob,r,n
if __name__=='__main__':
    a=[x for x in sys.argv[1:] if not x.startswith('--')]
    g,r,n=tab(a[0]); gr,rr=None,None
    if len(a)>1: gr,rr,_=tab(a[1])
    print(f'{a[0].split("/")[-2] if "/" in a[0] else a[0]} {n}B exact {g["exact"]} jump {g["jump"]} frame {g["frame"]} reg {g["reg"]} all3 {g["all3"]}'+(f'  (vs ref: exact {g["exact"]-gr["exact"]:+d} jump {g["jump"]-gr["jump"]:+d} frame {g["frame"]-gr["frame"]:+d} reg {g["reg"]-gr["reg"]:+d} all3 {g["all3"]-gr["all3"]:+d})' if gr else ''))
    rows=[]
    for rid in [x[0] for x in REGIONS]:
        v=r[rid]
        if rr:
            w=rr[rid]
            de,da=v['exact']-w['exact'],v['all3']-w['all3']
            rows.append(f'{rid}:{de:+d}/{da:+d}' if (de or da or '--all' in sys.argv) else None)
        else:
            rows.append(f'{rid}:{v["exact"]}/{v["all3"]}')
    print(' '.join(x for x in rows if x))
    if '--mask' in sys.argv:
        for nm in ('frame','reg','jump','all3'):
            print(nm.ljust(6),' '.join(f'{rid}:{r[rid][nm]-rr[rid][nm]:+d}' for rid in [x[0] for x in REGIONS] if rr and r[rid][nm]!=rr[rid][nm]))
