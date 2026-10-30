import re,sys,difflib,collections
O=[(int(l.split()[0],16)-0x22a10,l.split(None,1)[1].strip()) for l in open('orig.dis')]
C=[(int(l.split()[0],16),l.split(None,1)[1].strip()) for l in open(sys.argv[1])]
def norm(s):
    s=re.sub(r'\s+<[^>]*>','',s)
    if s.startswith('call'): s='call'
    s=re.sub(r'^lddw (r\d+), .*',r'lddw \1',s)
    s=re.sub(r'r10 - 0x[0-9a-f]+','FP',s)
    m=re.match(r'^(j\w+ .*?)([+-]0x[0-9a-f]+|[+-]\d+)$',s)
    if s.startswith('j') and m: s=m.group(1)+'J'
    return s
def skel(s): return re.sub(r'\br[0-9]\b','R',s)
on=[norm(s) for _,s in O]; cn=[norm(s) for _,s in C]
sm=difflib.SequenceMatcher(None,[skel(x) for x in on],[skel(x) for x in cn],autojunk=False)
seg=int(sys.argv[2],16) if len(sys.argv)>2 else 0x400
maps=collections.defaultdict(collections.Counter)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag!='equal': continue
    for k in range(i2-i1):
        a=re.findall(r'\br([0-9])\b',on[i1+k]); b=re.findall(r'\br([0-9])\b',cn[j1+k])
        for x,y in zip(a,b):
            if x!=y: maps[O[i1+k][0]//seg][(x,y)]+=1
print('skeleton ratio',round(sm.ratio(),4))
for r in sorted(maps):
    print('%05x'%(r*seg), ' '.join('o%s->c%s:%d'%(x,y,n) for (x,y),n in maps[r].most_common(5)))
