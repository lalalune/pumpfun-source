#!/usr/bin/env python3
"""slottab.py <ours.txt> <lr.json>: per-spill-slot traffic, orig vs ours, slots paired by aligned (n2-equal) spill/reload votes."""
import sys,re,difflib,collections,json
sys.path.insert(0,__import__('os').path.dirname(__file__))
def load(p): return [(int(l.split()[0],16),l.split(None,1)[1].strip()) for l in open(p) if l.strip()]
O=load('orig.txt'); C=load(sys.argv[1]); slots=json.load(open(sys.argv[2]))['slots']
SP=re.compile(r'^stxdw \[r10 - (0x[0-9a-f]+)\], r\d$'); RL=re.compile(r'^ldxdw r\d, \[r10 - (0x[0-9a-f]+)\]$')
def n2(s):
    s=re.sub(r'\s+<[^>]*>','',s)
    if s.startswith('call'): return 'call'
    s=re.sub(r'^lddw (r\d+), .*',r'lddw \1',s); s=re.sub(r'r10 - 0x[0-9a-f]+','FP',s)
    if s.startswith('j'): s=re.sub(r'([+-]0x[0-9a-f]+|[+-]\d+)$','J',s)
    return re.sub(r'\br[0-9]\b','R',s)
def traffic(L):
    t=collections.defaultdict(lambda:[0,0])
    for a,s in L:
        m=SP.match(s)
        if m and 0x800<=int(m.group(1),16)<=0xc80: t[int(m.group(1),16)][0]+=1
        m=RL.match(s)
        if m and 0x800<=int(m.group(1),16)<=0xc80: t[int(m.group(1),16)][1]+=1
    return t
to=traffic(O); tc=traffic(C)
sm=difflib.SequenceMatcher(None,[n2(s) for _,s in O],[n2(s) for _,s in C],autojunk=False)
vote=collections.defaultdict(collections.Counter)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag!='equal': continue
    for k in range(i2-i1):
        a=SP.match(O[i1+k][1]) or RL.match(O[i1+k][1]); b=SP.match(C[j1+k][1]) or RL.match(C[j1+k][1])
        if a and b: vote[int(a.group(1),16)][int(b.group(1),16)]+=1
print('orig slot  st/ld | ours slot st/ld (votes) | ours values')
seen=set()
for x in sorted(to):
    v=vote.get(x); y=v.most_common(1)[0][0] if v else None; seen.add(y)
    vals='; '.join(s[:60] for s in slots.get(hex(y),[]))[:150] if y else ''
    print('-0x%03x %2d/%2d | %s %s (%s) | %s'%(x,*to[x],('-0x%03x'%y) if y else '   ?  ',('%2d/%2d'%tuple(tc[y])) if y else '',dict(v.most_common(3)) if v else '',vals))
print('ours slots never paired:')
for y in sorted(tc):
    if y not in seen: print('  -0x%03x %d/%d %s'%(y,*tc[y],'; '.join(s[:60] for s in slots.get(hex(y),[]))[:150]))
