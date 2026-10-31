import sys,os,difflib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import oracle,xled
O=oracle.orig_window(); ot=oracle.mask(O)
def fm(t):
    out=[]
    for x in t:
        x=bytearray(x); op=x[0]; cl=op&7
        if (cl==1 and (x[1]>>4)==10) or (cl in (2,3) and (x[1]&15)==10): x[2:4]=b'\0\0'
        if op==0x07: x[4:8]=b'\0'*4
        out.append(bytes(x))
    return out
def rm(t): return [bytes([x[0],0])+x[2:] for x in t]
def jm(t): return [x[:2]+b'\0\0'+x[4:] if (x[0]&7) in (5,6) and x[0] not in (0x85,0x95) else x for x in t]
def M(a,b): return sum(k.size for k in difflib.SequenceMatcher(None,a,b,autojunk=False).get_matching_blocks())
for p in sys.argv[1:]:
    q=p if (p=='main' or '.' in p) else f'{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/rx/{p}/fn.bin'
    c=oracle.mask(xled.load(q))
    print(f'{p:14s} B {sum(len(x) for x in c)} M {M(ot,c)} fM {M(fm(ot),fm(c))} rM {M(rm(ot),rm(c))} rfM {M(rm(fm(ot)),rm(fm(c)))} rfjM {M(jm(rm(fm(ot))),jm(rm(fm(c))))}')
