#!/usr/bin/env python3
"""table.py: markdown joint-ceiling matrix from data/joint.jsonl (+ main's w15a28 reference rows). Experiment only."""
import json,os,sys
O=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENES={'m0':'main','L':'L = mv_5_1+t1n+m_crl2+devol','L_tai2':'L + s_tai2','Lc2':'L + c2','Ls1':'L + s1','Lsh':'L + sh_iflet+rP_back',
       'Ltf':'L + tf_g1a','Ln1':'L + n1','Lpo':'L + po','Ln1po':'L + n1 + po','Ltpo':'L_tai2 + po','Mc2':'main + c2','Ltc2':'L_tai2 + c2'}
rows=[json.loads(l) for l in open(O+'/data/joint.jsonl')]
best={}
for r in rows: best[(r['rx'],r['pass'])]=r
ref=[{'rx':'m0','pass':'p1','bytes':27400,'M':2249,'Mperm':2293,'Mhc':2300,'climb_ratio':0.68245,'climb_bytes':27376,'nforces':7,'fM':2277,'fMperm':2321,'joint':2328,'rot':0,'frot':0,'fLCS':28,'fLCSrfj':3,'src':'w15a28 #3746'},
     {'rx':'m0','pass':'p2','bytes':27400,'M':2249,'Mperm':2293,'Mhc':2300,'climb_ratio':0.68395,'climb_bytes':27376,'nforces':9,'fM':2282,'fMperm':2338,'joint':2338,'rot':0,'frot':0,'fLCS':35,'fLCSrfj':2,'src':'w15a28 #3746'}]
allr=ref+sorted(best.values(),key=lambda r:-(r.get('joint') or 0))
print('| composite | pass | bytes | M | Mperm | Mhc | forces | climb ratio @ bytes | forced M | forced Mperm | joint | d joint vs main p2 | true LCS ---/rfj vs main | window rot (unforced/forced) |')
print('| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |')
for r in allr:
    j=r.get('joint')
    print(f"| {GENES.get(r['rx'],r['rx'])} | {r['pass']} | {r.get('bytes')} | {r.get('M')} | {r.get('Mperm')} | {r.get('Mhc')} | {r.get('nforces')} | {r.get('climb_ratio')} @ {r.get('climb_bytes')} | {r.get('fM')} | {r.get('fMperm')} | **{j}** | {j-2338 if j else '':+} | {r.get('fLCS','')}/{r.get('fLCSrfj','')} | {r.get('rot')}/{r.get('frot')} |")
print()
for r in allr:
    if r.get('forces'): print(f"- {GENES.get(r['rx'],r['rx'])} {r['pass']}: `{r['forces']}`")
