#!/usr/bin/env python3
"""bbscan.py <base m.ll> <out.jsonl> [procs]: move each unit of Lv's IR bb11 to every legal position (def-use order kept),
run the RAPRIO llc (no forces) with SSC debug, record M/bytes/rot/holder weight. Experiment only (IR oracle bounds)."""
import sys,os,json,re,concurrent.futures as cf
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import ire
base,outp=sys.argv[1],sys.argv[2]; P=int(sys.argv[3]) if len(sys.argv)>3 else 3
txt=open(base).read(); L=txt.split('\n')
i0=L.index('bb11:                                             ; preds = %bb10, %bb8, %bb5')
i1=next(i for i in range(i0,len(L)) if L[i].startswith('  %_9.not.i = icmp eq i8'))
body=L[i0+3:i1]   # after phi, lifetime.end q, lifetime.start st
# group into units: a unit ends at a line that is a load/store/call/and/icmp result consumer (gep lines attach to next)
units=[];cur=[]
for l in body:
    cur.append(l)
    if re.match(r'\s+%\S+ = getelementptr',l) and not ('new.sroa_idx' in l): continue
    if re.match(r'\s+%4[23] = ',l) and 'zext' not in l and 'store' not in l: continue
    if 'zext i1 %quote_locked' in l: continue
    units.append(cur); cur=[]
if cur: units.append(cur)
# regroup: hold=16-17, cbx=18-19, new=20-21, sk=22-25; 0 and 26.. fixed
g=[units[0]]+units[1:16]+[units[16]+units[17],units[18]+units[19],units[20]+units[21],units[22]+units[23]+units[24]+units[25]]
tail=[l for u in units[26:] for l in u]
units=g
MOVERS=[int(x) for x in os.environ.get('MOVERS','9,10,11,12,13,14,15,16,17,18,19').split(',')]
def defs(u): return {m for l in u for m in re.findall(r'^\s+(%[\w.]+) =',l)}
def uses(u):
    s=set()
    for l in u:
        r=l.split('=',1)[1] if re.match(r'^\s+%[\w.]+ =',l) else l
        s|=set(re.findall(r'(%[\w.]+)',r))
    return s
D=[defs(u) for u in units]; U=[uses(u) for u in units]
def mem(u): 
    t='\n'.join(u); return ('store' in t) or ('call' in t) or (' load ' in t)
def legal(order):
    seen=set()
    for k in order:
        need=U[k]&set().union(*D)
        if not need<=seen|D[k]: return False
        seen|=D[k]
    return True
cands=[]
n=len(units)
for k in MOVERS:
    for j in range(1,n+1):
        if j==k or j==k+1: continue
        order=list(range(n)); order.pop(k); order.insert(j if j<k else j-1,k)
        if order==list(range(n)) or not legal(order): continue
        cands.append((f'u{k}to{j}',order))
os.makedirs(T+'/../irx/bbscan',exist_ok=True)
def job(c):
    name,order=c
    t='\n'.join(L[:i0+3]+[l for k in order for l in units[k]]+tail+L[i1:])
    d=os.path.join(ire.OUT,'irx','bbscan'); p=f'{d}/{name}.ll'; open(p,'w').write(t)
    r=ire.run(p); os.remove(p); r['name']=name; r['unit']=units[order.index(order[0])][0].strip()[:40]
    return r
done=set()
if os.path.exists(outp): done={json.loads(l)['name'] for l in open(outp)}
print('units',n,'cands',len(cands),flush=True)
for k,u in enumerate(units): print(k,' | '.join(x.strip()[:60] for x in u),flush=True)
with cf.ThreadPoolExecutor(P) as ex, open(outp,'a') as f:
    for r in ex.map(job,[c for c in cands if c[0] not in done]):
        r.pop('top',None); f.write(json.dumps(r)+'\n'); f.flush()
