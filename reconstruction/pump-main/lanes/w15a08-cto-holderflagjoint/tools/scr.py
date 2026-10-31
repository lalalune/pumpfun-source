#!/usr/bin/env python3
"""scr.py <name> <edit.py>... : post-opt IR edits on rx/main/m.ll (or $BASE), llc obj + PEI MIR, report M, bytes, Mperm (spill-permutation bound)"""
import sys,os,subprocess,runpy,json
O=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,O+'/tools'); import relab as R
n=sys.argv[1]; d=f'{O}/d/{n}'; os.makedirs(d,exist_ok=True)
t=open(os.environ.get('BASE',O+'/rx/main/m.ll')).read()
for p in sys.argv[2:]:
    p=p if os.path.exists(p) else f'{O}/e/ir/{p}.py'
    for e in runpy.run_path(p)['EDITS']:
        if callable(e): t=e(t); continue
        a,b=e; c=t.count(a); assert c==1,(p,c,a[:150]); t=t.replace(a,b)
open(d+'/m.ll','w').write(t)
L=O+'/tools/llc.sh'
p1=subprocess.Popen([L,d+'/m.ll','-filetype=obj','-o',d+'/f.o'],stderr=subprocess.PIPE)
p2=subprocess.Popen([L,d+'/m.ll','-stop-after=prologepilog','-o',d+'/pei.mir'],stderr=subprocess.PIPE)
p3=None
if os.environ.get('LAY'):
    p3=subprocess.Popen([L,d+'/m.ll','-filetype=null','-o','/dev/null','-print-after=block-placement','-filter-print-funcs='+os.environ.get('FN','_ZN13pump_recovered9admin_cto7execute17h')],stderr=open(d+'/pab.mir','w'))
e1=p1.communicate()[1]; p2.communicate()
if p3:
    p3.wait(); subprocess.run(['python3',O+'/tools/lay.py',d+'/pab.mir'],stdout=open(d+'/lay','w'))
if p1.returncode: print(json.dumps({'n':n,'err':e1.decode()[-400:]})); sys.exit(1)
b=R.g['elf_fn'](d+'/f.o',R.g['KEEP']); open(d+'/f.bin','wb').write(b)
sp=R.spills(d+'/pei.mir'); m=R.M(b); mp,_=R.bestperm(b,sp,3)
os.environ.get('KEEPLL') or os.remove(d+'/m.ll')
print(json.dumps({'n':n,'bytes':len(b),'M':m,'ratio':R.ratio(b),'nspill':len(sp),'Mperm':mp}))
