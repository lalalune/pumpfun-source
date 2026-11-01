#!/usr/bin/env python3
"""onbase.py <base.ll> <out.combo> <base_ids,comma> <M0> <dbmin> <dbmax> <dmmin> <edits.jsonl>:<singles.jsonl> ...
Write combo lines 'base_ids x' for every screened single x (deduplicated by signature, first id kept) whose single
dB lies in [dbmin,dbmax] and whose single dM >= dmmin, with no line conflict against the base cells. Then run
screen.py --combo on them with the merged edit file. Experiment only."""
import sys,json,os
base,outc,bids,M0,dbmin,dbmax,dmmin=sys.argv[1:8]; M0=int(M0); dbmin=int(dbmin); dbmax=int(dbmax); dmmin=int(dmmin)
pairs=[a.split(':',1) for a in sys.argv[8:]]
E={}; S={}
for ef,sf in pairs:
    for l in open(ef):
        e=json.loads(l); E[e['id']]=e
    for l in open(sf):
        r=json.loads(l)
        if 'M' in r: S[r['id']]=r
B=bids.split(',')
bl=set()
for b in B: bl|=set(int(k) for k in E[b]['rep'])
seen=set(); out=[]
for i,r in sorted(S.items(),key=lambda kv:-kv[1]['M']):
    if i in B or r['sig'] in seen: continue
    seen.add(r['sig'])
    db=r['bytes']-27400; dm=r['M']-M0
    if not (dbmin<=db<=dbmax and dm>=dmmin): continue
    if set(int(k) for k in E[i]['rep'])&bl: continue
    out.append(' '.join(B+[i]))
open(outc,'w').write('\n'.join(out)+'\n')
mf=outc+'.edits.jsonl'
with open(mf,'w') as f:
    for e in E.values(): f.write(json.dumps(e)+'\n')
print(len(out),'combos ->',outc,'edits ->',mf)
