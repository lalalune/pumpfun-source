import sys
sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/restore/reconstruction/harness')
from score import sections
def ro(p):
    b=open(p,'rb').read(); s=sections(b)['.rodata']; return b[s['offset']:s['offset']+s['size']]
O=ro('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/restore/reconstruction/base/original.so'); C=ro(sys.argv[1])
lo,hi=int(sys.argv[2],16),int(sys.argv[3],16)
print('O',O[lo:hi]); print(); print('C',C[lo:hi])
