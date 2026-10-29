#!/usr/bin/env python3
"""rpo.py raw.ll [flip:BB ...]: rebuild MIR-ish CFG from raw rustc IR, simulate rustc RPO codegen + first-reference block creation; compare to raw order.
MIR successor model: 'br i1 c, T, F' -> switchInt [0:F, otherwise:T] (case F created first);
switch -> [cases..., otherwise] (otherwise created first). flip:BB swaps the 2-way successor order (as if switch on !c)."""
import sys,re
L=open(sys.argv[1]).read().split('\n')
flips={a.split(':')[1] for a in sys.argv[2:] if a.startswith('flip:')}
order=[];kind={};succ={};cur=None
for l in L[1:]:
    m=re.match(r'^([A-Za-z0-9_.$"]+):',l)
    if m: cur=m.group(1); order.append(cur); succ[cur]=[]; kind[cur]='none'; continue
    if cur is None and l.strip(): cur='start'; order.append(cur); succ[cur]=[]; kind[cur]='none'
    s=l.strip()
    if s.startswith('br i1'):
        t,f=re.findall(r'label %([A-Za-z0-9_.$"]+)',s); succ[cur]=[f,t]; kind[cur]='2'
    elif s.startswith('br label'):
        succ[cur]=re.findall(r'label %([A-Za-z0-9_.$"]+)',s); kind[cur]='1'
    elif s.startswith('switch'):
        succ[cur]=['__D__'+re.findall(r'label %([A-Za-z0-9_.$"]+)',s)[0]]; kind[cur]='n'
    elif re.match(r'i\d+ -?\d+, label',s):
        succ[cur].insert(len(succ[cur])-1,re.findall(r'label %([A-Za-z0-9_.$"]+)',s)[0])
for b in order:
    succ[b]=[x.replace('__D__','') for x in succ[b]]
    if b in flips and kind[b]=='2': succ[b]=succ[b][::-1]
    elif b in flips and kind[b]=='n': succ[b]=succ[b][:-1][::-1]+succ[b][-1:]
def rpo(entry):
    seen={entry}; post=[]; stack=[(entry,iter(succ[entry][::-1]))]
    while stack:
        b,it=stack[-1]
        nxt=next((x for x in it if x not in seen),None)
        if nxt is None: post.append(b); stack.pop(); continue
        seen.add(nxt); stack.append((nxt,iter(succ[nxt][::-1])))
    return post[::-1]
R=rpo('start'); created=[]
def mk(x):
    if x not in created: created.append(x)
for b in R:
    mk(b)
    if kind[b]=='2': mk(succ[b][0]); mk(succ[b][1])
    elif kind[b]=='n': mk(succ[b][-1]); [mk(x) for x in succ[b][:-1]]
    else: [mk(x) for x in succ[b]]
print('RPO    ',' '.join(R))
print('created',' '.join(created))
print('raw    ',' '.join(order))
print('MATCH' if created==order else 'DIFF')
