import sys,os,struct,difflib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),"../../w12a02-cto-iroracle/scripts"))
import tail, ctoracle as co
def spillmask(t):
    b=bytearray(t); op=b[0]; dst=b[1]&15; src=b[1]>>4; cls=op&7
    off=struct.unpack_from('<h',b,2)[0]
    if ((cls==1 and src==10) or (cls in (2,3) and dst==10)) and off<=-0x8d0: b[2:4]=b'\0\0'
    return bytes(b)
p=sys.argv[1]; lo=int(sys.argv[2],16); hi=int(sys.argv[3],16)
OT=tail.OT; OFF=tail.OFF; ct=tail.toks(p)
for name,f in (('spill',spillmask),('spill+reg',lambda t: spillmask(tail.regmask(t)))):
    c=list(ct); sm=difflib.SequenceMatcher(None,[f(t) for t in OT],[f(t) for t in c],autojunk=False)
    for a,b,s in sm.get_matching_blocks():
        for k in range(s):
            if lo<=OFF[a+k]<hi: c[b+k]=OT[a+k]
    print(p,hex(lo),hex(hi),name,co.metrics(OT,c,sum(len(t) for t in c),27400)['ratio'])
