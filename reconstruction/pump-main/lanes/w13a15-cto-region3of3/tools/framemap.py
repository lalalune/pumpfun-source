#!/usr/bin/env python3
"""framemap.py orig.rel cand.rel [lo hi] : align frame/jump-masked streams, then for aligned pairs whose
r10 offsets differ, tally (orig_off -> cand_off) and the orig offsets where the pair occurs. Shows which frame
objects cost exact tokens inside [lo,hi) (orig rel offsets, hex)."""
import sys,re,difflib,collections
def load(p):
    return [(int(l.split(None,1)[0],16),l.rstrip('\n').split(None,1)[1]) for l in open(p)]
def ab(s,fr):
    lab=s.split(';')[1].strip()[:40] if ';' in s else ''
    s=re.sub(r'\s*<[^>]*>$','',s.split(';')[0].strip())
    if s.startswith('call'): s='call '+lab
    s=re.sub(r'lddw (r\d+), 0x[0-9a-f]+',r'lddw \1, X',s)
    s=re.sub(r'^(j\w+ .*)[+-]0x[0-9a-f]+$',r'\1J',s)
    if fr: s=re.sub(r'r10 - 0x[0-9a-f]+','FP',s); s=re.sub(r'^add64 (r\d+), -0x[0-9a-f]+$',r'add64 \1, -A',s)
    return s
def fo(s):
    m=re.search(r'r10 - (0x[0-9a-f]+)',s) or re.match(r'add64 r\d+, -(0x[0-9a-f]+)',s)
    return int(m.group(1),16) if m else None
O=load(sys.argv[1]); C=load(sys.argv[2])
lo,hi=(int(sys.argv[3],16),int(sys.argv[4],16)) if len(sys.argv)>4 else (0,1<<30)
sm=difflib.SequenceMatcher(None,[ab(x[1],1) for x in O],[ab(x[1],1) for x in C],autojunk=False)
T=collections.Counter(); W=collections.defaultdict(list)
for a,b,k in sm.get_matching_blocks():
    for i in range(k):
        o,c=O[a+i],C[b+i]
        if not(lo<=o[0]<hi): continue
        if ab(o[1],0)!=ab(c[1],0):
            x,y=fo(o[1]),fo(c[1])
            if x is not None and y is not None and x!=y:
                T[(x,y)]+=1; W[(x,y)].append(o[0])
            elif x is not None or y is not None: T[('reg+fp',)]+=1
            else: T[('reg',)]+=1
tot=0
for k,n in T.most_common(60):
    tot+=n
    if len(k)==2: print(f'-{k[0]:#x} -> -{k[1]:#x}  {n:3d}  at {" ".join("%x"%a for a in W[k][:8])}')
    else: print(k[0],n)
print('total aligned-but-different',sum(T.values()))
