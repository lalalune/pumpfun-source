#!/usr/bin/env python3
"""combo2.py <out.combo> <M0> <base_sig> <minpred> <K> <TOP> <edits.jsonl>:<singles.jsonl> ...
Size-neutral subsets (sum of single dB == 0) of size 2..K over the deduplicated singles with dM >= -4 and |dB| <= 64,
predicted dM (sum) >= minpred, no line conflicts; ranked by predicted dM then fewer cells. Writes combo lines and a merged
edit file <out.combo>.edits.jsonl. Experiment only."""
import sys,json,itertools
outc,M0,bsig,minpred,K,TOP=sys.argv[1:7]; M0=int(M0); minpred=int(minpred); K=int(K); TOP=int(TOP)
E={}; S={}
for a in sys.argv[7:]:
    ef,sf=a.split(':',1)
    for l in open(ef):
        e=json.loads(l); E[e['id']]=e
    for l in open(sf):
        r=json.loads(l)
        if 'M' in r and r['sig']!=bsig and '+' not in r['id']: S[r['id']]=r
seen={}; P=[]
for i,r in sorted(S.items(),key=lambda kv:-kv[1]['M']):
    if r['sig'] in seen: continue
    seen[r['sig']]=i
    if r['M']-M0>=-4 and abs(r['bytes']-27400)<=64: P.append(i)
dm={i:S[i]['M']-M0 for i in P}; db={i:S[i]['bytes']-27400 for i in P}
lines={i:set(int(k) for k in E[i]['rep']) for i in P}
out=[]
for k in range(2,K+1):
    for sub in itertools.combinations(P,k):
        if sum(db[i] for i in sub)!=0: continue
        p=sum(dm[i] for i in sub)
        if p<minpred: continue
        if all(db[i]==0 for i in sub) and k>2: continue
        L=set(); bad=False
        for i in sub:
            if L&lines[i]: bad=True; break
            L|=lines[i]
        if bad: continue
        out.append((p,k,sub))
out.sort(key=lambda x:(-x[0],x[1]))
open(outc,'w').write(''.join(' '.join(s)+'\n' for _,_,s in out[:TOP]))
with open(outc+'.edits.jsonl','w') as f:
    for e in E.values(): f.write(json.dumps(e)+'\n')
print(len(P),'pool',len(out),'subsets; top',out[:3])
