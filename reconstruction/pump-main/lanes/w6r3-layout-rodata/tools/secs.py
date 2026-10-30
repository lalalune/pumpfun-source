import sys
H='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w6r3-layout-rodata/reconstruction'
sys.path.insert(0,H+'/harness'); from score import sections
o=open(H+'/base/original.so','rb').read(); c=open(sys.argv[1],'rb').read(); A=sections(o); C=sections(c)
for n in A:
  if n in C and n:
    x=o[A[n]['offset']:A[n]['offset']+A[n]['size']]; y=c[C[n]['offset']:C[n]['offset']+C[n]['size']]
    print(n,hex(A[n]['addr']),hex(C[n]['addr']),len(x),len(y),len(y)-len(x),'identical' if x==y else 'differ')
