"""regdelta.py <fnA.bin|so> <fnB.bin|so> [seg]: per original region, matched tokens (plain metric) for A and B."""
import sys,difflib,collections
sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import ctoracle as co
from pathlib import Path
def toks(p):
    if p.endswith('.so'): return co.so_tokens(p)[0]
    raw=Path(p).read_bytes(); out=[];i=0
    while i<len(raw):
        n=16 if raw[i]==0x18 else 8; out.append(raw[i:i+n]); i+=n
    return out
otok,w=co.orig_tokens(); off=[];o=0
for t in otok: off.append(o); o+=len(t)
seg=int(sys.argv[3],16) if len(sys.argv)>3 else 0x400
res=[]
for p in sys.argv[1:3]:
    sm=difflib.SequenceMatcher(None,otok,toks(p),autojunk=False); R=collections.Counter()
    for a,b,sz in sm.get_matching_blocks():
        for k in range(sz): R[off[a+k]//seg]+=1
    res.append(R)
for k in sorted(set(res[0])|set(res[1])):
    d=res[1][k]-res[0][k]
    if d: print(f'{k*seg:#07x} {res[0][k]:4d} -> {res[1][k]:4d} ({d:+d})')
