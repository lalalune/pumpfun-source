import sys,difflib,subprocess,re
sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import ctoracle as co
otok,w=co.orig_tokens()
import tokio as _rd
ctok=_rd.toks(sys.argv[1]); n=sum(len(t) for t in ctok)
lo,hi=int(sys.argv[2],16),int(sys.argv[3],16)
# usage: side2.py <cand.so|fn.bin> <lo> <hi> <cand.dis> <orig.dis>  (offsets relative to 0x22a10; .dis = 'addr  insn' lines, e.g. from objdis.sh / win.py orig)
Cd=open(sys.argv[4]).read().splitlines()
O=open(sys.argv[5]).read().splitlines()
def mreg(t):
    b=bytearray(t); d=b[1]&15; s=b[1]>>4
    if d!=10: d=0
    if s!=10 and b[0]!=0x85: s=0
    b[1]=(s<<4)|d; return bytes(b)
f=lambda t: co.abstract(mreg(t))
sm=difflib.SequenceMatcher(None,[f(t) for t in otok],[f(t) for t in ctok],autojunk=False)
off=[];o=0
for t in otok: off.append(o); o+=len(t)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if off[i1-1 if i2==i1 else i1] < lo or (i1<len(off) and off[i1]>=hi): continue
    for k in range(max(i2-i1,j2-j1)):
        a=O[i1+k] if i1+k<i2 else ''; b=Cd[j1+k] if j1+k<j2 else ''
        mark=' ' if tag=='equal' else tag[0]
        if tag=='equal' and co.abstract(otok[i1+k])!=co.abstract(ctok[j1+k]): mark='R'
        print(f'{mark} {a:48s} | {b}')
