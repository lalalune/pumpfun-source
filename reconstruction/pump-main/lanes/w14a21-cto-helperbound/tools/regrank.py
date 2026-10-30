#!/usr/bin/env python3
"""regrank.py ref results.jsonl lo hi: rank results by exact-match delta vs ref in orig [lo,hi) and elsewhere."""
import sys,os,difflib,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import oracle
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a21-cto-helperbound')
o=oracle.mask(oracle.orig_window()); addr=[];x=0
for t in o: addr.append(x); x+=len(t)
ref,res,lo,hi=sys.argv[1],sys.argv[2],int(sys.argv[3],16),int(sys.argv[4],16)
def per(n):
    p=f'{O}/rx/{n}/fn.bin'
    if not os.path.exists(p): return None
    c=oracle.mask(open(p,'rb').read()); sm=difflib.SequenceMatcher(None,o,c,autojunk=False); i=e=0
    for a,b,s in sm.get_matching_blocks():
        for k in range(s):
            if lo<=addr[a+k]<hi: i+=1
            else: e+=1
    return i,e,len(c)
R=per(ref); out=[]
for l in open(res):
    d=json.loads(l)
    if 'ratio' not in d: continue
    p=per(d['name'])
    if p: out.append((p[0]-R[0],p[1]-R[1],d['name'],d['bytes'],d['ratio']))
out.sort(reverse=True)
for r in out[:15]: print(r)
