#!/usr/bin/env python3
"""slotmap.py <fn.bin|so> <cand.dis> <orig.dis>: align orig/candidate with registers and frame masked, then map each
original spill slot (r10-0x8d0 and below) to the candidate slots used at the aligned instructions. Prints per original
slot: the candidate slot(s), the delta, and the first original address."""
import sys,re,difflib,collections
sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import ctoracle as co, tokio
otok,_=co.orig_tokens(); ctok=tokio.toks(sys.argv[1])
Cd=open(sys.argv[2]).read().splitlines(); O=open(sys.argv[3]).read().splitlines()
def mreg(t):
    b=bytearray(t); d=b[1]&15; s=b[1]>>4
    if d!=10: d=0
    if s!=10 and b[0]!=0x85: s=0
    b[1]=(s<<4)|d; return bytes(b)
f=lambda t: co.abstract(mreg(t))
sm=difflib.SequenceMatcher(None,[f(t) for t in otok],[f(t) for t in ctok],autojunk=False)
M=collections.defaultdict(collections.Counter); first={}
for a,b,n in sm.get_matching_blocks():
    for k in range(n):
        mo=re.search(r'\[r10 - (0x[0-9a-f]+)\]',O[a+k]); mc=re.search(r'\[r10 - (0x[0-9a-f]+)\]',Cd[b+k])
        if mo and mc and int(mo.group(1),16)>=0x8d0:
            M[mo.group(1)][mc.group(1)]+=1; first.setdefault(mo.group(1),O[a+k].split()[0])
for s in sorted(M,key=lambda x:int(x,16)):
    c=M[s].most_common(3); d=int(c[0][0],16)-int(s,16)
    print(f'{s} first {first[s]}  ->', ' '.join(f'{k}x{v}' for k,v in c), f' delta {d:+#x}' if d else '  same')
