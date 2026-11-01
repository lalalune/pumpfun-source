#!/usr/bin/env python3
"""tnew3.py <tag>: translate every cached w16a17 capture (5998913 basis) onto the current baseline function with the splice oracle"""
import sys,os,json,itertools
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import splice, oracle
S=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w16a17-cto-stitch16')
tag=sys.argv[1]
so=os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so')
OLD=open(S+'/rx/main/fn.bin','rb').read(); NEW=oracle.elf_fn(so,oracle.KEEP)
orig=oracle.orig_window()
OB=splice.parse(OLD); OBT=splice.targets(OB); NV=splice.Var(OB,NEW)
print('main diff hunks',len(NV.hunks),'tokens changed',sum(max(i2-i1,j2-j1) for i1,i2,j1,j2 in NV.hunks))
r0,s0=oracle.metric(NEW,orig); print('base',len(NEW),r0,s0,'M',splice.M(NEW),flush=True)
R=json.load(open(S+'/data/cat16_r4.json'))
rows=[r for r in R if r.get('tpath') and not r.get('nonsrc') and not r.get('tmh') and not r.get('excluded') and r.get('tM') and r['tM']>=2220 and abs(r['tbytes']-27400)<=160]
for n in os.listdir(S+'/rx'):
    p=f'{S}/rx/{n}/fn.bin'
    if os.path.exists(p): rows.append({'lane':'w16a17(own)','name':n,'tpath':p})
out=[]; seen=set(); nconf=0
for r in rows:
    p=r['tpath'] if r['tpath'].startswith('/') else S+'/'+r['tpath']
    if not os.path.exists(p): continue
    raw=open(p,'rb').read()
    if raw in seen: continue
    seen.add(raw)
    s=splice.splice(OLD,[NV,raw],OB,OBT)
    if s is None: nconf+=1; continue
    rr,sd=oracle.metric(s,orig)
    out.append({'lane':r['lane'],'name':r['name'],'tpath':p,'bytes':len(s),'M':splice.M(s),'ratio':rr,'slots':sd})
out.sort(key=lambda x:(abs(x['bytes']-27400),-x['M'],x['slots'] if x['slots'] is not None else 10**9))
json.dump(out,open(f'{os.path.dirname(T)}/data/tnew3_{tag}.json','w'),indent=0)
print('rows',len(rows),'unique',len(seen),'conflicts',nconf,'translated',len(out))
for x in out[:40]: print(f"{x['lane'][:22]:22s} {x['name'][:34]:34s} {x['bytes']} {x['M']} {x['ratio']:.5f} slots {x['slots']}")
