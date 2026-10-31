#!/usr/bin/env python3
"""irmv.py <src m.ll> <name> MOVE... : post-opt IR block-order oracle (experiment only). MOVE = 'blk1,blk2@after_blk'
moves those blocks (in that order) right after after_blk inside admin_cto::execute. Runs llc like fastbuild, prints
bytes/ratio/M/Mperm/marker. Output in rx/<name>/."""
import sys,os,re,subprocess,json
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import relab as R, marker as MK
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w16a07-cto-sweeptuple')
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
src,name=sys.argv[1],sys.argv[2]; moves=sys.argv[3:]
t=open(src).read()
i=t.index('define hidden { i64, ptr } @_ZN14pump_recovered9admin_cto7execute'); j=t.index('\n}\n',i)
head,body,tail=t[:i],t[i:j],t[j:]
parts=re.split(r'\n(?=[\w.$"-]+:)',body)
fn=parts[0]; blocks=parts[1:]
def bname(b): return b.split('\n',1)[0].split(':')[0].strip('"')
for mv in moves:
    names,after=mv.split('@'); names=names.split(',')
    sel=[]
    for n in names:
        k=[x for x in range(len(blocks)) if bname(blocks[x])==n]; assert len(k)==1,(n,len(k)); sel.append(blocks.pop(k[0]))
    k=[x for x in range(len(blocks)) if bname(blocks[x])==after]; assert len(k)==1,(after,len(k))
    blocks[k[0]+1:k[0]+1]=sel
nb='\n'.join([fn]+blocks)
d=f'{O}/rx/{name}'; os.makedirs(d,exist_ok=True)
open(d+'/m.ll','w').write(head+nb+tail)
r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
if r.returncode: print(r.stderr[-2000:]); sys.exit(1)
b=R.g['elf_fn'](d+'/m.o',R.g['KEEP']); open(d+'/fn.bin','wb').write(b); os.remove(d+'/m.o'); os.remove(d+'/m.ll')
m0=R.M(b); sp=R.binspills(b); mb,pm=R.bestperm(b,sp,4); mk=MK.marker(b) or {}
print(json.dumps({'name':name,'bytes':len(b),'ratio':R.ratio(b),'M':m0,'Mperm':mb,'mk':{k:mk.get(k) for k in ('lam','key','data','E','own')}}))
