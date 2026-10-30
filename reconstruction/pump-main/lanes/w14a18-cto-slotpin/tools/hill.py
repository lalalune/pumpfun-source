#!/usr/bin/env python3
"""hill.py <qdir> <bc> [passes]: interval-level greedy hill-climb on the scorer's own ratio. Start from the real colouring
(col.json); candidate moves = each object's vote targets against the original (top 3); a move is legal if no live-overlapping
spill interval / any alloca occupies the target. Accept moves that raise M. Writes hill.json and prints the trajectory."""
import sys,os,json,subprocess,collections,difflib
from concurrent.futures import ThreadPoolExecutor
T=os.path.dirname(os.path.abspath(__file__)); O=os.path.dirname(T); sys.path.insert(0,T); import slotpin as S
d,bc=sys.argv[1:3]; P=int(sys.argv[3]) if len(sys.argv)>3 else 2
ob={int(k):v for k,v in json.load(open(d+'/objs.json')).items()}; col={int(k):v for k,v in json.load(open(d+'/col.json')).items()}
LV=S.liveness(bc,d)
a,ta=S._rd(d+'/direct.txt'); b,tb=S._rd(O+'/orig_fn.txt'); oa=S._offs(a); obb=S._offs(b)
V=collections.defaultdict(collections.Counter)
for t,i1,i2,j1,j2 in difflib.SequenceMatcher(None,ta,tb,autojunk=False).get_opcodes():
    if t!='equal': continue
    for k in range(i2-i1):
        x,y=oa[i1+k],obb[j1+k]
        if x is None or y is None: continue
        for i,o in ob.items():
            if o['off']<=x<o['off']+o['size']: V[i][y-(x-o['off'])]+=1; break
moves=[(i,t) for i,c in V.items() for t,_ in c.most_common(3)]+[(i,col[i]) for i in col]
START=os.environ.get('START')
def legal(m,i,t):
    sz=ob[i]['size']
    for j,u in m.items():
        if j==i: continue
        us=ob[j]['size']
        if t<u+us and u<t+sz:
            if ob[i]['type']=='spill-slot' and ob[j]['type']=='spill-slot' and u==t and us==sz and not S.ovl(LV.get(i,[]),LV.get(j,[])): continue
            return False
    return True
def M(m,tag):
    f=f'{d}/_h{tag}.json'; json.dump({str(k):v for k,v in m.items()},open(f,'w'))
    s=subprocess.run(['python3',T+'/slotpin.py','run',d,f,f'{d}/_h{tag}.txt'],capture_output=True,text=True).stdout.split()
    try: return round(float(s[1])*(3339+int(s[4]))/2)
    except Exception: return -1
cur=dict(col)
if START: cur.update({int(k):v for k,v in json.load(open(START)).items()})
best=M(cur,'base'); print('start',best,'moves',len(moves),flush=True)
for p in range(P):
    cand=[(i,t) for i,t in moves if cur.get(i)!=t and legal(cur,i,t)]
    def ev(x):
        i,t=x; m=dict(cur); m[i]=t; return M(m,f'{i}_{t}')-best,i,t
    with ThreadPoolExecutor(4) as ex: R=sorted(ex.map(ev,cand),reverse=True)
    acc=0
    for g,i,t in R:
        if g<=0: break
        if not legal(cur,i,t): continue
        m=dict(cur); m[i]=t; v=M(m,'try')
        if v>best: cur=m; best=v; acc+=1
    print('pass',p,'positive singles',sum(1 for g,_,_ in R if g>0),'accepted',acc,'M',best,flush=True)
    if not acc: break
json.dump({str(k):v for k,v in cur.items()},open(d+'/hill.json','w'))
for f in os.listdir(d):
    if f.startswith('_h'): os.remove(os.path.join(d,f))
print('final M',best)
