#!/usr/bin/env python3
"""brscan.py <base.s.ll> <out.jsonl> [jobs]: llvm.expect true/false on every br i1 in execute/validate/sweep/wallet pre-opt bodies; score + region deltas"""
import sys,os,re,json,difflib
from concurrent.futures import ThreadPoolExecutor
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
os.environ.setdefault('LANE_OUT',os.path.dirname(T))
import fx,oracle
OUT=os.path.dirname(T)
R=[('E1',0x0),('E2',0x280),('E3',0x420),('V1',0x708),('V2',0xb00),('V3',0xe60),('V4',0x1258),('V5',0x1490),('J1',0x1800),('J2',0x1990),('W1',0x1c88),('S1',0x1f68),('T1',0x26e8),('C1',0x3c50),('P1',0x4aa8),('EV',0x4e50),('TL',0x5558),('S2',0x5a18),('W2',0x5c18),('END',0x6b08)]
def split(raw):
    i=0;o=[]
    while i<len(raw):
        n=16 if raw[i]==0x18 else 8; o.append(i); i+=n
    return o
ow=oracle.orig_window(); ot=oracle.mask(ow); oo=split(ow)
def regs(raw):
    ct=oracle.mask(raw); sm=difflib.SequenceMatcher(None,ot,ct,autojunk=False)
    cnt={r[0]:0 for r in R}
    for b in sm.get_matching_blocks():
        for k in range(b.a,b.a+b.size):
            off=oo[k]
            for i in range(len(R)-1):
                if R[i][1]<=off<R[i+1][1]: cnt[R[i][0]]+=1; break
    return cnt
base=sys.argv[1]; outp=sys.argv[2]; jobs=int(sys.argv[3]) if len(sys.argv)>3 else 2
t0=open(base).read()
FN={'ex':r'admin_cto7execute17h','va':r'admin_cto8validate17h','sw':r'admin_cto7execute5sweep17h','wa':r'admin_cto7execute6wallet17h'}
spans={}
for k,p in FN.items():
    m=re.search(r'^define[^\n]*'+p+r'[^\n]*\n',t0,re.M); s=m.start(); e=t0.index('\n}\n',s); spans[k]=(s,e)
bn=os.path.basename(base).replace('.s.ll','')
bfn=f'{OUT}/fx/{bn}/fn.bin'
if not os.path.exists(bfn): fx.run(t0,bn)
bc=regs(open(bfn,'rb').read()); bM=sum(bc.values())
tasks=[]
for k,(s,e) in spans.items():
    body=t0[s:e]
    for i,m in enumerate(re.finditer(r'  br i1 (%[\w.]+), label (%[\w.]+), label (%[\w.]+)\n',body)):
        for val in ('true','false'):
            tasks.append((f'{k}{i}{val[0]}',k,m.start(),m.end(),m.group(1),m.group(2),m.group(3),val))
done=set()
if os.path.exists(outp):
    for l in open(outp):
        try: done.add(json.loads(l)['name'])
        except: pass
def run(tk):
    n,k,ms,me,c,a,b,val=tk
    if n in done: return None
    s,e=spans[k]
    new=f'  {c}.xh = call zeroext i1 @llvm.expect.i1(i1 zeroext {c}, i1 zeroext {val})\n  br i1 {c}.xh, label {a}, label {b}\n'
    t=t0[:s+ms]+new+t0[s+me:]
    r=fx.run(t,f'bs_{bn}_{n}')
    if 'err' in r: return {'name':n,'err':r['err'][:200]}
    c2=regs(open(f'{OUT}/fx/bs_{bn}_{n}/fn.bin','rb').read())
    d={x:c2[x]-bc[x] for x in c2 if c2[x]!=bc[x]}
    import shutil; shutil.rmtree(f'{OUT}/fx/bs_{bn}_{n}',ignore_errors=True)
    return {'name':n,'fn':k,'cond':c,'M':r['M'],'bytes':r['bytes'],'dM':r['M']-bM,'d':d}
with ThreadPoolExecutor(jobs) as ex, open(outp,'a') as f:
    for res in ex.map(run,tasks):
        if res: f.write(json.dumps(res)+'\n'); f.flush()
print('tasks',len(tasks))
