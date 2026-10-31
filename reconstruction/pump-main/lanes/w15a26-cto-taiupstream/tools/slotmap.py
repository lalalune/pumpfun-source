#!/usr/bin/env python3
"""slotmap.py orig.dis cand.dis [lo hi]: align skeletons (regs+frame offsets masked); for aligned pairs with r10 refs,
print orig slot -> cand slot mapping (first occurrence order) and the count of mismatches. Experiment only."""
import sys,re,difflib,collections
def load(f):
    out=[]
    for l in open(f):
        a,t=l.strip().split(' ',1); out.append((int(a,16),t))
    return out
def sk(t): return re.sub(r'r\d','r',re.sub(r'[-+]0x[0-9a-f]+','#',t))
A=load(sys.argv[1]);B=load(sys.argv[2]); lo,hi=(int(sys.argv[3],0),int(sys.argv[4],0)) if len(sys.argv)>4 else (0,1<<30)
sm=difflib.SequenceMatcher(None,[sk(t) for _,t in A],[sk(t) for _,t in B],autojunk=False)
m=collections.OrderedDict(); bad=0; tot=0
for x,y,n in sm.get_matching_blocks():
    for k in range(n):
        a,ta=A[x+k]; b,tb=B[y+k]
        if not lo<=a<hi: continue
        ra=re.search(r'\[r10-0x([0-9a-f]+)\]',ta); rb=re.search(r'\[r10-0x([0-9a-f]+)\]',tb)
        if ra and rb:
            tot+=1; oa,ob=int(ra.group(1),16),int(rb.group(1),16)
            if oa!=ob: bad+=1
            m.setdefault(oa,collections.Counter())[ob]+=1
print('pairs',tot,'mismatch',bad)
for oa,c in sorted(m.items()):
    ob=c.most_common(1)[0][0]
    if ob!=oa or len(c)>1: print(f'{oa:#x} -> {dict((hex(k),v) for k,v in c.items())}  d={ob-oa:+#x}')
