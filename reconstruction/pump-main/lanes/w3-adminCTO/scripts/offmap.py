#!/usr/bin/env python3
"""offmap.py orig.txt cand.txt pei.txt allocas.txt: align insn streams with r10 offsets abstracted; map cand frame objects -> orig offsets."""
import sys,re,difflib,collections
def load(f):
    L=[]
    for l in open(f):
        a,ins=l.split(None,1); ins=ins.strip()
        offs=[int(x,16) for x in re.findall(r'r10 - (0x[0-9a-f]+)',ins)]
        m=re.match(r'add64 (r\d+), -(0x[0-9a-f]+)$',ins)
        n=re.sub(r'r10 - 0x[0-9a-f]+','r10-X',ins)
        n=re.sub(r'call -?0x[0-9a-f]+','call',n); n=re.sub(r'lddw (r\d+), 0x[0-9a-f]+',r'lddw \1',n)
        n=re.sub(r'([+-]) ?0x[0-9a-f]+$',r'\1J',n) if n.startswith('j') else n
        if m: n=f'add64 {m.group(1)}, -A'; offs=[int(m.group(2),16)]
        L.append((a,n,offs))
    return L
o=load(sys.argv[1]); c=load(sys.argv[2])
sm=difflib.SequenceMatcher(None,[x[1] for x in o],[x[1] for x in c],autojunk=False)
pairs=collections.Counter()
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal':
        for k in range(i2-i1):
            for oo,cc in zip(o[i1+k][2],c[j1+k][2]): pairs[(cc,oo)]+=1
print('ratio(abstracted)',round(sm.ratio(),4),file=sys.stderr)
# frame objects
objs=[]
for l in open(sys.argv[3]):
    m=re.match(r'\s*fi#(\d+): size=(\d+), align=\d+, at location \[SP-(\d+)\]',l)
    if m and int(m.group(1))>=0: objs.append((int(m.group(1)),int(m.group(2)),int(m.group(3))))
names={}
if len(sys.argv)>4:
    for l in open(sys.argv[4]):
        m=re.match(r'fi#\s*(\d+) (\S+)',l)
        if m: names[int(m.group(1))]=m.group(2)
def obj(off):
    for fi,s,loc in objs:
        if loc-s< off<=loc: return fi,s,loc
    return None
res=collections.defaultdict(collections.Counter)
for (cc,oo),n in pairs.items():
    ob=obj(cc)
    if ob: res[ob][oo-(ob[2]-cc)]+=n   # implied orig base = oo + (loc-cc) ... store orig base offset
for ob in sorted(res,key=lambda x:x[0]):
    fi,s,loc=ob
    # implied orig location of object base: orig_off + (loc - cand_off)
    tot=collections.Counter()
    for (cc,oo),n in pairs.items():
        if obj(cc)==ob: tot[oo+(loc-cc)]+=n
    best=tot.most_common(3)
    print(f'fi#{fi:3d} {names.get(fi,"spill"):30s} size={s:4d} cand={loc:#x} orig~ '+' '.join(f'{b:#x}({n})' for b,n in best))
