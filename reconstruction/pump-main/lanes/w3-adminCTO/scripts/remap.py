# remap.py orig cand: oracle upper bound - remap each cand r10 offset to its most frequent aligned orig offset, then exact difflib ratio
import sys,re,difflib,collections
def rd(f):
    return [l.split(None,1)[1].strip() for l in open(f)]
def norm(s):
    s=re.sub(r'call -?0x[0-9a-f]+','call X',s); s=re.sub(r'lddw (r\d+), 0x[0-9a-f]+',r'lddw \1, X',s); return s
o=[norm(x) for x in rd(sys.argv[1])]; c=[norm(x) for x in rd(sys.argv[2])]
ab=lambda s: re.sub(r'r10 - 0x[0-9a-f]+','r10-X',re.sub(r'^add64 (r\d+), -0x[0-9a-f]+$',r'add64 \1, -A',s))
sm=difflib.SequenceMatcher(None,[ab(x) for x in o],[ab(x) for x in c],autojunk=False)
pairs=collections.defaultdict(collections.Counter)
offs=lambda s: [int(x,16) for x in re.findall(r'r10 - (0x[0-9a-f]+)',s)]+([int(m.group(1),16)] if (m:=re.match(r'^add64 r\d+, -(0x[0-9a-f]+)$',s)) else [])
for t,i1,i2,j1,j2 in sm.get_opcodes():
    if t=='equal':
        for k in range(i2-i1):
            for a,b in zip(offs(o[i1+k]),offs(c[j1+k])): pairs[b][a]+=1
mp={b:cn.most_common(1)[0][0] for b,cn in pairs.items()}
def rm(s):
    s=re.sub(r'r10 - (0x[0-9a-f]+)',lambda m:'r10 - %#x'%mp.get(int(m.group(1),16),int(m.group(1),16)),s)
    return re.sub(r'^(add64 r\d+), -(0x[0-9a-f]+)$',lambda m:'%s, -%#x'%(m.group(1),mp.get(int(m.group(2),16),int(m.group(2),16))),s)
c2=[rm(x) for x in c]
print('exact',round(difflib.SequenceMatcher(None,o,c,autojunk=False).ratio(),4),'remapped',round(difflib.SequenceMatcher(None,o,c2,autojunk=False).ratio(),4))
