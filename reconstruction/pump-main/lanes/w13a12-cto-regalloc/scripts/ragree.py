"""ragree.py <so> [seg]: register agreement on structurally matched code.
Aligns orig vs candidate admin_cto with registers AND frame offsets/jump offsets masked, then for each matched pair
counts whether registers agree (frame-masked tokens equal). Prints totals + per-region (orig offset) table."""
import sys,difflib,collections
sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import ctoracle as co
def mreg(t):
    b=bytearray(t); d=b[1]&15; s=b[1]>>4
    if d!=10: d=0
    if s!=10 and b[0]!=0x85: s=0
    b[1]=(s<<4)|d; return bytes(b)
def run(path,seg=0x800,quiet=False):
    otok,w=co.orig_tokens(); ctok,n=co.so_tokens(path)
    f=lambda t: co.abstract(mreg(t))
    sm=difflib.SequenceMatcher(None,[f(t) for t in otok],[f(t) for t in ctok],autojunk=False)
    off=[];o=0
    for t in otok: off.append(o); o+=len(t)
    R=collections.defaultdict(lambda:[0,0]); tot=[0,0]
    for a,b,sz in sm.get_matching_blocks():
        for k in range(sz):
            eq=co.abstract(otok[a+k])==co.abstract(ctok[b+k])
            r=R[off[a+k]//seg]; r[0]+=1; r[1]+=eq; tot[0]+=1; tot[1]+=eq
    m=co.metrics(otok,ctok,n,27400)
    if not quiet:
        for k in sorted(R): print(f'{k*seg:#07x} matched {R[k][0]:4d} reg-agree {R[k][1]/R[k][0]:.3f}')
    print(f'{path}: ratio {m["ratio"]} abs {m["abs_ratio"]} structural(reg+frame masked) {sm.ratio():.5f} matched {tot[0]} reg-agree {tot[1]} ({tot[1]/tot[0]:.4f})')
if __name__=='__main__':
    for p in sys.argv[1:]: run(p,quiet=len(sys.argv)>2)
