"""segstat.py <so|fn.bin> [seg] [lo hi]: per original segment, plain matched / reg-masked / reg+frame masked tokens."""
import sys,difflib,collections
sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import ctoracle as co, tokio
otok,w=co.orig_tokens(); ctok=tokio.toks(sys.argv[1])
seg=int(sys.argv[2],16) if len(sys.argv)>2 else 0x400
lo=int(sys.argv[3],16) if len(sys.argv)>3 else 0; hi=int(sys.argv[4],16) if len(sys.argv)>4 else 1<<30
def mreg(t):
    b=bytearray(t); d=b[1]&15; s=b[1]>>4
    if d!=10: d=0
    if s!=10 and b[0]!=0x85: s=0
    b[1]=(s<<4)|d; return bytes(b)
off=[];o=0
for t in otok: off.append(o); o+=len(t)
fs=[lambda t:t, mreg, co.abstract, lambda t:co.abstract(mreg(t))]
R=[collections.Counter() for _ in fs]; N=collections.Counter()
for i in range(len(otok)): N[off[i]//seg]+=1
for k,f in enumerate(fs):
    sm=difflib.SequenceMatcher(None,[f(t) for t in otok],[f(t) for t in ctok],autojunk=False)
    for a,b,sz in sm.get_matching_blocks():
        for j in range(sz): R[k][off[a+j]//seg]+=1
tot=[0]*4;tn=0
for s in sorted(N):
    if not (lo<=s*seg<hi): continue
    tn+=N[s]
    for k in range(4): tot[k]+=R[k][s]
    print(f'{s*seg:#07x} n={N[s]:4d} plain={R[0][s]:4d} reg={R[1][s]:4d} frame={R[2][s]:4d} both={R[3][s]:4d}')
print('total',tn,tot)
