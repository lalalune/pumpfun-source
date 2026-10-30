import sys,re,itertools,os,runpy; sys.path.insert(0,'.'); import irlib
from concurrent.futures import ThreadPoolExecutor
t,m=irlib.load(); f0=m.group(0)
if os.environ.get('PRE'): f0=runpy.run_path(os.environ['PRE'])['edit'](f0)
L=f0.split('\n')
brs=[i for i,l in enumerate(L) if re.match(r'\s+br i1 ',l)]
W=[(3,5),(5,3),(1,1),(1,2),(2,1),(1,4),(4,1),(1,16),(16,1),(1,2000),(2000,1),(1,0xfffff),(0xfffff,1)]
def mk(sel):
    N=L[:]; extra=[]
    for k,(i,(a,b)) in enumerate(sel):
        N[i]=N[i]+f', !prof !{9000+k}'; extra.append(f'!{9000+k} = !{{!"branch_weights", i32 {a}, i32 {b}}}')
    return '\n'.join(N),extra
def go(sel):
    f,extra=mk(sel)
    return sel, irlib.run(f,suffix='\n'+'\n'.join(extra)+'\n')[0]
def run2(f,extra):
    import tempfile,subprocess
    t,m=irlib.load(); sym=re.search(r'@(\S+?)\(',m.group(0)).group(1)
    t2=t[:m.start()]+f+t[m.end():]+'\n'+'\n'.join(extra)+'\n'
    old=irlib.BASE
    d=tempfile.mkdtemp(dir=irlib.OUT+'/tmp'); p=d+'/b.ll'; open(p,'w').write(t2)
    irlib.BASE=p
    t3,m3=irlib.load(); r,dd=irlib.run(m3.group(0))
    subprocess.run(['rm','-rf',d]); irlib.BASE=old
    return r
mode=sys.argv[1] if len(sys.argv)>1 else 'single'
jobs=[]
if mode=='single':
    for i in brs:
        for w in W: jobs.append(((i,w),))
elif mode=='triple':
    Wp=[(3,5),(5,3),(1,1)]
    for c in itertools.combinations(brs,3):
        for ws in itertools.product(Wp,repeat=3): jobs.append(tuple(zip(c,ws)))
else:
    Wp=[(3,5),(5,3),(1,1)]
    for i,j in itertools.combinations(brs,2):
        for w1 in Wp:
            for w2 in Wp: jobs.append(((i,w1),(j,w2)))
with ThreadPoolExecutor(6) as ex: res=list(ex.map(go,jobs))
res=[(r,s) for s,r in res if r]
res.sort(key=lambda x:x[0][1]+x[0][2])
print(len(jobs),'jobs')
for r,s in res[:30]: print(r,[(L[i].strip()[:60],w) for i,w in s])
noh=[(r,s) for r,s in res if not any('%43,' in L[i] for i,w in s)]
print('without %43:'); [print(r,[(L[i].strip()[:40],w) for i,w in s]) for r,s in noh[:8]]
print('zero-diff count',sum(1 for r,s in res if r[1]+r[2]==0),'zero-diff without 43',sum(1 for r,s in noh if r[1]+r[2]==0))
