#!/usr/bin/env python3
"""mkjobs.py <m.ll> <out.jsonl> [base-prio] [base-force]: single-override screen jobs (top/bot/global-toggle priority for every
initially queued vreg; force r6-r9/spill for global ones) on top of a base override set; reads the queue from a RAPRIO_LOG run
of the private llc with the base set. Experiment only."""
import sys,os,json,subprocess,tempfile
m,of=sys.argv[1:3]; bp=sys.argv[3] if len(sys.argv)>3 else ''; bf=sys.argv[4] if len(sys.argv)>4 else ''
LLC=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a84-cto-raprio/llvmb/bin/llc')
fd,log=tempfile.mkstemp(suffix='.log'); os.close(fd); os.remove(log)
env=dict(os.environ,RAPRIO_LOG=log); 
if bp: env['RAPRIO_PRIO']=bp
if bf: env['RAPRIO_FORCE']=bf
subprocess.run([LLC,'-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',m,'-filetype=obj','-o','/dev/null'],env=env,check=True)
seen={}
for l in open(log):
    f=l.split()
    if f[0]=='Q' and f[3]=='st=1':
        v=int(f[1]); p=int(f[2][2:]); seen.setdefault(v,p)
os.remove(log)
bpv={x.split('=')[0] for x in bp.split(',') if x}; bfv={x.split('=')[0] for x in bf.split(',') if x}
def j(name,v,prio=None,force=None):
    d={'name':name,'v':v}
    P=','.join(x for x in [bp,prio] if x); F=','.join(x for x in [bf,force] if x)
    if P: d['prio']=P
    if F: d['force']=F
    return d
J=[]
for v,p in seen.items():
    if str(v) in bpv or str(v) in bfv: continue
    J.append(j(f'top{v}',v,prio=f'{v}={0xfffffff0}')); J.append(j(f'bot{v}',v,prio=f'{v}={0x80000001}')); J.append(j(f'tg{v}',v,prio=f'{v}={p^(1<<29)}'))
    if (p>>29)&1:
        for r in ('r6','r7','r8','r9','spill'): J.append(j(f'f{r}_{v}',v,force=f'{v}={r}'))
open(of,'w').write('\n'.join(json.dumps(x) for x in J)+'\n'); print(len(seen),len(J))
