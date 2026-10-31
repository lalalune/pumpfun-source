#!/usr/bin/env python3
"""evx.py <m.ll> <tag> [job.json]: greedy trace of the head values (experiment only).
Runs the private RAPRIO llc (job env honoured) with RAPRIO_LOG, names the head vregs from the pre-greedy MIR
(arg copies, %0 accounts ptr, [%0+144] sharing, [%0+56] curve, [%0+8] global, first MOV_ri 0 phi) and prints:
the dequeue step / assigned register of each, every eviction of %0 and of the named values, and %0's split pieces."""
import sys,os,re,subprocess,json,tempfile
T=os.path.dirname(os.path.abspath(__file__)); O=os.path.dirname(T); LLC=O+'/llvmb/bin/llc'
A=['-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections']
m,tag=sys.argv[1],sys.argv[2]; job=json.loads(sys.argv[3]) if len(sys.argv)>3 else {}
d=O+'/cm/'+tag; os.makedirs(d,exist_ok=True)
env=dict(os.environ); [env.pop(k) for k in list(env) if k.startswith('RAPRIO_')]
for k in ('prio','force','hint','casc','weight','nohint','sticky'):
    if job.get(k): env['RAPRIO_'+k.upper()]=job[k]
log=d+'/ra.log'
if os.path.exists(log): os.remove(log)
env2=dict(env); env2['RAPRIO_LOG']=log
subprocess.run([LLC,*A,m,'-stop-before=greedy','-o',d+'/pre.mir'],check=True,env=env)
subprocess.run([LLC,*A,m,'-stop-before=stack-slot-coloring','-o',d+'/post.mir'],check=True,env=env2)
mir=open(d+'/pre.mir').read(); body=mir[mir.index('\nbody:'):]
names={0:'acc%0'}
for l in body.split('\n'):
    mm=re.match(r'\s*%(\d+):gpr = COPY \$r(\d)$',l)
    if mm: names.setdefault(int(mm.group(1)),'arg_r'+mm.group(2))
    mm=re.match(r'\s*%(\d+):gpr = LDD(?:_V1)? %0, (144|56|8|16|0) ',l)
    if mm:
        nm={'144':'sharing','56':'curve','8':'global','16':'mintai','0':'ai0'}[mm.group(2)]+'@%0'
        if nm not in names.values(): names.setdefault(int(mm.group(1)),nm)
    mm=re.match(r'\s*%(\d+):gpr = MOV_ri 0$',l)
    if mm and 'phi0' not in names.values(): names[int(mm.group(1))]='phi0'
L=[l.split() for l in open(log) if l.strip()]
step={}; reg={}; ev=[]; new={}; q={}; fin={}
for f in L:
    if f[0]=='D': step.setdefault(int(f[2]),int(f[1]))
    if f[0]=='Q': q.setdefault(int(f[1]),' '.join(f[2:]))
    if f[0]=='R':
        reg[int(f[1])]=f[3]
        if 'new:' in f: new[int(f[1])]=[int(x) for x in f[f.index('new:')+1:]]
    if f[0]=='A': fin[int(f[1])]=f[2]
    if f[0]=='E': ev.append((int(f[1]),f[3],int(f[5]),len(ev)))
print('#',tag,job.get('name',''))
for v,n in sorted(names.items(),key=lambda x:step.get(x[0],1e9)):
    print(f'  {n:12s} %{v:<5d} step {step.get(v)} -> {reg.get(v)} fin {fin.get(v)}  {q.get(v,"")}')
    for (x,r,b,i) in ev:
        if x==v: print(f'      evicted from {r} by %{b} ({names.get(b,"")}) step~{step.get(b)}')
        if b==v: print(f'      evicts %{x} ({names.get(x,"")}) from {r}')
def kids(v,depth=0):
    for c in new.get(v,[]):
        print('    '*(depth+1)+f'%{c} step {step.get(c)} -> {reg.get(c)} fin {fin.get(c)} {q.get(c,"")}'); kids(c,depth+1)
print('  %0 split tree:'); kids(0)
