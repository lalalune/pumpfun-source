import sys; sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w6r1-layout-rodata/reconstruction/harness')
from score import sections
a=open(sys.argv[1],'rb').read(); b=open(sys.argv[2],'rb').read(); A=sections(a); Bs=sections(b)
for n in ['.text','.rodata','.data.rel.ro']:
    x=a[A[n]['offset']:A[n]['offset']+A[n]['size']]; y=b[Bs[n]['offset']:Bs[n]['offset']+Bs[n]['size']]
    print(n,len(x),len(y),'identical' if x==y else 'differ %d bytes'%sum(1 for i,j in zip(x,y) if i!=j))
