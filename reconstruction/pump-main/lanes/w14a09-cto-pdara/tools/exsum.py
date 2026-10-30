#!/usr/bin/env python3
"""exsum.py: per trial in results2.jsonl, exact matches per 0x800 region (cached in exsum.jsonl)."""
import sys,os,json,difflib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from slots import orig_dis,cand_dis
O=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
o=orig_dis(); W=0x800
cache={}
if os.path.exists(O+'/exsum.jsonl'):
    for l in open(O+'/exsum.jsonl'): d=json.loads(l); cache[d['name']]=d
RF=os.environ.get('RES',O+'/results2.jsonl'); CF=RF.replace('.jsonl','_ex.jsonl') if 'results3' in RF else O+'/exsum.jsonl'
cache={}
if os.path.exists(CF):
    for l in open(CF): d=json.loads(l); cache[d['name']]=d
R=[json.loads(l) for l in open(RF)]
f=open(CF,'a')
for r in R:
    n=r['name']
    if n in cache or r.get('error'): continue
    p=O+'/rx/'+r.get('dir',n.replace('+','_'))+'/m.o'
    if not os.path.exists(p): continue
    c=cand_dis(p)
    sm=difflib.SequenceMatcher(None,[t for _,t in o],[t for _,t in c],autojunk=False)
    cnt=[0]*(o[-1][0]//W+1)
    for a,b,k in sm.get_matching_blocks():
        for j in range(k): cnt[o[a+j][0]//W]+=1
    d={'name':n,'ex':cnt,'ratio':r['ratio'],'bytes':r['bytes']}; cache[n]=d; f.write(json.dumps(d)+'\n'); f.flush()
rows=sorted(cache.values(),key=lambda d:-(d['ex'][6]+d['ex'][7]))
for d in rows[:int(sys.argv[1]) if len(sys.argv)>1 else 15]: print('%-28s %.5f %5d'%(d['name'][:28],d['ratio'],d['bytes']),' '.join('%4d'%x for x in d['ex']),'| tail',d['ex'][6]+d['ex'][7],'sum',sum(d['ex']))
