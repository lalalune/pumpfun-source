#!/usr/bin/env python3
# oracle.py BASE.ll NAME EDIT.py [--mir] : apply edit(t)->t, llc, report exactish/opregs/r10-offset agreement
import sys,os,subprocess,difflib,pickle,runpy,collections
B='/Users/shawwalters/Documents/Codex/2026-10-24/amm-sell-swarm/infra/sdk-native/rust/lib/rustlib/aarch64-apple-darwin/bin'
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w3-swaphop')
base,name,ed=sys.argv[1:4]; mir='--mir' in sys.argv
d=O+'/orc/'+name; os.makedirs(d,exist_ok=True)
t=open(base).read()
if ed!='-': t2=runpy.run_path(ed)['edit'](t)
else: t2=t
open(d+'/m.ll','w').write(t2)
r=subprocess.run([B+'/llc','-O3','-mtriple=sbf','-mattr=+store-imm,+jmp-ext','-relocation-model=pic','-function-sections','-data-sections','-filetype=obj',d+'/m.ll','-o',d+'/m.o'],capture_output=True,text=True)
if r.returncode: print(r.stderr[-2000:]); sys.exit(1)
if mir: subprocess.run([B+'/llc','-O3','-mtriple=sbf','-mattr=+store-imm,+jmp-ext','-relocation-model=pic','-stop-after=prologepilog',d+'/m.ll','-o',d+'/m.mir'],check=True)
secs=subprocess.run([B+'/llvm-objdump','-h',d+'/m.o'],capture_output=True,text=True).stdout
sec=next(l.split()[1] for l in secs.splitlines() if '.text.' in l and '8swap_hop17h' in l and '.rel' not in l)
subprocess.run([B+'/llvm-objcopy','-O','binary','--only-section='+sec,d+'/m.o',d+'/m.bin'],check=True)
raw=open(d+'/m.bin','rb').read()
P=O+'/ir/orig_raw.bin'
if not os.path.exists(P):
    sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/restore/reconstruction/harness'); av=sys.argv; sys.argv=av[:1]
    import score; W={x['start']:x for x in score.original_windows()}; open(P,'wb').write(W[0x5b3b0]['raw']); sys.argv=av
oraw=open(P,'rb').read()
def toks(raw):
    i=0;out=[]
    while i<len(raw):
        k=16 if raw[i]==0x18 else 8; t=raw[i:i+k]
        if t[0]==0x85: t=t[:2]
        elif t[0]==0x18: t=t[:2]
        elif t[0]&7==5 and t[0]!=0x85 and t[0]!=0x95: t=t[:2]+t[4:8]  # mask jump offsets
        out.append(t); i+=k
    return out
o=toks(oraw); c=toks(raw)
def R(f): return difflib.SequenceMatcher(None,[f(x) for x in o],[f(x) for x in c],autojunk=False).ratio()
ex=R(lambda x:x); orr=R(lambda x:x[:2])
# r10 offset agreement over opregs-aligned insns
def soff(t):
    op=t[0];regs=t[1];dd=regs&15;s=regs>>4;cl=op&7
    if (cl==1 and s==10) or (cl in(2,3) and dd==10): return int.from_bytes(t[2:4],'little',signed=True)
sm=difflib.SequenceMatcher(None,[x[:2] for x in o],[x[:2] for x in c],autojunk=False)
eq=tot=0; dl=collections.Counter()
for op,i1,i2,j1,j2 in sm.get_opcodes():
    if op!='equal': continue
    for k in range(i2-i1):
        a=soff(o[i1+k]); b=soff(c[j1+k])
        if a is not None and b is not None:
            tot+=1; eq+=(a==b); dl[b-a]+=1
print(f'{name}: bytes {len(raw)} exactish {ex:.4f} opregs {orr:.4f} offeq {eq}/{tot} top {dl.most_common(5)}')
