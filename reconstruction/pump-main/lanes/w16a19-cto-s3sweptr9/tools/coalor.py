#!/usr/bin/env python3
"""coalor.py <m.ll> <name> [--force F] [--perm] [--members SW|X]: w14a69's ideal-coalescer-order oracle on the RAPRIO llc
(experiment only). Renames every pre-coalescing member of swept's final class (SW) to the return block's Result payload
vreg (RP) before RegisterCoalescer, so swept joins the Err-payload class without any CFG change, then finishes llc
(with optional RAPRIO forces) and scores. --members X instead merges the post-sweep Err join's class (the bb64 copy source)."""
import sys,os,re,subprocess,json
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle, relab as R, bdis
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w16a19-cto-s3sweptr9')
LLC=OUT+'/llvmb/bin/llc'; A=['-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections']
a=sys.argv[1:]; m=a.pop(0); name=a.pop(0); force=''; perm=False
while a:
    x=a.pop(0)
    if x=='--force': force=a.pop(0)
    elif x=='--perm': perm=True
d=OUT+'/rx/'+name; os.makedirs(d,exist_ok=True)
env=dict(os.environ)
for k in ('RAPRIO_PRIO','RAPRIO_FORCE','RAPRIO_HINT','RAPRIO_LOG'): env.pop(k,None)
# 1. coalescer log + SW/RP
r=subprocess.run([LLC,*A,m,'-filetype=obj','-o',d+'/dbg.o','-debug-only=regalloc'],capture_output=True,text=True,env=env)
open(d+'/ra.log','w').write(r.stderr); os.remove(d+'/dbg.o')
c=subprocess.run([sys.executable,T+'/coal.py',m],capture_output=True,text=True).stdout
sw=re.search(r'SW=%(\d+)',c).group(1); rp=re.search(r'RP=%(\d+)',c).group(1)
mem=subprocess.run([sys.executable,T+'/ufclass.py',d+'/ra.log','%'+sw],capture_output=True,text=True).stdout.split()
# 2. pre-coalescer MIR, rename, finish
subprocess.run([LLC,*A,m,'-stop-before=register-coalescer','-o',d+'/pre.mir'],check=True,env=env)
subprocess.run([sys.executable,T+'/mirren.py',d+'/pre.mir',d+'/c.mir','%'+rp,*mem],check=True)
if force: env['RAPRIO_FORCE']=force
r=subprocess.run([LLC,*A,d+'/c.mir','-start-before=register-coalescer','-filetype=obj','-o',d+'/f.o'],capture_output=True,text=True,env=env)
if r.returncode: sys.exit(r.stderr[-1500:])
b=oracle.elf_fn(d+'/f.o',oracle.KEEP)
import struct
def fixfs(c):
    b=bytearray(c); i=0
    while i<len(b):
        op=b[i]
        if op in (0x7b,0x73,0x6b,0x63,0x7a,0x72,0x6a,0x62) and (b[i+1]&0xf)==10:
            off=struct.unpack_from('<h',b,i+2)[0]
            if off>=0: struct.pack_into('<h',b,i+2,off-0x1000)
        i+=16 if op==0x18 else 8
    return bytes(b)
b=fixfs(b); open(d+'/fn.bin','wb').write(b)
rr,sd=oracle.metric(b,oracle.orig_window())
res={'name':name,'SW':sw,'RP':rp,'members':len(mem),'ratio':round(rr,5),'bytes':len(b),'M':R.M(b)}
L=bdis.d(b)
for i,(o,s) in enumerate(L):
    if s=='exit':
        for k in range(i-1,i-4,-1):
            mm=re.match(r'stxdw \[r\d\+0x8\], (r\d)',L[k][1])
            if mm: res['payreg']=mm.group(1)
        break
res['ev218']=''.join(s[-1] for o,s in L if re.match(r'stxdw \[r10-0x218\], r\d',s))
if force: res['force']=force
if perm:
    subprocess.run([LLC,*A,d+'/c.mir','-start-before=register-coalescer','-stop-after=prologepilog','-o',d+'/pei.mir'],capture_output=True,env=env)
    # permhc reads d/f.o: write a re-biased copy is not possible for .o, so permhc runs on the raw object (fixed-stack bias only hits arg stores)
    p=subprocess.run([sys.executable,T+'/permhc.py',d],capture_output=True,text=True)
    try:
        pj=json.loads(p.stdout.strip().split('\n')[-1]); res['Mperm']=pj['Mperm']; res['Mhc']=pj['Mhc']
    except Exception as ex: res['perm_err']=(p.stderr or str(ex))[-300:]
os.remove(d+'/ra.log')
print(json.dumps(res))
