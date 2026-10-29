import sys,re,bisect; sys.path.insert(0,sys.argv[1]+'/scripts')
sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/restore/reconstruction/harness')
from m13 import *
import coords as CO
M=model(sys.argv[2],sys.argv[3])
orig=(C.BASE/'original.so').read_bytes()
nm=lambda a: re.sub(r'17h[0-9a-f]{16}E$','',M.names[a])[:100]
L=[a for a in M.cst if a in M.inv and M.region(a)=='L']
v=[M.inv[a] for a in L]
tails=[];tidx=[];prev=[-1]*len(v)
for i,x in enumerate(v):
    j=bisect.bisect_left(tails,x)
    if j==len(tails): tails.append(x);tidx.append(i)
    else: tails[j]=x;tidx[j]=i
    prev[i]=tidx[j-1] if j>0 else -1
lis=set();k=tidx[-1]
while k>=0: lis.add(k);k=prev[k]
print('L',len(L),'LIS',len(lis))
oL=sorted(L,key=lambda a:M.inv[a]); pos={a:i for i,a in enumerate(oL)}
for i,a in enumerate(L):
    if i in lis: continue
    st=M.inv[a]; s=CO.sites(orig,M.osec,st,M.wins[st]['raw'])
    fl=sorted(set((x['path'].split('src/')[-1],x['line']) for x in s))
    p=oL[pos[a]-1]
    print(f'{st:#x} {M.units[a][0]:6} {nm(a)[:85]:85} sites={len(fl)} {fl[:1]} | orig-after {nm(p)[15:70]}')
