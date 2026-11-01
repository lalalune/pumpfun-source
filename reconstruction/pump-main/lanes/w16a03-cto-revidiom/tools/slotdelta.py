"""slotdelta.py <rxname>: per original fp slot, the dominant cand-orig offset delta over rfj-matched pairs (only off slots)."""
import sys,io,contextlib,collections
sys.path.insert(0,'.')
argv=sys.argv; sys.argv=['x']
with contextlib.redirect_stdout(io.StringIO()):
    import binlcs,runs,shape
sys.argv=argv
from runs import matched,tok_rfj
O=binlcs.ON
name=sys.argv[1]
C=binlcs.dis_bin(open(f'../rx/{name}/fn.bin','rb').read())
h=matched([tok_rfj(x[2]) for x in O],[tok_rfj(x[2]) for x in C])
d=collections.defaultdict(collections.Counter)
for i,(a,t,p) in enumerate(O):
    j=h[i]
    if j is None: continue
    po=[o for o in p[1] if o[0]=='m' and o[1]==10]; pc=[o for o in C[j][2][1] if o[0]=='m' and o[1]==10]
    if po and pc: d[po[0][2]][pc[0][2]-po[0][2]]+=1
off=collections.Counter(); tot=0
for s in sorted(d):
    k,n=d[s].most_common(1)[0]; tot+=sum(d[s].values())
    if k!=0: off[k]+=sum(d[s].values())
print(name,'accesses',tot,'off by delta',off.most_common(8))
rng=collections.defaultdict(list)
for s in sorted(d):
    k,n=d[s].most_common(1)[0]
    if k!=0: rng[k].append(s)
for k,v in sorted(rng.items(),key=lambda x:-len(x[1]))[:4]:
    print(f'  delta {k:+d}: {len(v)} slots, orig range {hex(min(v))}..{hex(max(v))}')
