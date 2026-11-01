#!/usr/bin/env python3
"""irs.py <base.s.ll> <specfile.py> [names...]: apply IR edit specs (V dict: name -> list of (old,new[,count])) to execute's body, score with fx, print region deltas"""
import sys,os,runpy,json,difflib,re
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
os.environ.setdefault('LANE_OUT',os.path.dirname(T))
import fx,oracle
OUT=os.path.dirname(T)
R=[('E1',0x0),('E2',0x280),('E3',0x420),('V1',0x708),('V2',0xb00),('V3',0xe60),('V4',0x1258),('V5',0x1490),('J1',0x1800),('J2',0x1990),('W1',0x1c88),('S1',0x1f68),('T1',0x26e8),('C1',0x3c50),('P1',0x4aa8),('EV',0x4e50),('TL',0x5558),('S2',0x5a18),('W2',0x5c18),('END',0x6b08)]
def split(raw):
    i=0;o=[]
    while i<len(raw):
        n=16 if raw[i]==0x18 else 8; o.append(i); i+=n
    return o
ow=oracle.orig_window(); ot=oracle.mask(ow); oo=split(ow)
def regs(raw):
    ct=oracle.mask(raw); sm=difflib.SequenceMatcher(None,ot,ct,autojunk=False)
    cnt={r[0]:0 for r in R}
    for b in sm.get_matching_blocks():
        for k in range(b.a,b.a+b.size):
            off=oo[k]
            for i in range(len(R)-1):
                if R[i][1]<=off<R[i+1][1]: cnt[R[i][0]]+=1; break
    return cnt
def body_span(t):
    m=re.search(r'^define[^\n]*admin_cto7execute17h[^\n]*\n',t,re.M); s=m.start(); e=t.index('\n}\n',s)
    return s,e
base=sys.argv[1]; spec=runpy.run_path(sys.argv[2]); V=spec['V']; names=sys.argv[3:] or list(V)
t0=open(base).read(); s,e=body_span(t0)
bn=os.path.basename(base).replace('.s.ll','')
bfn=f'{OUT}/fx/{bn}/fn.bin'
if not os.path.exists(bfn): fx.run(t0,bn,keep=False)
bc=regs(open(bfn,'rb').read())
for n in names:
    body=t0[s:e]; ok=True
    for ed in V[n]:
        old,new=ed[0],ed[1]; cnt=ed[2] if len(ed)>2 else 1
        c=body.count(old)
        if c!=cnt and cnt!=-1: print(json.dumps({'name':n,'err':f'count {c} for {old[:80]}'})); ok=False; break
        body=body.replace(old,new)
    if not ok: continue
    extra=spec.get('DECL','')
    t=t0[:s]+body+t0[e:]
    if extra and extra not in t: t=t+'\n'+extra+'\n'
    r=fx.run(t,n)
    if 'err' in r: print(json.dumps(r)); continue
    c=regs(open(f'{OUT}/fx/{n}/fn.bin','rb').read())
    d={k:c[k]-bc[k] for k in c if c[k]!=bc[k]}
    print(json.dumps({'name':n,'M':r['M'],'bytes':r['bytes'],'ratio':r['ratio'],'d':d}),flush=True)
