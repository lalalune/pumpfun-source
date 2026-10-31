import sys,os,collections
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled
from fact import mk
from lcschunk_m import matched_ops
from fhist import r10off
O=oracle.orig_window(); ot,oo=xled.toks(O)
lo,hi=-int(sys.argv[2],16),-int(sys.argv[3],16)
for p in sys.argv[1].split(','):
    C=xled.load(p if (p=='main' or '.' in p) else f'{os.path.dirname(T)}/rx/{p}/fn.bin'); ct,co=xled.toks(C)
    ops=matched_ops(mk(1,1,1)(ot),mk(1,1,1)(ct)); m=collections.defaultdict(collections.Counter)
    for op,i,j in ops:
        if op!='=': continue
        a,b=r10off(ot[i]),r10off(ct[j])
        if isinstance(a,int) and isinstance(b,int) and lo<=a<=hi: m[a][b]+=1
    print(p,' '.join(f'{-a:#x}->{",".join(f"{-b:#x}" for b,_ in m[a].most_common(2))}' for a in sorted(m,reverse=True)))
