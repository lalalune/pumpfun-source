import sys,os,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import shape,srcmap
from win_dm import dm
o=shape.orig()
hits=[]
for i in range(len(o)-3):
    p=[o[i+k][2] for k in range(4)]
    if p[0][0]=='ldxw' and p[1][0]=='stxw' and p[2][0]=='ldxw' and p[3][0]=='stxw':
        s0=p[0][1][1]; d0=p[1][1][0]; s1=p[2][1][1]; d1=p[3][1][0]
        if s0[0]=='m' and s1[0]=='m' and s0[1]==s1[1] and s0[2]-s1[2]==3 and d0[1]==d1[1] and d0[2]-d1[2]==3:
            w=shape.win_of(o[i][0])
            if w and w[0]!=0x22a10: hits.append((w,o[i][0],s1,d1))
names={w[0]:(w[2][0] if w[2] else 'admin_cto') for w in shape.windows()}
seen=set()
for w,a,s1,d1 in hits:
    u=srcmap.userloc(a); l=srcmap.loc(a)
    inner=f'{l[1].split("/")[-1]}:{l[2]}' if l and l[1] else '?'
    snip=''
    if u:
        line=srcmap.srcline(u[0],u[1]); snip=line[max(0,u[2]-1):u[2]+90].strip()
    key=(w[0],u)
    tag='' if key not in seen else '(dup)'
    seen.add(key)
    sb='fp' if s1[1]==10 else f'r{s1[1]}'; db='fp' if d1[1]==10 else f'r{d1[1]}'
    print(f'{w[0]:#08x}+{a-w[0]:#06x} {sb}{s1[2]:+#x}->{db}{d1[2]:+#x} inner {inner:24s} user {u[0].split("/")[-1] if u else "?"}:{u[1] if u else ""} {snip[:100]} {dm(names[w[0]])[:50]} {tag}')
