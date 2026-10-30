import difflib,collections,ctoracle as co
def mreg(t):
    b=bytearray(t); d=b[1]&15; s=b[1]>>4
    if d!=10: d=0
    if s!=10 and b[0]!=0x85: s=0
    b[1]=(s<<4)|d; return bytes(b)
def segs(otok,ctok,seg):
    off=[];o=0
    for t in otok: off.append(o); o+=len(t)
    fs=[lambda t:t, mreg, co.abstract, lambda t:co.abstract(mreg(t))]
    R=collections.defaultdict(lambda:[0,0,0,0])
    for k,f in enumerate(fs):
        sm=difflib.SequenceMatcher(None,[f(t) for t in otok],[f(t) for t in ctok],autojunk=False)
        for a,b,sz in sm.get_matching_blocks():
            for j in range(sz): R[(off[a+j]//seg)*seg][k]+=1
    return R
