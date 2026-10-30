#!/usr/bin/env python3
# hc.py BASE.ll FIRST LAST [rounds] : greedy single-block-move hill-climb on swap_hop IR blocks in [FIRST..LAST] (names),
# objective = (call-order aligned count, exactish). Prints improvements.
import sys,os,re,subprocess,tempfile,difflib,json
from concurrent.futures import ThreadPoolExecutor
OB=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin'); O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w7r1-swaphop-inline')
base,first,last=sys.argv[1:4]; rounds=int(sys.argv[4]) if len(sys.argv)>4 else 3
L=open(base).read().split('\n')
s=[i for i,l in enumerate(L) if l.startswith('define') and '8swap_hop17h' in l][0]
e=s
while L[e]!='}': e+=1
body=[re.sub(r'%(\d+)\b',r'%v\1',l) for l in L[s+1:e]]
blocks=[]; cur=['entry',[]]
for l in body:
    m=re.match(r'^([\w.\-]+):',l)
    if m: blocks.append(cur); cur=[m.group(1),[l]]
    else: cur[1].append(l)
blocks.append(cur)
m=json.load(open(O+'/symmap.json'))
cen=json.load(open(O+'/census_base.json'))['targets'][0]; orig=[x['callee'] for x in cen['orig_sequence']]
oraw=open(O+'/orig_raw.bin','rb').read()
def toks(raw):
    i=0;out=[]
    while i<len(raw):
        k=16 if raw[i]==0x18 else 8; t=raw[i:i+k]
        if t[0]==0x85: t=t[:2]
        elif t[0]==0x18: t=t[:2]
        elif t[0]&7==5 and t[0]!=0x85 and t[0]!=0x95: t=t[:2]+t[4:8]
        out.append(t); i+=k
    return out
otok=toks(oraw)
def evalorder(order):
    d=tempfile.mkdtemp(dir=O+'/tmp')
    txt='\n'.join(L[:s+1]+[l for b in order for l in b[1]]+L[e:])
    open(d+'/m.ll','w').write(txt)
    r=subprocess.run([OB+'/llc','-O3','-mattr=+store-imm,+jmp-ext','-relocation-model=pic','-function-sections','-data-sections','-filetype=obj',d+'/m.ll','-o',d+'/m.o'],capture_output=True,text=True)
    if r.returncode: subprocess.run(['rm','-rf',d]); return None
    rel=subprocess.run([OB+'/llvm-readelf','-rW',d+'/m.o'],capture_output=True,text=True).stdout
    sec=None; calls=[]
    for l in rel.splitlines():
        mm=re.match(r"Relocation section '\.rel\.text\.(\S+)'",l)
        if mm: sec=mm.group(1); continue
        if sec and '8swap_hop17h' in sec:
            p=l.split()
            if len(p)>=5 and p[2]=='R_SBF_64_32' and p[4]!='abort': calls.append(m.get(p[4],'?'))
    hd=subprocess.run([OB+'/llvm-objdump','-h',d+'/m.o'],capture_output=True,text=True).stdout
    secn=next(l.split()[1] for l in hd.splitlines() if '.text.' in l and '8swap_hop17h' in l and '.rel' not in l)
    subprocess.run([OB+'/llvm-objcopy','-O','binary','--only-section='+secn,d+'/m.o',d+'/m.bin'],check=True)
    raw=open(d+'/m.bin','rb').read(); subprocess.run(['rm','-rf',d])
    sm=difflib.SequenceMatcher(None,orig,calls,autojunk=False)
    al=sum(b-a for o,a,b,_,_ in sm.get_opcodes() if o=='equal')
    ex=difflib.SequenceMatcher(None,otok,toks(raw),autojunk=False).ratio()
    return (al,round(ex,4),len(raw))
names=[b[0] for b in blocks]; i0=names.index(first); i1=names.index(last)
cur=blocks[:]; best=evalorder(cur); print('base',best,flush=True)
for r in range(rounds):
    region=[b[0] for b in cur[i0:i1+1]]
    cands=[]
    for x in region:
        for y in region:
            if x==y: continue
            o=cur[:]; xi=[b[0] for b in o].index(x); blk=o.pop(xi); yi=[b[0] for b in o].index(y); o.insert(yi+1,blk)
            cands.append((f'{x}>{y}',o))
    with ThreadPoolExecutor(int(os.environ.get('J','6'))) as ex:
        res=list(ex.map(lambda c:(c[0],evalorder(c[1])),cands))
    res=[(k,v) for k,v in res if v]
    res.sort(key=lambda kv:(kv[1][0],kv[1][1]),reverse=True)
    print('round',r,'top',res[:8],flush=True)
    k,v=res[0]
    if (v[0],v[1])<=(best[0],best[1]): break
    best=v; cur=dict(cands)[k]; print('take',k,v,flush=True)
open(O+'/ir/x/hc_best.order','w').write('\n'.join(b[0] for b in cur))
