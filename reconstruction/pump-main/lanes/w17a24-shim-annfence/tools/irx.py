#!/usr/bin/env python3
"""irx.py <base.ll> <name> <spec.json>: apply hand IR edits {after:{lineidx:[lines]}, before:{..}, replace:{lineidx:[old,new]}} (0-based
line indices into base) plus module decls, then score with fx. Experiment only."""
import sys,os,json
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import fx
base,name,spec=sys.argv[1:4]
L=open(base).read().split('\n'); S=json.load(open(spec)) if os.path.exists(spec) else json.loads(spec)
rep={}
for k,(old,new) in S.get('replace',{}).items():
    k=int(k); assert old in L[k],(k,old,L[k]); rep.setdefault(k,[L[k]]); rep[k][-1]=rep[k][-1].replace(old,new)
for k,v in S.get('after',{}).items():
    k=int(k); rep.setdefault(k,[L[k]]); rep[k]=rep[k]+v
for k,v in S.get('before',{}).items():
    k=int(k); rep.setdefault(k,[L[k]]); rep[k]=v+rep[k]
out=[]
for i,l in enumerate(L): out.extend(rep.get(i,[l]))
body='\n'.join(out)
import re
have=set(re.findall(r'^declare [^@]*(@[\w.$-]+)\(',body,re.M))
txt=body+'\n'+'\n'.join(d for d in S.get('decl',[]) if re.match(r'^declare [^@]*(@[\w.$-]+)\(',d).group(1) not in have)+'\n'
r=fx.run(txt,name,keep='--keep' in sys.argv); print(json.dumps(r))
