#!/usr/bin/env python3
"""reorder.py <cand.s> <ref.s> <out.s>: placement-only oracle. Reorders cand's fallthrough chains (maximal block runs
ending in ja/exit) into the order their first blocks have in ref's layout, matching blocks by (IR block name,
occurrence). Registers/frame of cand stay fixed: the result bounds cand's code under ref's block placement."""
import sys,re
def parse(p):
    L=open(p).read().split('\n')
    fs=[k for k,l in enumerate(L) if re.match(r'^_ZN14pump_recovered9admin_cto7execute\w*:',l)][0]
    fe=[k for k,l in enumerate(L) if l.startswith('.Lfunc_end0')][0]
    st=[k for k in range(fs+1,fe) if re.match(r'^(LBB0_\d+:|# %bb\.\d+:)',L[k])]
    bl=list(zip(st,st[1:]+[fe])); keys=[]; cnt={}
    for a,b in bl:
        n=L[a].split('#')[-1].strip(); cnt[n]=cnt.get(n,0)+1; keys.append((n,cnt[n]))
    return L,fs,fe,bl,keys
def last(L,b):
    xs=[l.strip() for l in L[b[0]+1:b[1]] if l.strip() and not l.strip().startswith(('#','.'))]
    return xs[-1] if xs else ''
cL,cfs,cfe,cbl,ck=parse(sys.argv[1]); rL,_,_,rbl,rk=parse(sys.argv[2])
rpos={k:i for i,k in enumerate(rk)}
chains=[]; cur=[]
for i,b in enumerate(cbl):
    cur.append(i); t=last(cL,b)
    if t.startswith('ja ') or t=='exit': chains.append(cur); cur=[]
if cur: chains.append(cur)
def key(ci):
    c=chains[ci]
    ps=[rpos[ck[i]] for i in c if ck[i] in rpos]
    return min(ps) if ps else None
ks=[key(i) for i in range(len(chains))]
# chains without a ref position inherit the previous chain's key + epsilon
order=[]; prev=-1
for i,k in enumerate(ks):
    if k is None: k=prev+0.5
    prev=k; order.append((k if i else -1,i))
order.sort()
body=[]
for _,ci in order:
    for i in chains[ci]: body+=cL[cbl[i][0]:cbl[i][1]]
open(sys.argv[3],'w').write('\n'.join(cL[:cbl[0][0]]+body+cL[cfe:]))
print('chains',len(chains),'moved',sum(1 for j,(_,ci) in enumerate(order) if ci!=j))
