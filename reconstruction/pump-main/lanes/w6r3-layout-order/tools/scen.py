import sys,re
sys.path.insert(0,__file__.rsplit('/',1)[0])
from m13 import *
M=model(sys.argv[1],sys.argv[2])
nm=lambda a: re.sub(r'17h[0-9a-f]{16}E$','',M.names[a])
order=list(M.cst)
base=M.eval(order)
print('as built',len(base),'text delta',sum(M.units[a][0] for a in order)-M.osec['.text']['size'])
wrong=[a for a in order if a not in M.inv or M.inv[a] in M.UN]
for a in wrong:
    i=order.index(a)
    print(hex(a),M.units[a][0], (M.wins[M.inv[a]]['bytes'] if a in M.inv else 'extra'), hex(M.inv.get(a,0)), M.region(a), i, nm(a)[:80])
import itertools
X=([a for a in wrong if a not in M.inv]+[None])[0]
W=[a for a in wrong if a in M.inv]
def run(fix,drop=True,ordr=None):
    sz=lambda a: 0 if (drop and a==X) else (M.wins[M.inv[a]]['bytes'] if a in fix else M.units[a][0])
    return len(M.eval(ordr or order,sz))
print('drop extra',run(set()))
for k in range(1,len(W)+1):
    best=max((run(set(c)),[nm(x)[16:40] for x in c]) for c in itertools.combinations(W,k))
    print(k,best)
print('drop+all',run(set(W)), 'keep+all',run(set(W),False))
