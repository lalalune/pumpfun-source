#!/usr/bin/env python3
"""cfg.py <exec.ll> <value>: blocks dominated by the def block of <value>, with line numbers and whether value used there."""
import sys,re
L=open(sys.argv[1]).read().split('\n'); val=sys.argv[2]
blocks=[]; cur=None
for i,l in enumerate(L):
    m=re.match(r'^("[^"]+"|[\w.$-]+):',l)
    if i==0 or m:
        cur={'name':'entry' if i==0 else m.group(1).strip('"'),'start':i+1,'lines':[]}; blocks.append(cur)
    cur['lines'].append((i+1,l))
succ={}
for b in blocks:
    term=[l for _,l in b['lines'] if l.strip().startswith(('br ','switch ','ret ','unreachable','invoke'))]
    t=term[-1] if term else ''
    if t.strip().startswith('switch'):
        idx=[j for j,(_,l) in enumerate(b['lines']) if l.strip().startswith('switch')][0]
        t=' '.join(l for _,l in b['lines'][idx:])
    succ[b['name']]=[x.strip('"') for x in re.findall(r'label %("[^"]+"|[\w.$-]+)',t)]
names=[b['name'] for b in blocks]; pred={n:[] for n in names}
for n in names:
    for s in succ[n]: pred[s].append(n)
dom={n:set(names) for n in names}; dom['entry']={'entry'}
ch=True
while ch:
    ch=False
    for n in names[1:]:
        ps=[dom[p] for p in pred[n]]
        nd=set.intersection(*ps)|{n} if ps else {n}
        if nd!=dom[n]: dom[n]=nd; ch=True
db=[b['name'] for b in blocks if any(re.match(r'\s*'+re.escape(val)+r' = ',l) for _,l in b['lines'])][0]
for b in blocks:
    if db in dom[b['name']]:
        used=any(re.search(re.escape(val)+r'(?![\w.])',l) for _,l in b['lines'])
        print(b['start'],b['name'][:70],'USE' if used else '', 'succ=%d'%len(succ[b['name']]))
