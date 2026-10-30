#!/usr/bin/env python3
"""prof.py <fn.bin|unstripped.so> [step]: per-orig-region matched count and median cand-orig byte offset (tokens = opcode+regs only)."""
import sys,os,difflib,statistics
sys.argv_s=sys.argv[:]; sys.argv=['x','n']
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'rx.py')).read().split('OUT=os.environ')[0])
p=sys.argv_s[1]; step=int(sys.argv_s[2],16) if len(sys.argv_s)>2 else 0x400
cand=open(p,'rb').read() if p.endswith('.bin') else elf_fn(p,KEEP)
def toks(raw):
    o=[];off=[];i=0
    while i<len(raw):
        n=16 if raw[i]==0x18 else 8; o.append(raw[i:i+2]); off.append(i); i+=n
    return o,off
O,oo=toks(orig_window()); Cc,co=toks(cand)
sm=difflib.SequenceMatcher(None,O,Cc,autojunk=False)
reg={}
for b in sm.get_matching_blocks():
    for k in range(b.size): reg.setdefault(oo[b.a+k]//step,[]).append(co[b.b+k]-oo[b.a+k])
print('len',len(cand))
for r in sorted(reg): print('%05x n=%4d med=%+5d'%(r*step,len(reg[r]),statistics.median(reg[r])))
