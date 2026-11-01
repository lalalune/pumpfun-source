#!/usr/bin/env python3
"""iru.py <name> <mode> : IR-order realisation of B units on rx/<name>/mi.ll with real llc.
Each unit's IR blocks are moved (in IR) right after the IR block of its B-layout predecessor. mode: singles | sets:<k.k.k>|... | greedy"""
import sys,os,json,re; T=os.path.dirname(os.path.abspath(__file__)); O=os.path.dirname(T); sys.path.insert(0,T)
import sub, relayn, irord, sc, eseq, irB, uo
R=relayn.R
def setup(n,specf='Bspec_O.txt'):
    d=irB.prep(n); irB.prep('main')
    spec=open(f'{O}/tmp/{specf}').read().strip().split(',')
    rs=sub.resolve_content(f'{O}/rx/main/mi.s',d+'/mi.s',spec); m=irB.irnames(d+'/mi.s')
    asm2ir={}
    for x,a in zip(spec,rs):
        if a and a in m: asm2ir[x]=irord.short(m[a])
    # B layout order (asm) -> predecessor names in spec space
    pB=[x for x in spec if x in asm2ir]
    units=[[asm2ir[x] for x in u if x in asm2ir] for u in uo.U]
    unitspec=[[x for x in u if x in asm2ir] for u in uo.U]
    return d,spec,asm2ir,units,unitspec
def predir(spec,asm2ir,unitspec,k,d):
    # IR name of the asm block that precedes unit k's first block in the B layout (from relayout of mi.s)
    names,Bn,miss=sub.border2(f'{O}/rx/main/mi.s',d+'/mi.s',spec)
    m=irB.irnames(d+'/mi.s'); rs=sub.resolve_content(f'{O}/rx/main/mi.s',d+'/mi.s',spec); mp={a:b for a,b in zip(spec,rs) if b}
    a=mp[unitspec[k][0]]; i=Bn.index(a); pa=Bn[i-1]
    # walk back to a block with an IR name
    while pa not in m: i-=1; pa=Bn[i-1]
    return irord.short(m[pa])
def mvspec(n,S,specf='Bspec_O.txt'):
    d,spec,asm2ir,units,unitspec=setup(n,specf); mv=[]
    for k in sorted(S):
        if not units[k]: continue
        p=predir(spec,asm2ir,unitspec,k,d)
        for x in units[k]:
            mv.append(f'{x}@{p}'); p=x
    return d,'mv:'+';'.join(mv)
def run(n,S,tag):
    d,sp=mvspec(n,S); os.makedirs(O+'/t',exist_ok=True); outp=f'{O}/t/{n}_{tag}'
    r=irord.run(d+'/mi.ll',outp,sp); r.pop('ch',None)
    if 'err' not in r: r['eseq']=' '.join(map(str,eseq.seq(sc.fn(outp+'.s'))[:10]))
    r['mv']=sp; return r
if __name__=='__main__':
    n=sys.argv[1]; mode=sys.argv[2]
    if mode=='singles':
        for k in range(len(uo.U)):
            r=run(n,{k},f'u{k}'); print(k,uo.U[k],json.dumps({x:r.get(x) for x in ('M','bytes','jM','fM','eseq','err')}),flush=True)
    elif mode.startswith('sets:'):
        for s in mode[5:].split('|'):
            S={int(x) for x in s.split('.') if x}; r=run(n,S,'s'+s.replace('.','_')); print(s,json.dumps(r),flush=True)
