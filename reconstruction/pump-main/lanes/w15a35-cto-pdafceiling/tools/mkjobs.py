#!/usr/bin/env python3
"""mkjobs.py <m.ll> <out.jsonl> [ops=top,bot,casc] [ralog]: run the private RAPRIO llc once with RAPRIO_LOG, take every
queued vreg (Q lines; first-enqueue order) and write one greedy single per vreg x op (w15a18 job format)."""
import sys,os,subprocess,json,tempfile
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w15a35-cto-pdafceiling')
m,of=sys.argv[1],sys.argv[2]; ops=(sys.argv[3] if len(sys.argv)>3 else 'top,bot,casc').split(',')
log=sys.argv[4] if len(sys.argv)>4 else of+'.ralog'
if os.path.exists(log): os.remove(log)
env=dict(os.environ); [env.pop(k) for k in list(env) if k.startswith('RAPRIO_')]; env['RAPRIO_LOG']=log
d=tempfile.mkdtemp(dir=O+'/tmp')
subprocess.run([O+'/llvmb/bin/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',m,
                '-stop-before=stack-slot-coloring','-o',d+'/pre.mir'],env=env,check=True)
seen=[]; S=set()
for l in open(log):
    if l.startswith('Q '):
        v=int(l.split()[1])
        if v not in S: S.add(v); seen.append(v)
with open(of,'w') as f:
    for v in seen:
        for op in ops:
            if op=='top': j={'name':f'top_{v}','v':v,'prio':f'{v}=0xfffffff0'}
            elif op=='bot': j={'name':f'bot_{v}','v':v,'prio':f'{v}=1'}
            elif op=='casc': j={'name':f'casc_{v}','v':v,'casc':f'{v}=0x7ffffff0'}
            elif op=='w10': j={'name':f'w10_{v}','v':v,'weight':f'{v}=*10'}
            elif op=='w01': j={'name':f'w01_{v}','v':v,'weight':f'{v}=*0.1'}
            f.write(json.dumps(j)+'\n')
print(len(seen),'vregs',len(seen)*len(ops),'jobs')
