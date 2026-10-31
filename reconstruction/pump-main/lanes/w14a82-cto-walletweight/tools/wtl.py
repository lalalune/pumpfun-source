#!/usr/bin/env python3
"""wtl.py <ra.log> <lo> <hi> [roots..]: greedy timeline for vregs whose live range overlaps slot range [lo,hi).
For each selectOrSplit: step, vreg, root, stage, size(slots), overlap, weight, outcome (reg / evicted-by / split / spill).
With roots given, only their split families are shown."""
import sys,re,collections
log=open(sys.argv[1]).read().split('\n'); lo,hi=int(sys.argv[2]),int(sys.argv[3]); want=set(sys.argv[4:])
g=next(i for i,l in enumerate(log) if l.startswith('********** GREEDY'))
segre=re.compile(r'\[(\d+)[rBeRd],(\d+)[rBeRd]:\d+\)')
parent={}; seen=set(); cur=None; ev=[]; step=0
def segs(s): return [(int(a),int(c)) for a,c in segre.findall(s)]
for l in log[g:]:
    m=re.match(r'selectOrSplit GPR:(%\d+) (.*?)\s+weight:(\S+)',l)
    if m:
        cur=m.group(1); seen.add(cur); step+=1
        S=segs(m.group(2)); ev.append(dict(step=step,v=cur,segs=S,w=float(m.group(3)),stage='',out=[])); continue
    if not ev: continue
    e=ev[-1]
    m=re.match(r'(RS_\w+) Cascade (\d+)',l)
    if m: e['stage']=m.group(1)+'/'+m.group(2); continue
    m=re.match(r'queuing new interval: (%\d+)',l)
    if m:
        v=m.group(1)
        if v not in seen and v not in parent and v!=cur: parent[v]=cur; e['out'].append('new:'+v)
        continue
    m=re.match(r'assigning (%\d+) to \$(r\d+)',l)
    if m and m.group(1)==cur: e['out'].append('->'+m.group(2)); continue
    m=re.match(r'unassigning (%\d+) from \$(r\d+)',l)
    if m: e['out'].append('evict(%s@%s)'%(m.group(1),m.group(2))); continue
    if l.startswith('wait for second round'): e['out'].append('wait'); continue
    m=re.match(r'Inline spilling',l)
    if m: e['out'].append('SPILL'); continue
    m=re.match(r'Split for \$(r\d+) in (\d+) bundles',l)
    if m: e['out'].append('rsplit:%s/%s'%(m.group(1),m.group(2))); continue
    for k in ('tryLocalSplit','Split around','Split '):
        if l.startswith(k) and 'Split for' not in l: e['out'].append(l[:40]); break
def root(v):
    while v in parent: v=parent[v]
    return v
for e in ev:
    o=sum(max(0,min(b,hi)-max(a,lo)) for a,b in e['segs'])
    if o<=0: continue
    r=root(e['v'])
    if want and r not in want and e['v'] not in want: continue
    sz=sum(b-a for a,b in e['segs'])
    print('%5d %-6s root=%-6s %-14s sz=%6d ov=%5d [%d,%d) w=%.3e  %s'%(e['step'],e['v'],r,e['stage'],sz,o,e['segs'][0][0],e['segs'][-1][1],e['w'],' '.join(e['out'])[:150]))
