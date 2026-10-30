#!/usr/bin/env python3
# regmatch.py <cand.dis> [bucket_hex]: per original-address bucket, fraction of original tokens matched by difflib
import sys,re,difflib
def load(f): return [(int(l.split()[0],16),l.split(None,1)[1].strip()) for l in open(f)]
def toks(rows):
    out=[]
    for o,s in rows:
        s=re.sub(r'^call .*','call',s); s=re.sub(r'lddw (r\d+), .*',r'lddw \1',s)
        m=re.search(r'@(0x[0-9a-f]+)$',s)
        if m: s=s[:m.start()]+'%+d'%((int(m.group(1),16)-o-8)//8)
        out.append(s)
    return out
import os
O=load(os.environ.get('ORIG_DIS',os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w12a08-cto-errorder/an/orig.dis'))); C=load(sys.argv[1])
a=toks(O); b=toks(C)
sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
bk=int(sys.argv[2],16) if len(sys.argv)>2 else 0x800
m=[0]*len(a)
for i,j,n in sm.get_matching_blocks():
    for k in range(n): m[i+k]=1
from collections import defaultdict
tot=defaultdict(int); hit=defaultdict(int)
for (o,s),x in zip(O,m): tot[o//bk]+=1; hit[o//bk]+=x
print('ratio %.5f'%sm.ratio(), 'matched', sum(m), 'of', len(a))
print(' '.join(f'{k*bk:#x}:{hit[k]}/{tot[k]}' for k in sorted(tot)))
