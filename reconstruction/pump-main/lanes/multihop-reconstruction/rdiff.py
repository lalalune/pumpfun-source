# rdiff.py HARNESS cand.so olo ohi clo chi : text diff of two ranges (regs kept, offsets masked)
import sys,re,difflib
H=sys.argv[1]; sys.path.insert(0,H); a=sys.argv[2:]; sys.argv=sys.argv[:1]
import win, coords, score
from pathlib import Path
p=Path(a[0]); st,n,_=next(f for f in score.candidate_functions(p) if '8swap_hop17h' in f[2])
co=win.objdump_text(p,st,st+n); oo=win.objdump_text(coords.BASE/'original.so',0x5b3b0,0x5b3b0+18584)
def rng(d,base,lo,hi): return [(k-base,re.sub(r'<.*>','',v).strip()) for k,v in sorted(d.items()) if lo<=k-base<hi]
O=rng(oo,0x5b3b0,int(a[1],16),int(a[2],16)); C=rng(co,st,int(a[3],16),int(a[4],16))
def m(t): return re.sub(r'0x[0-9a-f]+','#',t)
sm=difflib.SequenceMatcher(None,[m(x[1]) for x in O],[m(x[1]) for x in C],autojunk=False)
for op,a1,a2,b1,b2 in sm.get_opcodes():
    for i in range(max(a2-a1,b2-b1)):
        L=O[a1+i] if a1+i<a2 else (0,''); R=C[b1+i] if b1+i<b2 else (0,'')
        tag=' ' if op=='equal' else op[0]
        print(f"{tag} {hex(L[0]) if L[1] else '':>7} {L[1]:34} | {hex(R[0]) if R[1] else '':>7} {R[1]}")
