#!/usr/bin/env python3
"""fbrange.py fn.bin LO HI: framebound restricted to our offsets in [LO,HI] (hex); also lists remapped offsets that differ."""
import sys,os,difflib,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import framebound as fb, ctoracle
raw=open(sys.argv[1],'rb').read(); ctok=[]; i=0
while i<len(raw):
    n=16 if raw[i]==0x18 else 8; ctok.append(raw[i:i+n]); i+=n
lo,hi=int(sys.argv[2],16),int(sys.argv[3],16)
otok,w=ctoracle.orig_tokens()
oa=[ctoracle.abstract(t) for t in otok]; ca=[ctoracle.abstract(t) for t in ctok]
sm=difflib.SequenceMatcher(None,oa,ca,autojunk=False)
votes=collections.defaultdict(collections.Counter)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag!='equal': continue
    for k in range(i2-i1):
        fo=fb.frame_off(otok[i1+k],otok[i1+k-1] if i1+k else None); fc=fb.frame_off(ctok[j1+k],ctok[j1+k-1] if j1+k else None)
        if fo and fc and fo[0]==fc[0]: votes[-fc[1]][-fo[1]]+=1
remap={c:v.most_common(1)[0][0] for c,v in votes.items() if lo<=c<=hi}
new=[]
for j,t in enumerate(ctok):
    fc=fb.frame_off(t,ctok[j-1] if j else None)
    if fc and -fc[1] in remap: t=fb.setoff(t,fc[0],-remap[-fc[1]])
    new.append(t)
r0=difflib.SequenceMatcher(None,otok,ctok,autojunk=False).ratio(); r1=difflib.SequenceMatcher(None,otok,new,autojunk=False).ratio()
print(f'{r0:.5f} -> {r1:.5f}  ({len(remap)} offsets)')
for c in sorted(remap):
    if remap[c]!=c: print(f'  {c:#x} -> {remap[c]:#x}  votes {dict(votes[c].most_common(3))}')
