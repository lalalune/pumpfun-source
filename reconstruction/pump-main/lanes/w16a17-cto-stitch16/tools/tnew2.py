#!/usr/bin/env python3
"""tnew2.py <base unstripped.so> <tag>: translate every cached capture (5998913 basis) onto a new base function with the
splice oracle; price ratio + positional slots (oracle.metric); report captures/pairs that beat or tie-with-fewer-slots."""
import sys,os,json,itertools
sys.path.insert(0,'tools'); import splice, oracle
so=sys.argv[1]; tag=sys.argv[2]
OLD=open('rx/main/fn.bin','rb').read(); NEW=oracle.elf_fn(so,oracle.KEEP)
orig=oracle.orig_window()
OB=splice.parse(OLD); OBT=splice.targets(OB); NV=splice.Var(OB,NEW)
r0,s0=oracle.metric(NEW,orig); print('base',len(NEW),r0,s0,'M',splice.M(NEW),flush=True)
R=json.load(open('data/cat16_r4.json'))
rows=[r for r in R if r.get('tpath') and not r.get('nonsrc') and not r.get('tmh') and not r.get('excluded') and r.get('tM') and r['tM']>=2230 and abs(r['tbytes']-27400)<=64]
for n in ['g1','crl3','C3b','crl3t1n','g1t1n','G1d','G1i','t1n','I6n','hkl3','lfb5','ntA','ntB','q5','hkcopy','S1','S2','a1','shif','cuunw','wlwe','colnat','gwclk','csF','L1','C3a','rS3','rS4']:
    p=f'rx/{n}/fn.bin'
    if os.path.exists(p): rows.append({'lane':'w16a17(own)','name':n,'tpath':p})
out=[]; seen=set()
for r in rows:
    raw=open(r['tpath'],'rb').read()
    if raw in seen: continue
    seen.add(raw)
    s=splice.splice(OLD,[NV,raw],OB,OBT)
    if s is None: continue
    rr,sd=oracle.metric(s,orig)
    out.append({'lane':r['lane'],'name':r['name'],'tpath':r['tpath'],'bytes':len(s),'M':splice.M(s),'ratio':rr,'slots':sd})
out.sort(key=lambda x:(abs(x['bytes']-27400),-x['ratio'],x['slots'] if x['slots'] is not None else 10**9))
json.dump(out,open(f'w17/tnew2_{tag}.json','w'),indent=0)
print('translated',len(out))
for x in [x for x in out if x['bytes']==27400][:15]: print(f"{x['lane'][:22]:22s} {x['name'][:28]:28s} {x['M']} {x['ratio']:.5f} slots {x['slots']}")
# pairs of 0 B items with ratio >= base
z=[x for x in out if x['bytes']==27400 and x['ratio']>=r0-1e-9]
print('0B ties/gains',len(z))
best=[]
for a,b in itertools.combinations(z,2):
    s=splice.splice(OLD,[NV,open(a['tpath'],'rb').read(),open(b['tpath'],'rb').read()],OB,OBT)
    if s is None or len(s)!=27400: continue
    rr,sd=oracle.metric(s,orig); best.append((-rr,sd,a['name'],b['name']))
best.sort(); print('pairs',len(best)); [print(x) for x in best[:12]]
