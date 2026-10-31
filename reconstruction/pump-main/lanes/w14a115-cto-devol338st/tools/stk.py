#!/usr/bin/env python3
"""stk.py: post-opt store-kind screen on rx/x_hr_fcF/m.ll (bb65.i store). llc only."""
import sys,os,subprocess,json
sys.path.insert(0,os.path.dirname(__file__)); import oracle
O=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
M=open(O+'/rx/x_hr_fcF/m.ll').read()
S='  store i8 0, ptr %44, align 1, !alias.scope !8547, !noalias !8600\n'
assert M.count(S)==1
K={}
for v in (0,1):
    for g,off in (('%38',40),('%39',41),('%40',42),('%41',43),('%43',44),('%44',45)):
        K[f'b{off}_{v}']=f'  store i8 {v}, ptr {g}, align 1\n'
for v in (0,1,2,100,10000):
    K[f'q32_{v}']=f'  store i64 {v}, ptr %37, align 8\n'
for k,s in K.items():
    d=O+'/rx/stk_'+k; os.makedirs(d,exist_ok=True)
    open(d+'/m.ll','w').write(M.replace(S,s))
    r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
    if r.returncode: print(k,r.stderr[-300:]); continue
    c=oracle.elf_fn(d+'/m.o',oracle.KEEP); rr,sd=oracle.metric(c,oracle.orig_window())
    print(json.dumps({'k':k,'ratio':round(rr,5),'bytes':len(c),'slots':sd}),flush=True)
