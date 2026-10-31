#!/usr/bin/env python3
"""jwhy.py <fn.bin> <+|-><hexpos> [...]: apply pure shift.py edits (+8 at block start / -8 delete insn at cand offset)
and list the jumps whose matched status changes (src cand off -> dst cand off, offset before/after)."""
import sys,os,struct,difflib,bisect
T=os.path.dirname(os.path.abspath(__file__))
sa=sys.argv[:]; sys.argv=['x','n']
src=open(T+'/shift.py').read().split("if __name__=='__main__':")[0]
sys.argv=['x',sa[1]]; g={'__file__':T+'/shift.py'}; exec(src,g)
ins,slot,build,mask,OT=g['ins'],g['slot'],g['build'],g['mask'],g['OT']
def idx_of(off): k=bisect.bisect_left(slot,off//8); assert slot[k]*8==off,hex(off); return k
add=dele=None
for a in sa[2:]:
    k=idx_of(int(a[1:],16))
    if a[0]=='+': add=k
    else: dele=k
def matched(c):
    toks=mask(c); sm=difflib.SequenceMatcher(None,OT,toks,autojunk=False); s=set()
    for b in sm.get_matching_blocks():
        for k in range(b.size): s.add(b.b+k)
    return toks,s
c0=build(); c1=build(add,dele)
t0,m0=matched(c0); t1,m1=matched(c1)
# map insn index in c0 to c1 token index
def tokidx_map():
    mp={}; j=0
    for k in range(len(ins)):
        if dele is not None and k==dele: continue
        if add is not None and k==add: j+=1
        mp[k]=j; j+=1
    return mp
mp=tokidx_map(); print('M',len(m0),'->',len(m1))
for k,b in enumerate(ins):
    if k not in mp: continue
    a0=k in m0; a1=mp[k] in m1
    if a0!=a1:
        off=struct.unpack('<h',bytes(b[2:4]))[0]; isj=(b[0]&7) in (5,6) and b[0] not in (0x85,0x95)
        dst=(slot[k]+len(b)//8+off)*8 if isj else None
        print(('GAIN' if a1 else 'LOSS'),'%05x'%(slot[k]*8),'jump->%05x'%dst if isj else 'insn %02x'%b[0])
