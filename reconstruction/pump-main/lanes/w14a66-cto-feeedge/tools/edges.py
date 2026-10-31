#!/usr/bin/env python3
"""edges.py m.ll : list critical edges (cond-br pred -> multi-pred succ) in execute as 'PRED SUCC' lines."""
import sys,re
t=open(sys.argv[1]).read()
k=t.index('define '); k=t.index('admin_cto7execute',k); k=t.rindex('\ndefine',0,k); e=t.index('\n}\n',k)
body=t[k:e]
blocks=re.split(r'\n\n',body)
preds={}; terms={}
for b in blocks:
    L=b.strip('\n').split('\n')
    m=re.match(r'^("?[^:\s]+"?):',L[0])
    if not m: continue
    name=m.group(1)
    term=[l for l in L if l.strip()][-1].strip()
    terms[name]=term
    for s in re.findall(r'label %("[^"]+"|[\w.$]+)',term): preds.setdefault(s,[]).append(name)
for p,term in terms.items():
    if not term.startswith('br i1'): continue
    ss=re.findall(r'label %("[^"]+"|[\w.$]+)',term)
    if len(set(ss))!=2: continue
    for s in ss:
        if len(set(preds.get(s,[])))>1: print(p,s)
