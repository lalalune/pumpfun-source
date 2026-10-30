#!/usr/bin/env python3
"""objmap.py <orig.rel> <cand.dis> <pe.log> <module.ll>: per our frame object (layout from debug llc), vote the original
offset of its base over frame-masked aligned accesses; prints our base, orig base votes, size, members."""
import sys,re,difflib,collections,subprocess,os
T=os.path.dirname(os.path.abspath(__file__))
sys.argv_=sys.argv
def load(p): return [(int(l.split(None,1)[0],16),l.rstrip('\n').split(None,1)[1]) for l in open(p)]
def ab(s):
    s=re.sub(r'\s*<[^>]*>$','',s.split(';')[0].strip())
    if s.startswith('call'): s='call'
    s=re.sub(r'lddw (r\d+), 0x[0-9a-f]+',r'lddw \1, X',s); s=re.sub(r'^(j\w+ .*)[+-]0x[0-9a-f]+$',r'\1J',s)
    s=re.sub(r'r10 - 0x[0-9a-f]+','FP',s); s=re.sub(r'^add64 (r\d+), -0x[0-9a-f]+$',r'add64 \1, -A',s)
    return s
def fo(s):
    m=re.search(r'r10 - (0x[0-9a-f]+)',s) or re.match(r'add64 r\d+, -(0x[0-9a-f]+)',s)
    return int(m.group(1),16) if m else None
O=load(sys.argv[1]); C=load(sys.argv[2])
lay=subprocess.run(['python3',T+'/layout.py',sys.argv[3],sys.argv[4]],capture_output=True,text=True).stdout.split('\n')
objs=[]
for l in lay:
    p=l.split()
    if len(p)<3: continue
    base=int(p[0],16); nm=p[2]; size=int(p[3]) if len(p)>3 and p[3].isdigit() else 8
    objs.append((base,max(size,1),nm,' '.join(p[4:])[:60]))
def obj_of(off):
    for b,s,n,m in objs:
        if b-s< off <=b or off==b: return (b,s,n,m)
sm=difflib.SequenceMatcher(None,[ab(x[1]) for x in O],[ab(x[1]) for x in C],autojunk=False)
V=collections.defaultdict(collections.Counter)
for a,b,k in sm.get_matching_blocks():
    for i in range(k):
        x,y=fo(O[a+i][1]),fo(C[b+i][1])
        if x is None or y is None: continue
        o=obj_of(y)
        if o: V[o][x+(o[0]-y)]+=1
for o in sorted(V,key=lambda o:o[0]):
    tot=sum(V[o].values()); best=V[o].most_common(3)
    d=best[0][0]-o[0]
    print(f'{o[0]:#6x} {o[2][:22]:22s} {o[1]:4d}  orig {" ".join(f"{v:#x}:{n}" for v,n in best)}  ({tot})  d={d:+#x}  {o[3]}')
