"""fdelta.py <rxname|main>: fp-offset deltas (cand - orig) over true-LCS (rfj) matched instruction pairs, per orig 0x800 chunk."""
import sys,io,contextlib,collections
sys.path.insert(0,'.')
sys.argv_saved=sys.argv; sys.argv=['x']
with contextlib.redirect_stdout(io.StringIO()):
    import binlcs, runs, shape
sys.argv=sys.argv_saved
from runs import matched, tok_rfj
O=binlcs.ON
for name in sys.argv[1:]:
    if name=='main':
        C=[(a,t,shape.parse(t)) for a,t,p in runs.cto_insns('main')]
        C=[(a,binlcs.re.sub(r'^call .*$','call 0x0',binlcs.re.sub(r'^lddw (r\d+), .*$',r'lddw \1, 0x0',t)),None) for a,t,p in C]
        C=[(a,t,shape.parse(t)) for a,t,_ in C]
    else:
        C=binlcs.dis_bin(open(f'../rx/{name}/fn.bin','rb').read())
    h=matched([tok_rfj(x[2]) for x in O],[tok_rfj(x[2]) for x in C])
    per=collections.defaultdict(collections.Counter)
    for i,j in enumerate(h):
        if j is None: continue
        po=[o for o in O[i][2][1] if o[0]=='m' and o[1]==10]; pc=[o for o in C[j][2][1] if o[0]=='m' and o[1]==10]
        if po and pc: per[O[i][0]//0x800][pc[0][2]-po[0][2]]+=1
    print('==',name)
    for k in sorted(per):
        c=per[k]; tot=sum(c.values())
        print(f'  orig {k*0x800:#06x}: n={tot:4d} ' + ' '.join(f'{d:+d}:{n}' for d,n in c.most_common(4)))
