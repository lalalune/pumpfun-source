#!/usr/bin/env python3
# jp.py <pre-BF .mir> : list the bb56.i join's predecessors (and of its single-succ feeder bb52.i*) with their r5 defs
import sys,re
t=open(sys.argv[1]).read().split('\n'); cur=None; succ={}; body={}; name={}
for l in t:
    m=re.match(r'^  bb\.(\d+)\.?([^:]*):',l)
    if m: cur=int(m.group(1)); name[cur]=m.group(2); body[cur]=[]; continue
    if cur is None: continue
    if 'successors:' in l: succ[cur]=[int(x) for x in re.findall(r'%bb\.(\d+)',l)]
    body[cur].append(l.strip())
J=[k for k,v in name.items() if v=='bb56.i']
def preds(b): return [k for k,v in succ.items() if b in v]
for j in J:
    P=preds(j); ext=[q for p in P if name[p].startswith('bb52.i') for q in preds(p)]
    for b in P+ext: print(b,name[b][:30],[s for s in body[b] if s.startswith('$r5 =')][-1:], 'liveins:'+','.join(re.findall(r'\$r\d',' '.join(x for x in body[b] if x.startswith('liveins')))))
