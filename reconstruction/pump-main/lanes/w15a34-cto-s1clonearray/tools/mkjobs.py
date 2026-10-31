#!/usr/bin/env python3
"""mkjobs.py <m.ll> <jobs.jsonl> [ops] : run private llc with RAPRIO_LOG on m.ll, write single-override jobs for every queued vreg.
ops: comma list of top,bot,casc,w3 (default top,bot,casc)."""
import sys,os,subprocess,json,tempfile
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a34-cto-s1clonearray'
L='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a18-cto-s1greedy/llvmb/bin/llc'
m,jf=sys.argv[1:3]; ops=(sys.argv[3] if len(sys.argv)>3 else 'top,bot,casc').split(',')
d=tempfile.mkdtemp(dir=O+'/tmp'); log=d+'/ra.log'
env=dict(os.environ); env['RAPRIO_LOG']=log
subprocess.run([L,'-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',m,'-stop-after=greedy','-o',d+'/post.mir'],env=env,check=True,capture_output=True)
seen=[]; S=set()
for l in open(log):
    f=l.split()
    if f and f[0]=='Q':
        v=int(f[1])
        if v not in S: S.add(v); seen.append(v)
with open(jf,'w') as f:
    for v in seen:
        for op in ops:
            if op=='top': j={'name':f'top_{v}','v':v,'prio':f'{v}=0xfffffff0'}
            elif op=='bot': j={'name':f'bot_{v}','v':v,'prio':f'{v}=1'}
            elif op=='casc': j={'name':f'casc_{v}','v':v,'casc':f'{v}=0x7ffffff0'}
            elif op=='w3': j={'name':f'w3_{v}','v':v,'weight':f'{v}=*3'}
            f.write(json.dumps(j)+'\n')
print(len(seen),'vregs',len(seen)*len(ops),'jobs')
import shutil; shutil.rmtree(d)
