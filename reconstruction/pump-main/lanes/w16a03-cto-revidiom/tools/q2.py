"""Query 2: 7-byte memcpy pieces (two overlapping ldxw/stxw pairs at k+3,k) i.e. [1,8) slices of an Option<Pubkey>-like aggregate."""
import sys,os,collections
sys.path.insert(0,os.path.dirname(__file__))
import shape
from win_dm import dm
o=shape.orig()
hits=collections.defaultdict(list)
for i in range(len(o)-3):
    p=[o[i+k][2] for k in range(4)]
    if p[0][0]=='ldxw' and p[1][0]=='stxw' and p[2][0]=='ldxw' and p[3][0]=='stxw':
        s0=p[0][1][1]; d0=p[1][1][0]; s1=p[2][1][1]; d1=p[3][1][0]
        if s0[0]=='m' and s1[0]=='m' and s0[1]==s1[1] and s0[2]-s1[2]==3 and d0[1]==d1[1] and d0[2]-d1[2]==3:
            w=shape.win_of(o[i][0])
            if w: hits[w[0]].append((o[i][0]-w[0], f"src {'fp' if s1[1]==10 else 'r%d'%s1[1]}{s1[2]:+#x} -> dst {'fp' if d1[1]==10 else 'r%d'%d1[1]}{d1[2]:+#x}"))
names={w[0]:(w[2][0] if w[2] else 'admin_cto?') for w in shape.windows()}
for w,v in sorted(hits.items(),key=lambda x:-len(x[1])):
    print(f'{w:#08x} {len(v):2d}  {dm(names[w])[:100]}')
    for a,s in v[:8]: print(f'      +{a:#06x} {s}')
