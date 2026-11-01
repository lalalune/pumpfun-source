#!/usr/bin/env python3
"""ire.py <name> [edits.py] [--base m.ll] [--force F] [--perm] [--no-ares]: post-opt IR (m.ll) edit oracle for the S3 payload-r9 lane.
Applies EDITS (list of (old,new) exact single-occurrence replacements, or callables t->t) to a post-opt slim module,
runs the RAPRIO llc through llcw.py (join-restore), and prints ratio, bytes, M (and Mperm/Mhc with --perm), plus the
register of the swept payload at the sweep exits and at the event store. Experiment only (never a proposal)."""
import sys,os,subprocess,runpy,json,re,time
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle, relab as R
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w16a19-cto-s3sweptr9')
LLC=OUT+'/llvmb/bin/llc'
A=['-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections']
a=sys.argv[1:]; name=a.pop(0); edits=None; base=OUT+'/rx/S3n/m.ll'; force=''; perm=False; ares=True
while a:
    x=a.pop(0)
    if x=='--base': base=a.pop(0)
    elif x=='--force': force=a.pop(0)
    elif x=='--perm': perm=True
    elif x=='--no-ares': ares=False
    else: edits=x
d=OUT+'/rx/'+name; os.makedirs(d,exist_ok=True); t0=time.time()
t=open(base).read()
if edits:
    g=runpy.run_path(edits)
    for e in g['EDITS']:
        if callable(e): t=e(t); continue
        x,y=e; c=t.count(x); assert c==1,(c,x[:200]); t=t.replace(x,y)
open(d+'/m.ll','w').write(t)
env=dict(os.environ)
for k in ('RAPRIO_PRIO','RAPRIO_FORCE','RAPRIO_HINT','RAPRIO_LOG'): env.pop(k,None)
if force: env['RAPRIO_FORCE']=force
drv=[sys.executable,T+'/llcw.py'] if ares else [LLC]
r=subprocess.run([*drv,*A,d+'/m.ll','-filetype=obj','-o',d+'/f.o'],env=env,capture_output=True,text=True)
if r.returncode: print(json.dumps({'name':name,'error':r.stderr[-800:]})); sys.exit(1)
c=oracle.elf_fn(d+'/f.o',oracle.KEEP); open(d+'/fn.bin','wb').write(c)
orig=oracle.orig_window(); rr,sd=oracle.metric(c,orig)
res={'name':name,'ratio':round(rr,5),'bytes':len(c),'M':R.M(c)}
# payload registers: 'call; ldxdw rP,[r10-X]; ldxdw rT,[r10-X-8]' pairs inside the sweep region, event swept store
sys.path.insert(0,T); import bdis
L=bdis.d(c); regs=[]
for i in range(len(L)-2):
    o,s=L[i]
    if s.startswith('call') and 0x1d00<=o<=0x3e00:
        m1=re.match(r'ldxdw (r\d), \[r10-0x([0-9a-f]+)\]',L[i+1][1]); m2=re.match(r'ldxdw (r\d), \[r10-0x([0-9a-f]+)\]',L[i+2][1])
        if m1 and m2 and int(m2.group(2),16)==int(m1.group(2),16)+8: regs.append(m1.group(1))
res['exits']=''.join(x[1:] for x in regs)
m0=[s for o,s in L if re.match(r'mov64 r\d, 0$',s) and 0x1d00<=o<=0x1d60]
res['zero']=m0[0].split()[1].rstrip(',') if m0 else '-'
ev=[s for o,s in L if re.match(r'stxdw \[r10-0x218\], r\d',s)]
res['ev218']=''.join(s[-1] for s in ev)
if force: res['force']=force
if perm:
    subprocess.run([LLC,*A,d+'/m.ll','-stop-after=prologepilog','-o',d+'/pei.mir'],env=env,capture_output=True)
    p=subprocess.run([sys.executable,T+'/permhc.py',d],capture_output=True,text=True)
    try:
        pj=json.loads(p.stdout.strip().split('\n')[-1]); res['Mperm']=pj['Mperm']; res['Mhc']=pj['Mhc']
    except Exception as ex: res['perm_err']=(p.stderr or str(ex))[-300:]
res['secs']=round(time.time()-t0,1)
bs=os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so')
res['eq_main']=oracle.mask(oracle.elf_fn(bs,oracle.KEEP))==oracle.mask(c)
print(json.dumps(res)); open(d+'/res.json','w').write(json.dumps(res))
