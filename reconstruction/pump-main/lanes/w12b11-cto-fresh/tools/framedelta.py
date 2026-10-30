#!/usr/bin/env python3
"""framedelta.py orig.txt cand.txt : align (segab abstraction) and report orig r10 offset -> candidate offset deltas,
grouped into runs over orig offsets (shows where the frame shifts)."""
import sys,re,difflib,collections
def ab(l):
    ins=l.split(None,1)[1].split(';')[0].strip()
    offs=re.findall(r'r10 - (0x[0-9a-f]+)',ins)
    m=re.match(r'^add64 (r\d+), -(0x[0-9a-f]+)$',ins)
    if m: offs=[m.group(2)]
    a=ins
    a=re.sub(r'call -?0x[0-9a-f]+','call X',a); a=re.sub(r'lddw (r\d+), 0x[0-9a-f]+',r'lddw \1, X',a)
    a=re.sub(r'r10 - 0x[0-9a-f]+','FP',a); a=re.sub(r'^add64 (r\d+), -0x[0-9a-f]+$',r'add64 \1, -A',a)
    a=re.sub(r'^(j\w+ .*)[+-]0x[0-9a-f]+$',r'\1J',a); a=re.sub(r'\br[0-9]\b','R',a)
    return a,[int(x,16) for x in offs]
o=[ab(l) for l in open(sys.argv[1]) if l.strip()]; c=[ab(l) for l in open(sys.argv[2]) if l.strip()]
sm=difflib.SequenceMatcher(None,[x[0] for x in o],[x[0] for x in c],autojunk=False)
pairs=collections.defaultdict(collections.Counter)
for t,i1,i2,j1,j2 in sm.get_opcodes():
    if t=='equal':
        for k in range(i2-i1):
            for oo,cc in zip(o[i1+k][1],c[j1+k][1]): pairs[oo][cc]+=1
# best mapping per orig offset
rows=[]
for oo in sorted(pairs):
    cc,n=pairs[oo].most_common(1)[0]; tot=sum(pairs[oo].values())
    rows.append((oo,cc,n,tot))
# print runs of equal delta
prev=None
for oo,cc,n,tot in rows:
    d=cc-oo
    if d!=prev:
        print(f'orig {oo:#06x} -> cand {cc:#06x}  delta {d:+#x}  ({n}/{tot})')
        prev=d
print('n offsets',len(rows), 'equal-delta0:',sum(1 for r in rows if r[1]==r[0]))
