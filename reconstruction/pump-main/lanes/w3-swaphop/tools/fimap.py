# fimap.py cand.so|cand.o.bin sh.mir : per our frame object, the orig object base it maps to (via opregs alignment)
import sys,difflib,collections,re
sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/restore/reconstruction/harness')
a=sys.argv[1:]; sys.argv=sys.argv[:1]
import score
from pathlib import Path
W={x['start']:x for x in score.original_windows()}
def body(p):
    if p.endswith('.bin'): return open(p,'rb').read()
    pp=Path(p); blob=pp.read_bytes(); cs=score.sections(blob)
    st,n,_=next(f for f in score.candidate_functions(pp) if '8swap_hop17h' in f[2]); return score.body(blob,cs,st,n)
def ins(raw):
    i=0;r=[]
    while i<len(raw):
        k=16 if raw[i]==0x18 else 8; t=raw[i:i+k]; op=t[0]; regs=t[1]; d=regs&15; s=regs>>4
        off=int.from_bytes(t[2:4],'little',signed=True); imm=int.from_bytes(t[4:8],'little',signed=True)
        cls=op&7; so=None
        if (cls==1 and s==10) or (cls in (2,3) and d==10): so=-off
        r.append([i,op,regs,so]); i+=k
    for j in range(len(r)-1):
        if r[j][1]==0xbf and (r[j][2]>>4)==10 and r[j+1][1]==0x07 and (r[j+1][2]&15)==(r[j][2]&15):
            raw_i=r[j+1][0]
    return r
def ins2(raw):
    r=ins(raw); i=0
    for j in range(len(r)-1):
        if r[j][1]==0xbf and (r[j][2]>>4)==10 and r[j+1][1]==0x07 and (r[j+1][2]&15)==(r[j][2]&15):
            off=raw[r[j+1][0]+4:r[j+1][0]+8]; r[j+1][3]=-int.from_bytes(off,'little',signed=True)
    return r
t=open(a[1]).read(); st=t[t.index('\nstack:'):]
fis=[(int(i),ty,-int(off),int(sz)) for i,ty,off,sz in re.findall(r"id: (\d+), name: [^,]*, type: ([\w-]+), offset: (-?\d+), size: (\d+)",st)]
def fi_of(X):
    for i,ty,B,s in fis:
        if B-s < X <= B: return (i,ty,B,s)
o=ins2(W[0x5b3b0]['raw']); c=ins2(body(a[0]))
sm=difflib.SequenceMatcher(None,[(x[1],x[2]) for x in o],[(x[1],x[2]) for x in c],autojunk=False)
by=collections.defaultdict(collections.Counter)
for op,i1,i2,j1,j2 in sm.get_opcodes():
    if op!='equal': continue
    for k in range(i2-i1):
        x=o[i1+k]; y=c[j1+k]
        if x[3] is None or y[3] is None or y[3]>0xf00: continue
        f=fi_of(y[3])
        if not f: continue
        fo=f[2]-y[3]; by[f][x[3]+fo]+=1
for f in sorted(by,key=lambda f:f[2]):
    mc=by[f].most_common(3); tot=sum(by[f].values())
    print(f"fi{f[0]:<4}{f[1][:5]:6} ours {f[2]:#6x}/{f[3]:<4} -> orig {mc[0][0]:#6x} ({mc[0][1]}/{tot}) delta {mc[0][0]-f[2]:+5d}  alt {[(hex(k),v) for k,v in mc[1:]]}")
