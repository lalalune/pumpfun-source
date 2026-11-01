"""chunkcmp.py <mask r f j> <name>...: per orig 0x800 chunk, true-LCS matched tokens of each candidate minus main."""
import sys,io,contextlib,collections
sys.path.insert(0,'.')
argv=sys.argv; sys.argv=['x']
with contextlib.redirect_stdout(io.StringIO()):
    import binlcs,runs,shape,lcsm
sys.argv=argv
from runs import matched
r,f,j=[int(x) for x in argv[1]]
O=binlcs.ON
def per(C):
    h=matched([lcsm.tok(x[2],r,f,j) for x in O],[lcsm.tok(x[2],r,f,j) for x in C])
    d=collections.Counter()
    for i,x in enumerate(h):
        if x is not None: d[O[i][0]//0x800]+=1
    return d
M=[(a,t,shape.parse(t)) for a,t,p in runs.cto_insns('main')]
import re
M=[(a,re.sub(r'^call .*$','call 0x0',re.sub(r'^lddw (r\d+), .*$',r'lddw \1, 0x0',t)),None) for a,t,p in M]
M=[(a,t,shape.parse(t)) for a,t,_ in M]
dm=per(M); print('main',sum(dm.values()),' '.join(f'{k*0x800:x}:{dm[k]}' for k in sorted(dm)))
for n in argv[2:]:
    C=binlcs.dis_bin(open(f'../rx/{n}/fn.bin','rb').read()); d=per(C)
    print(n,sum(d.values())-sum(dm.values()),' '.join(f'{k*0x800:x}:{d[k]-dm[k]:+d}' for k in sorted(dm)))
