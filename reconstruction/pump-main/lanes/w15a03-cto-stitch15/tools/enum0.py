#!/usr/bin/env python3
"""enum0.py <res.jsonl>... [--main 2248] [--k 3] [--top 40]: additive-model enumeration of gene sets whose byte deltas sum to 0
(single-gene rows only, deduped by gene; byte-identical-to-main genes dropped). Prints predicted dM for every 0 B pair/triple
(genes must not share an edit site: names are checked pairwise for apply conflicts by the caller)."""
import sys,json,itertools
a=sys.argv[1:]; MM=2248; K=3; TOP=40
for k in ('--main','--k','--top'):
    if k in a: i=a.index(k); v=int(a[i+1]); del a[i:i+2]; globals()[{'--main':'MM','--k':'K','--top':'TOP'}[k]]=v
S={}
for f in a:
    for l in open(f):
        r=json.loads(l)
        if 'error' in r or '+' in r['genes'] or r['genes']=='-' or r.get('eq_main'): continue
        S[r['genes']]=(r['bytes']-27400,r['M']-MM)
G=[(g,b,m) for g,(b,m) in S.items() if m>=-12]
out=[]
for k in range(1,K+1):
    for c in itertools.combinations(G,k):
        if sum(x[1] for x in c)==0: out.append((sum(x[2] for x in c),'+'.join(x[0] for x in c)))
out.sort(reverse=True)
for o in out[:TOP]: print(o)
print(len(G),'genes',len(out),'zero-byte sets')
