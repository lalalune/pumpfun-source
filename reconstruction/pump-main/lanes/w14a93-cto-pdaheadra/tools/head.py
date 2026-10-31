#!/usr/bin/env python3
"""head.py <m.ll> <tag> [--force F]: head RA summary. Private llc with RAPRIO_LOG; reports who evicts %0 (accounts ptr) from R8
and when, the final registers of the head values (arg copies, %0, sharing ptr [%0+144], curve ptr [%0+56], first MOV_ri 0 phi),
colmap total misses, ratio/L1/L2 and per-0x800 region L0/L1/L2. Experiment only."""
import sys,os,re,subprocess,json
T=os.path.dirname(os.path.abspath(__file__)); O=os.path.dirname(T)
a=sys.argv[1:]; m,tag=a[0],a[1]; force=a[a.index('--force')+1] if '--force' in a else ''
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
A=['-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections']
os.makedirs(O+'/cm',exist_ok=True); pre=O+'/cm/'+tag
subprocess.run([SDK+'/llc',*A,m,'-stop-before=greedy','-o',pre+'.pre.mir'],check=True)
cm=subprocess.run(['python3',T+'/colmap.py',m,pre]+(['--force',force] if force else []),capture_output=True,text=True).stdout.split('\n')[0]
mir=open(pre+'.pre.mir').read(); body=mir[mir.index('\nbody:'):]
names={}
for l in body.split('\n'):
    mm=re.match(r'\s*%(\d+):gpr = COPY \$r(\d)$',l)
    if mm: names.setdefault(int(mm.group(1)),'arg_r'+mm.group(2))
    mm=re.match(r'\s*%(\d+):gpr = LDD_V1 %0, (144|56|8|16) ',l)
    if mm:
        nm={'144':'sharing','56':'curve','8':'global','16':'mintai'}[mm.group(2)]+'@%0'
        if nm not in names.values(): names.setdefault(int(mm.group(1)),nm)
    mm=re.match(r'\s*%(\d+):gpr = MOV_ri 0$',l)
    if mm and 'phi0' not in names.values(): names[int(mm.group(1))]='phi0'
names[0]='acc%0'
log=open(pre+'.ra.log').read().split('\n')
fin={}; ev=[]; step={}
for l in log:
    f=l.split()
    if not f: continue
    if f[0]=='A': fin[int(f[1])]=f[2]
    if f[0]=='D': step[int(f[2])]=step.get(int(f[2]),int(f[1]))
    if f[0]=='E': ev.append((int(f[1]),f[3],int(f[5])))
e0=[(r,b) for v,r,b in ev if v==0]
out={'tag':tag,'cm':cm.split(';')[-1].strip() if cm else '', 'acc_evict':[(r,b,names.get(b,'?')) for r,b in e0][:3],
     'head':{n:(v,fin.get(v),step.get(v)) for v,n in sorted(names.items())}}
r=subprocess.run(['python3',T+'/regceil.py',pre+'.bin'],capture_output=True,text=True).stdout.strip().split('plain/regonly/L1/L2')[-1]
out['plain/reg/L1/L2']=r.strip()
print(json.dumps(out))
print(tag,subprocess.run(['python3',T+'/reg8.py',pre+'.bin'],capture_output=True,text=True).stdout.strip())
