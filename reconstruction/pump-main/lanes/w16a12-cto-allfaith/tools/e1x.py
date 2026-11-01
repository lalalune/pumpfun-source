#!/usr/bin/env python3
"""e1x.py <src rx name> <dst rx name> [hc|e1]: apply w14a142's per-arm holder-flag IR edits (hphi + hcs [+ hev]) to a
captured post-opt module rx/<src>/m.ll and score it like rx.py (SDK llc, oracle metric, eq_main). Experiment only: these are
post-opt IR edits (oracle bounds), not source. hphi = per-arm phi of constants at validate's exits; hcs = the curve store
reads it; hev = the event's is_holder_reward reads the holder argument (keeps %0 live past the curve store)."""
import sys,os,re,json,subprocess
T=os.path.dirname(os.path.abspath(__file__)); O=os.path.dirname(T); sys.path.insert(0,T)
import oracle
src,dst=sys.argv[1],sys.argv[2]; mode=sys.argv[3] if len(sys.argv)>3 else 'e1'
t=open(f'{O}/rx/{src}/m.ll').read()
def one(t,a,b):
    c=t.count(a); assert c==1,(c,a[:80]); return t.replace(a,b)
A54="bb54.i:                                           ; preds = %bb95.i, %bb52.i\n"
A75="bb75:                                             ; preds = %bb65.i, %bb44.i, %bb45.i\n"
t=one(t,A54,A54+"  %hph54 = phi i1 [ false, %bb52.i ], [ true, %bb95.i ]\n")
t=one(t,A75,A75+"  %hph = phi i1 [ false, %bb45.i ], [ %hph54, %bb65.i ], [ true, %bb44.i ]\n")
m=re.findall(r'\n  (%\d+) = and i8 %0, 1\n',t); assert len(m)==1,m
t=t.replace(f'\n  {m[0]} = and i8 %0, 1\n',f'\n  {m[0]} = zext i1 %hph to i8\n')
if mode=='e1':
    pat=re.compile(r'(  (%\d+) = getelementptr inbounds i8, ptr %_?\w+, i64 165\n  (%\d+) = )load i8, ptr \2, align 1, !range !\d+, !noundef !\d+(\n  call void @llvm\.lifetime\.start\.p0\(i64 48)')
    ms=pat.findall(t); assert len(ms)==1,len(ms)
    t=pat.sub(lambda x: x.group(1)+'and i8 %0, 1'+x.group(4),t)
d=f'{O}/rx/{dst}'; os.makedirs(d,exist_ok=True); open(d+'/m.ll','w').write(t)
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
if r.returncode: print(r.stderr[-2000:]); sys.exit(1)
cand=oracle.elf_fn(d+'/m.o',oracle.KEEP); open(d+'/fn.bin','wb').write(cand); os.remove(d+'/m.o')
orig=oracle.orig_window(); rr,sd=oracle.metric(cand,orig)
res={'name':dst,'ratio':round(rr,5),'bytes':len(cand),'slots_diff':sd}
bs=os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so')
res['eq_main']=oracle.mask(oracle.elf_fn(bs,oracle.KEEP))==oracle.mask(cand)
import difflib
Om=oracle.mask(orig); res['M']=sum(b.size for b in difflib.SequenceMatcher(None,Om,oracle.mask(cand),autojunk=False).get_matching_blocks())
print(json.dumps(res)); open(d+'/res.json','w').write(json.dumps(res))
