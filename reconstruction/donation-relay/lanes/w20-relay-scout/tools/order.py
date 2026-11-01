import sys,os,json,bisect
sys.path.insert(0,os.path.expanduser('~/.cache/pumpfun-reconstruction/relay/tools'))
import relay
from relaylib import *
cand=sys.argv[1]
t,c,sy,tf,tn,cn,pair,idx=relay.compare(cand)
seq=[(a,pair[a]) for a,_ in tf if a in pair]
# LIS of candidate addresses in target order
tails=[];prev=[None]*len(seq);tidx=[]
for i,(a,b) in enumerate(seq):
    k=bisect.bisect_left(tails,b)
    if k==len(tails): tails.append(b);tidx.append(i)
    else: tails[k]=b;tidx[k]=i
    prev[i]=tidx[k-1] if k>0 else None
lis=set();i=tidx[-1]
while i is not None: lis.add(i);i=prev[i]
print('matched',len(seq),'in-order LIS',len(lis))
print('out of order:')
for i,(a,b) in enumerate(seq):
    if i not in lis:
        print(hex(a),tn and dict(tf)[a],hex(b),demangle(sy[b][1])[:110],sy[b][1][-20:])
