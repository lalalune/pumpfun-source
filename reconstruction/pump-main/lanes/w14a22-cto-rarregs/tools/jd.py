#!/usr/bin/env python3
# jd.py <orig> <cand>: align (regs/frame/jump masked), list aligned jumps whose offsets differ: orig addr, target, delta (slots)
import sys,re,difflib,collections
def rd(f):
    R=[]
    for l in open(f):
        p=l.split(None,1)
        if len(p)<2: continue
        R.append((int(p[0],16),p[1].strip()))
    return R
def norm(s):
    s=re.sub(r'^call .*','call',s); s=re.sub(r'lddw (r\d+), .*',r'lddw',s); s=re.sub(r'r10 - 0x[0-9a-f]+','F',s); s=re.sub(r'\br[0-9]\b','R',s)
    return re.sub(r'[+-]0x[0-9a-f]+$','J',s) if s.startswith('j') else s
def off(s):
    m=re.search(r'([+-]0x[0-9a-f]+)$',s); return int(m.group(1),16)
o=rd(sys.argv[1]); c=rd(sys.argv[2])
sm=difflib.SequenceMatcher(None,[norm(s) for _,s in o],[norm(s) for _,s in c],autojunk=False)
D=collections.Counter(); bad=[]; n=0
for a,b,s in sm.get_matching_blocks():
    for i in range(s):
        oa,os_=o[a+i]; ca,cs=c[b+i]
        if os_.startswith('j'):
            n+=1; d=off(cs)-off(os_)
            if d: bad.append((oa,oa+8+off(os_)*8,d)); D[d]+=1
print('aligned jumps',n,'differing',len(bad)); print(D.most_common(12))
B=collections.Counter((x//0x800*0x800,t//0x800*0x800) for x,t,d in bad)
for k,v in sorted(B.items(),key=lambda x:-x[1])[:20]: print(hex(k[0]),'->',hex(k[1]),v)
