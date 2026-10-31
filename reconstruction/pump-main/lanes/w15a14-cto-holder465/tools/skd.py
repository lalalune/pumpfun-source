import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled
O=oracle.orig_window(); ot,oo=xled.toks(O); of=xled.fmask(ot)
def hits(p):
    C=open(p,'rb').read(); ct,co=xled.toks(C); cf=xled.fmask(ct); h={}
    for bl in difflib.SequenceMatcher(None,of,cf,autojunk=False).get_matching_blocks():
        for k in range(bl.size): h[bl.a+k]=co[bl.b+k]
    return h
a=hits(sys.argv[1]); b=hits(sys.argv[2]); lo,hi=int(sys.argv[3],0),int(sys.argv[4],0)
runs=[];cur=None
for i in range(len(ot)):
    if not(lo<=oo[i]<hi): continue
    s=(i in a, i in b)
    if s[0]!=s[1]:
        print(f"orig {oo[i]:#06x} a {'hit '+hex(a[i]) if i in a else 'miss':12s} b {'hit '+hex(b[i]) if i in b else 'miss'}")
