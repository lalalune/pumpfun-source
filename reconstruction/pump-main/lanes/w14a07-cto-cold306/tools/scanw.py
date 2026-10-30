import sys,os,re,subprocess
from concurrent.futures import ThreadPoolExecutor
F,od=sys.argv[1:3]; base=sys.argv[3:]  # base extra weights "line:a:b"
L=open(F).read().split('\n'); T=os.path.dirname(os.path.abspath(__file__))
brs=[i for i,l in enumerate(L) if l.startswith('  br i1') and 1950<i+1<2510]
def run(job):
    tag,ws=job; LL=L[:]; meta=[]
    for k,(n,a,b) in enumerate(ws):
        LL[n]=re.sub(r', !prof !\d+','',LL[n])
        if a>=0: LL[n]+=f', !prof !9996{k}'; meta.append(f'!9996{k} = !{{!"branch_weights", i32 {a}, i32 {b}}}')
    d=f'{od}/{tag}'; os.makedirs(d,exist_ok=True); open(d+'/in.ll','w').write('\n'.join(LL+meta))
    r=subprocess.run([T+'/xo.sh',d+'/in.ll',d],capture_output=True,text=True).stdout.strip()
    for f in ('in.ll','ex.bc','ex.o'):
        try: os.remove(f'{d}/{f}')
        except: pass
    return tag,r
B=[(int(x.split(':')[0])-1,int(x.split(':')[1]),int(x.split(':')[2])) for x in base]
jobs=[]
for n in brs:
    for a,b in ((20,12),(12,20)):
        jobs.append((f'{n+1}_{a}_{b}',B+[(n,a,b)]))
with ThreadPoolExecutor(6) as ex:
    for tag,r in ex.map(run,jobs): print(tag,r,flush=True)
