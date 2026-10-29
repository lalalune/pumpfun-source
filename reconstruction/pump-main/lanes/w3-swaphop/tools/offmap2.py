# offmap.py obj : align orig vs ours on (op,regs), pair r10 offsets of matched insns
import sys,difflib,collections,subprocess
H='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/restore/reconstruction/harness'
sys.path.insert(0,H); a=sys.argv[1:]; sys.argv=sys.argv[:1]
import score
W={x['start']:x for x in score.original_windows()}
def ins(raw):
    i=0;r=[]
    while i<len(raw):
        k=16 if raw[i]==0x18 else 8; t=raw[i:i+k]; op=t[0]; regs=t[1]; dst=regs&15; src=regs>>4
        off=int.from_bytes(t[2:4],'little',signed=True); imm=int.from_bytes(t[4:8],'little',signed=True)
        cls=op&7; so=None
        if (cls==1 and src==10) or (cls in (2,3) and dst==10): so=off
        if op==0x07 and dst!=10: pass
        r.append((i,op,regs,so,imm)); i+=k
    # mov rX,r10; add rX,-imm : address-of
    for j in range(len(r)-1):
        i0,op,regs,so,imm=r[j]
        if op==0xbf and (regs>>4)==10:
            i1,op1,regs1,so1,imm1=r[j+1]
            if op1==0x07 and (regs1&15)==(regs&15): r[j+1]=(i1,op1,regs1,('A',imm1),imm1)
    return r
from pathlib import Path
def body(p):
    if p.endswith('.bin'): return open(p,'rb').read()
    pp=Path(p); blob=pp.read_bytes(); cs=score.sections(blob)
    st,n,_=next(f for f in score.candidate_functions(pp) if '8swap_hop17h' in f[2]); return score.body(blob,cs,st,n)
o=ins(W[0x5b3b0]['raw']); c=ins(body(a[0]))
sm=difflib.SequenceMatcher(None,[(x[1],x[2]) for x in o],[(x[1],x[2]) for x in c],autojunk=False)
pairs=collections.Counter()
for op,i1,i2,j1,j2 in sm.get_opcodes():
    if op!='equal': continue
    for k in range(i2-i1):
        x=o[i1+k]; y=c[j1+k]
        if x[3] is not None and y[3] is not None:
            ox=x[3][1] if isinstance(x[3],tuple) else x[3]; oy=y[3][1] if isinstance(y[3],tuple) else y[3]
            pairs[(ox,oy)]+=1
# for each orig offset, best ours
by=collections.defaultdict(collections.Counter)
for (ox,oy),n in pairs.items(): by[ox][oy]+=n
rows=[]
for ox in sorted(by):
    oy,n=by[ox].most_common(1)[0]; tot=sum(by[ox].values())
    rows.append((ox,oy,n,tot))
for ox,oy,n,tot in rows: print(f"{-ox:#7x} -> {-oy:#7x}  delta {oy-ox:+6d}  {n}/{tot}")
