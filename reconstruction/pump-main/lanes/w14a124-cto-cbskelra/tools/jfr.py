import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled
from segcmp import fm,rm,jm
O=oracle.orig_window(); om=oracle.mask(O)
def M(a,b): return sum(k.size for k in difflib.SequenceMatcher(None,a,b,autojunk=False).get_matching_blocks())
for p in sys.argv[1:]:
    c=oracle.mask(xled.load(p if (p=='main' or '.' in p) else f'{os.path.dirname(T)}/rx/{p}/fn.bin'))
    print(f'{os.path.basename(p):14s} M {M(om,c)} jM {M(jm(om),jm(c))} fM {M(fm(om),fm(c))} rM {M(rm(om),rm(c))} fjM {M(jm(fm(om)),jm(fm(c)))} rjM {M(jm(rm(om)),jm(rm(c)))}')
