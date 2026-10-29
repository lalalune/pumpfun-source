import sys,re,json,subprocess; sys.path.insert(0,sys.argv[1]+'/scripts')
sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/restore/reconstruction/harness')
from m13 import *
import coords as CO
M=model(sys.argv[2],sys.argv[3])
orig=(C.BASE/'original.so').read_bytes()
lo,hi=int(sys.argv[4],16),int(sys.argv[5],16)
nm=lambda a: re.sub(r'17h[0-9a-f]{16}E$','',M.names[a])[:90]
for st in sorted(M.wins):
    if not lo<=st<=hi: continue
    w=M.wins[st]
    s=CO.sites(orig,M.osec,st,w['raw'])
    fl=sorted(set((x['path'].split('src/')[-1],x['line']) for x in s))
    a=M.pair.get(st)
    print(hex(st), hex(a) if a else '-', nm(a) if a else '?', fl[:6], '...' if len(fl)>6 else '')
