#!/usr/bin/env python3
"""mp.py <name> <m.ll> [force]: stock llc (or private llc with RAPRIO_FORCE) obj + PEI MIR -> M, bytes, Mperm (spill-permutation bound, w15a08 relab)."""
import sys,os,subprocess,json
O=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,O); import relab as R
n,m=sys.argv[1],sys.argv[2]; force=sys.argv[3] if len(sys.argv)>3 else ''
d=f'{O}/d/{n}'; os.makedirs(d,exist_ok=True)
A=['-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections']
LLC=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w15a14-cto-holder465/r/llvmb/bin/llc')
env=dict(os.environ)
if force: env['RAPRIO_FORCE']=force
p1=subprocess.Popen([LLC,*A,m,'-filetype=obj','-o',d+'/f.o'],env=env,stderr=subprocess.PIPE)
p2=subprocess.Popen([LLC,*A,m,'-stop-after=prologepilog','-o',d+'/pei.mir'],env=env,stderr=subprocess.PIPE)
e1=p1.communicate()[1]; p2.communicate()
if p1.returncode: print(json.dumps({'n':n,'err':e1.decode()[-400:]})); sys.exit(1)
b=R.g['elf_fn'](d+'/f.o',R.g['KEEP']); open(d+'/f.bin','wb').write(b)
sp=R.spills(d+'/pei.mir'); mm=R.M(b); mp,_=R.bestperm(b,sp,3)
os.remove(d+'/pei.mir') if not os.environ.get('KEEPMIR') else None
print(json.dumps({'n':n,'force':force,'bytes':len(b),'M':mm,'ratio':R.ratio(b),'nspill':len(sp),'Mperm':mp}))
