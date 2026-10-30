#!/usr/bin/env python3
"""brscan.py <raw.ll> <outdir> : for each conditional br in validate's raw IR, add 3:5 / 5:3 branch weights; opt -O3 + xo + tsites"""
import sys,re,os,subprocess,concurrent.futures as cf
src,od=sys.argv[1:3]; os.makedirs(od,exist_ok=True)
T=os.path.dirname(os.path.abspath(__file__))
OPT=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/rust/lib/rustlib/aarch64-apple-darwin/bin/opt')
L=open(src).read().split('\n')
s=next(i for i,l in enumerate(L) if l.startswith('define') and 'admin_cto8validate' in l)
e=next(i for i in range(s,len(L)) if L[i]=='}')
brs=[i for i in range(s,e) if re.match(r'\s+br i1 %[\w.]+, label %[\w.]+, label %[\w.]+\s*$',L[i])]
def ctx(i):
    b=i
    while b>s and not re.match(r'^[\w.\-]+:',L[b]): b-=1
    return L[b].split(':')[0]
def run(job):
    i,w=job; tag=f'b{i}_{w}'; d=f'{od}/{tag}'; os.makedirs(d,exist_ok=True)
    M=L[:]; M[i]=M[i].rstrip()+(', !prof !99990' if w=='35' else ', !prof !99991')
    M.append('!99990 = !{!"branch_weights", i32 3, i32 5}'); M.append('!99991 = !{!"branch_weights", i32 5, i32 3}')
    open(d+'/in.ll','w').write('\n'.join(M))
    subprocess.run([OPT,'-O3',d+'/in.ll','-o',d+'/opt.bc'],capture_output=True)
    r=subprocess.run([T+'/xo.sh',d+'/opt.bc',d],capture_output=True,text=True).stdout.strip()
    subprocess.run([os.path.dirname(OPT)+'/llvm-dis',d+'/ex.bc','-o',d+'/ex.ll'])
    ts=subprocess.run(['python3',T+'/tsites.py',d],capture_output=True,text=True).stdout.split(':',1)[-1].strip()
    for f in ('in.ll','opt.bc','ex.bc','ex.ll'):
        try: os.remove(f'{d}/{f}')
        except FileNotFoundError: pass
    return tag,ctx(i),L[i].strip(),r,ts
jobs=[(i,w) for i in brs for w in ('35','53')]
print(len(brs),'branches',flush=True)
with cf.ThreadPoolExecutor(int(os.environ.get('J','5'))) as ex:
    for tag,c,b,r,ts in ex.map(run,jobs): print(tag,c,b[:60],'|',r,'|',ts,flush=True)
