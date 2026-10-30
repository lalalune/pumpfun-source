#!/usr/bin/env python3
"""brw.py <raw.ll> <outdir> <tag> <line:a:b>... : apply branch weights a:b to validate raw-IR lines (absolute line numbers), opt+xo+tsites"""
import sys,os,subprocess
src,od,tag=sys.argv[1:4]; ed=sys.argv[4:]
T=os.path.dirname(os.path.abspath(__file__)); OPT=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/rust/lib/rustlib/aarch64-apple-darwin/bin/opt')
L=open(src).read().split('\n'); d=f'{od}/{tag}'; os.makedirs(d,exist_ok=True)
for k,e in enumerate(ed):
    n,a,b=map(int,e.split(':'))
    if 'switch' in L[n]:
        m=n
        while L[m].strip()!=']': m+=1
        L[m]=L[m].rstrip()+f', !prof !9998{k}'; L.append(f'!9998{k} = !{{!"branch_weights", i32 0, i32 {a}, i32 {b}}}')
    else:
        L[n]=L[n].rstrip()+f', !prof !9998{k}'; L.append(f'!9998{k} = !{{!"branch_weights", i32 {a}, i32 {b}}}')
open(d+'/in.ll','w').write('\n'.join(L))
subprocess.run([OPT,'-O3',d+'/in.ll','-o',d+'/opt.bc'],capture_output=True)
r=subprocess.run([T+'/xo.sh',d+'/opt.bc',d],capture_output=True,text=True).stdout.strip()
subprocess.run([os.path.dirname(OPT)+'/llvm-dis',d+'/ex.bc','-o',d+'/ex.ll'])
ts=subprocess.run(['python3',T+'/tsites.py',d],capture_output=True,text=True).stdout.split(':',1)[-1].strip()
for f in ('in.ll','opt.bc'): os.remove(f'{d}/{f}')
print(tag,' '.join(ed),'|',r,'|',ts)
