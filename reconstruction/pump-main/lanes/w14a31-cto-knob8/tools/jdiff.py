#!/usr/bin/env python3
"""jdiff.py <name|MAIN> [step]: jumps aligned under jump-masked matching whose raw offsets differ; histogram by (src region, dst region, delta bytes)."""
import sys,os,difflib,struct,collections
sa=sys.argv[:]; sys.argv=['x','n']
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'rx.py')).read().split('OUT=os.environ')[0])
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a31-cto-knob8')
step=int(sa[2],16) if len(sa)>2 else 0x800
def toks(raw):
    t=mask(raw); off=[];i=0
    for x in t: off.append(i); i+=len(x)
    return t,off
def jmk(t):
    out=[]
    for x in t:
        op=x[0]
        if (op&7) in (5,6) and op not in (0x85,0x95): x=x[:2]+b'\0\0'+x[4:]
        out.append(x)
    return out
n=sa[1]
raw=elf_fn(os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so'),KEEP) if n=='MAIN' else open(f'{O}/rx/{n}/fn.bin','rb').read()
ot,oo=toks(orig_window()); ct,co=toks(raw)
sm=difflib.SequenceMatcher(None,jmk(ot),jmk(ct),autojunk=False)
H=collections.Counter(); tot=0
for b in sm.get_matching_blocks():
    for k in range(b.size):
        x=ot[b.a+k]; y=ct[b.b+k]
        if x!=y:
            ox=struct.unpack('<h',x[2:4])[0]; oy=struct.unpack('<h',y[2:4])[0]
            src=oo[b.a+k]; dst=src+8+ox*8
            H[(src//step*step,dst//step*step,(oy-ox)*8)]+=1; tot+=1
print(n,'jump mismatches',tot)
for (s,d,dl),c in sorted(H.items(),key=lambda z:-z[1])[:40]: print('src %05x dst %05x delta %+5d  x%d'%(s,d,dl,c))
