#!/usr/bin/env python3
"""climbb.py <m.ll> <out.log> --base f1,f2 --genes votes.jsonl [--sticky] [--par N] [--size 27400|any] [--top K]
Price every vote gene (v=want) as a single force on top of the base forces, then greedily climb over the gainful
genes (STICKY=1 if --sticky). Logs JSON lines. Experiment only (private RAPRIO llc)."""
import sys,os,json,subprocess,hashlib
from concurrent.futures import ThreadPoolExecutor
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle,fscr
OUT=os.path.dirname(T)
a=sys.argv[1:]
def opt(k,d=None):
    if k in a: i=a.index(k); v=a[i+1]; del a[i:i+2]; return v
    return d
base=[x for x in opt('--base','').split(',') if x]; gf=opt('--genes'); par=int(opt('--par','4')); size=opt('--size','any'); top=int(opt('--top','0'))
sticky='--sticky' in a; a=[x for x in a if x!='--sticky']
m,logf=a[0],a[1]
genes=[]
for l in open(gf):
    j=json.loads(l); genes.append(f"{j['v']}={j['want']}")
if top: genes=genes[:top]
def run(forces):
    env=dict(os.environ,RAPRIO_FORCE=','.join(base+forces))
    if sticky: env['RAPRIO_STICKY']='1'
    k=hashlib.sha1((','.join(base+forces)+str(sticky)+m).encode()).hexdigest()[:12]; o=f'{OUT}/lx/cb_{k}.o'
    r=subprocess.run(['nice','-n','5',fscr.LLC['p'],*fscr.LLCA,m,'-filetype=obj','-o',o],env=env,capture_output=True,text=True)
    if r.returncode: return None
    b=oracle.elf_fn(o,oracle.KEEP); os.remove(o)
    return {'forces':forces,'M':len(fscr.mset(fscr.toks(b))),'bytes':len(b)}
okz=lambda r: size=='any' or r['bytes']==int(size)
lg=open(logf,'a'); b0=run([]); lg.write(json.dumps({'base':base,'sticky':sticky,'res':b0})+'\n'); lg.flush()
with ThreadPoolExecutor(par) as ex:
    pr=[r for r in ex.map(run,[[g] for g in genes]) if r]
for r in pr: lg.write(json.dumps({'price':r})+'\n')
lg.flush()
gain=[r['forces'][0] for r in sorted(pr,key=lambda r:-r['M']) if r['M']>b0['M'] and okz(r)]
lg.write(json.dumps({'gainful':gain})+'\n'); lg.flush()
cur=[]; best=b0
with ThreadPoolExecutor(par) as ex:
    while True:
        tr=[g for g in gain if g.split('=')[0] not in [c.split('=')[0] for c in cur]]
        if not tr: break
        res=[r for r in ex.map(run,[cur+[g] for g in tr]) if r and okz(r)]
        if not res: break
        x=max(res,key=lambda r:r['M'])
        if x['M']<=best['M']: break
        cur=x['forces']; best=x; lg.write(json.dumps({'step':best})+'\n'); lg.flush()
lg.write(json.dumps({'final':best,'base':base})+'\n'); lg.close()
print(json.dumps({'final':best,'base':base}))
