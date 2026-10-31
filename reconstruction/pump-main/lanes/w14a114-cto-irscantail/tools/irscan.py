#!/usr/bin/env python3
"""irscan.py <mn.ll> <out.jsonl> [W] [maxlen]: experiment-only post-opt IR block-ORDER scan of admin_cto::execute
OUTSIDE validate (generalized w14a101 irgreedy.py). Units: chains of 1..maxlen consecutive non-validate blocks.
Positions: before every non-validate block that follows a conditional-br/switch block, within W blocks of the unit.
Each variant = one unit moved; scored with px2.py (ratio, M, per-0x400 orig chunk M). SEEDS env: 'a+b@c ...'."""
import sys,re,json,os,tempfile
from multiprocessing import Pool
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import px2
def load(text):
    L=text.split('\n')
    fs=[i for i,l in enumerate(L) if l.startswith('define') and 'admin_cto7execute' in l][0]
    fe=fs+[k for k,l in enumerate(L[fs:]) if l=='}'][0]
    st=[i for i in range(fs+1,fe) if re.match(r'^("[^"]+"|[\w.$-]+):',L[i])]
    bl=[]
    for k,i in enumerate(st):
        e=st[k+1] if k+1<len(st) else fe
        n=re.match(r'^("[^"]+"|[\w.$-]+):',L[i]).group(1).strip('"')
        bl.append([n,L[i:e]])
    return L[:st[0]],bl,L[fe:]
def short(n): return n.split('E.')[-1] if 'to_string' in n else n
def move(bl,unit,before):
    u=[b for b in bl if short(b[0]) in unit]; assert len(u)==len(unit),(unit,)
    rest=[b for b in bl if short(b[0]) not in unit]
    k=[i for i,b in enumerate(rest) if short(b[0])==before][0]
    return rest[:k]+u+rest[k:]
def dump(h,bl,t): return '\n'.join(h+[l for b in bl for l in b[1]]+t)
def term(b):
    t=[l.strip() for l in b[1] if l.strip().startswith(('br ','switch','unreachable','ret'))]; return t[-1] if t else ''
src,outf=sys.argv[1:3]; W=int(sys.argv[3]) if len(sys.argv)>3 else 16; ML=int(sys.argv[4]) if len(sys.argv)>4 else 3
H,BL,TL=load(open(src).read())
for s in os.environ.get('SEEDS','').split():
    u,b=s.split('@'); BL=move(BL,u.split('+'),b)
names=[short(b[0]) for b in BL]
v0,v1=names.index(os.environ.get('VFIRST','bb6.i')),names.index(os.environ.get('VLAST','bb65.i'))
isv=lambda i: v0<=i<=v1
units=[]
for i in range(len(BL)):
    if isv(i) or i==0: continue
    for L in range(1,ML+1):
        if i+L>len(BL) or any(isv(j) for j in range(i,i+L)): break
        units.append((i,names[i:i+L]))
pos=sorted(set(i+1 for i,b in enumerate(BL[:-1]) if term(b).startswith(('br i1','switch')) and not isv(i+1) and i+1>0))
jobs=[(u,names[p]) for (i,u) in units for p in pos if int(os.environ.get("WMIN","0"))<abs(p-i)<=W and not (i<=p<=i+len(u))]
def run(j):
    u,p=j
    try: bl=move(BL,u,p)
    except Exception as e: return {'u':'+'.join(u),'p':p,'err':str(e)}
    with tempfile.TemporaryDirectory(dir=os.environ.get('TMPD')) as d:
        f=d+'/t.ll'; open(f,'w').write(dump(H,bl,TL))
        try: r=px2.run(f)
        except Exception as e: r={'err':str(e)[:200]}
    return {'u':'+'.join(u),'p':p,**r}
if __name__=='__main__':
    if os.environ.get('DUMP'):
        open(os.environ['DUMP'],'w').write(dump(H,BL,TL)); sys.exit()
    print(len(units),'units',len(pos),'pos',len(jobs),'jobs',flush=True)
    if os.environ.get('COUNT'): sys.exit()
    with Pool(int(os.environ.get('NP','6'))) as P, open(outf,'w') as f:
        for r in P.imap_unordered(run,jobs,chunksize=2):
            f.write(json.dumps(r)+'\n'); f.flush()
