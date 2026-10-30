#!/usr/bin/env python3
"""irclimb.py <ir-dir> <tag> <iters>: hill-climb IR block order/polarity in validate's region of admin_cto::execute."""
import sys,re,random,subprocess,os,json,difflib
sys.path.insert(0,os.path.dirname(__file__)); import blocks
L=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w10r1-admincto-region1of6')
irdir,tag,iters=sys.argv[1],sys.argv[2],int(sys.argv[3])
mod=open(irdir+'/pump_recovered.ll').read()
sym=re.search(r'_ZN14pump_recovered9admin_cto7execute17h[0-9a-f]+E',mod).group(0)
i=mod.index('@'+sym+'('); i=mod.rindex('\ndefine',0,i)+1; j=mod.index('\n}\n',i)+3
fn=mod[i:j]
h,B,r=blocks.split(fn)
labs=[b for b,_ in B]
lo=labs.index('bb5.i'); hi=max(k for k,l in enumerate(labs) if l=='bb75')
region=list(range(lo,hi))
ORIG_ERR=[289,298,306,296,326,312,307,330,338,334]
def render(order,flips):
    BB=[B[k] for k in range(lo)]+[B[k] for k in order]+[B[k] for k in range(hi,len(B))]
    out=[]
    for lab,t in BB:
        if lab in flips:
            m=re.search(r'\n  br i1 (%[\w.]+), label (%\S+), label (%\S+)$',t)
            if m:
                v=m.group(1); nv='%fl'+str(abs(hash(lab))%100000)
                t=t[:m.start()]+f'\n  {nv} = xor i1 {v}, true\n  br i1 {nv}, label {m.group(3)}, label {m.group(2)}'+t[m.end():]
        out.append((lab,t))
    return blocks.join(h,out,r)
def evaluate(order,flips,name):
    f=render(order,flips)
    d=f'{L}/irclimb/{tag}/{name}'; os.makedirs(d,exist_ok=True)
    open(d+'/x.py','w').write('def edit(fn):\n    return open(%r).read()\n'%(d+'/fn.ll'))
    open(d+'/fn.ll','w').write(f)
    p=subprocess.run(['python3',L+'/tools/irexp.py',irdir,f'climb-{tag}-{name}',d+'/x.py'],capture_output=True,text=True)
    o=p.stdout
    m1=re.search(r'R1local-strict (\d+)',o); m2=re.search(r'R1local-loose (\d+)',o); m3=re.search(r'cand_bytes (\d+)',o)
    if not (m1 and m2): return -1,o[-500:]
    eo=[int(x,16) for x in re.findall(r'stw \[r10 - 0x2b8\], (0x[0-9a-f]+)',open(f'{L}/irexp/climb-{tag}-{name}/fn.dis').read())]
    eo=[int(x) for x in eo]
    eo=[x for x in eo if x in ORIG_ERR]
    sm=difflib.SequenceMatcher(None,eo,ORIG_ERR).ratio()
    sc=int(m1.group(1))+int(m2.group(1))+int(40*sm)
    subprocess.run(['rm','-rf',f'{L}/irexp/climb-{tag}-{name}/m.o',f'{L}/irexp/climb-{tag}-{name}/m.ll'])
    return sc,(m1.group(1),m2.group(1),m3.group(1),eo)
order=region[:]; flips=set()
best,info=evaluate(order,flips,'s0'); print('start',best,info,flush=True)
random.seed(hash(tag)%1000)
condbr=[B[k][0] for k in region if re.search(r'\n  br i1 %[\w.]+, label \S+, label \S+$',B[k][1])]
for it in range(iters):
    o2=order[:]; f2=set(flips)
    if random.random()<0.35:
        lab=random.choice(condbr); f2^={lab}; mv=('flip',lab)
    else:
        n=random.choice([1,1,2,3])
        a=random.randrange(len(o2)-n+1); chunk=o2[a:a+n]; del o2[a:a+n]
        b=random.randrange(len(o2)+1); o2[b:b]=chunk; mv=('move',[B[k][0] for k in chunk],b)
    sc,inf=evaluate(o2,f2,f'i{it}')
    if sc>best:
        best,order,flips=sc,o2,f2; print('IMPROVE',it,sc,inf,mv,flush=True)
        json.dump({'order':[B[k][0] for k in order],'flips':sorted(flips),'score':sc,'info':inf},open(f'{L}/irclimb/{tag}/best.json','w'))
    elif it%10==0: print('it',it,sc,best,flush=True)
