#!/usr/bin/env python3
"""hc.py slim.ll outdir [rounds]: greedy hill-climb over single-block moves X>Y on buy_exact_quote IR; llc oracle; maximize raw ratio."""
import sys,os,re,subprocess,difflib,tempfile,json
from concurrent.futures import ThreadPoolExecutor as ProcessPoolExecutor
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools')
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w4-buyexactquote-v3')
src,od=sys.argv[1],sys.argv[2]; rounds=int(sys.argv[3]) if len(sys.argv)>3 else 3
os.makedirs(od,exist_ok=True)
T=open(src).read().split('\n')
s=next(i for i,l in enumerate(T) if l.startswith('define') and 'trade15buy_exact_quote17h' in l); e=next(i for i in range(s,len(T)) if T[i]=='}')
SYM=re.search(r'@(_ZN\S+?)\(',T[s]).group(1)
ren=lambda t: re.sub(r'^([0-9]+):', r'v\1:', re.sub(r'%([0-9]+)\b', r'%v\1', t))
body=[ren(x) for x in T[s+1:e]]; bl=[]; cur=['start',[]]
for l in body:
    m=re.match(r'^([A-Za-z0-9_.$"]+):',l)
    if m: bl.append(cur); cur=[m.group(1),[l]]
    else: cur[1].append(l)
bl.append(cur); bl=[b for b in bl if b[1]]
pre='\n'.join(T[:s]+[ren(T[s])]); post='\n'.join(T[e:])
ORIG=[l.strip() for l in open(O+'/an/orig-norm.txt') if l.strip()]
def norm(s):
    s=re.sub(r'call -?0x[0-9a-f]+','call X',s); s=re.sub(r'lddw (r\d+), 0x[0-9a-f]+',r'lddw \1, X',s); return s.strip()
def evalorder(names):
    d={n:b for n,b in bl}
    txt=pre+'\n'+'\n'.join('\n'.join(d[n]) for n in names)+'\n'+post
    fd,p=tempfile.mkstemp(suffix='.ll',dir=od); os.write(fd,txt.encode()); os.close(fd)
    o=p[:-3]+'.o'
    r=subprocess.run([SDK+'/llvm/bin/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext',p,'-filetype=obj','-o',o],capture_output=True,text=True)
    os.unlink(p)
    if r.returncode: return (-1,0)
    fn=subprocess.run([O+'/scripts/fn.sh',o,SYM],capture_output=True,text=True).stdout; os.unlink(o)
    C=[norm(x) for x in fn.splitlines() if x.strip()]
    sm=difflib.SequenceMatcher(None,ORIG,C,autojunk=False)
    return (sm.ratio(),len(C))
names=[n for n,b in bl]
best=evalorder(names); print('start',best,flush=True)
for rd in range(rounds):
    cands=[]
    for x in names[1:]:
        for y in names:
            if x==y: continue
            nn=[n for n in names if n!=x]; i=nn.index(y); nn.insert(i+1,x)
            if nn!=names: cands.append((f'{x}>{y}',nn))
    with ProcessPoolExecutor(8) as ex:
        res=list(ex.map(evalorder,[c[1] for c in cands],chunksize=8))
    sc=sorted(zip(res,range(len(cands))),reverse=True)
    top=sc[0]
    print('round',rd,'best move',cands[top[1]][0],top[0],'top5',[(cands[i][0],round(r[0],4)) for r,i in sc[:5]],flush=True)
    if top[0][0]<=best[0]+1e-9: break
    best=top[0]; names=cands[top[1]][1]
    json.dump(names,open(od+'/order.json','w'))
print('final',best)
