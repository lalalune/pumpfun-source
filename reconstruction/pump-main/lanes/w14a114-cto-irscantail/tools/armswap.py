#!/usr/bin/env python3
"""armswap.py <mn.ll> <out.jsonl>: experiment-only 'if/else arm order' IR scan of admin_cto::execute.
For every conditional br (or switch) block X outside validate and each pair of its successors (A,B): the region of A is
the set of blocks dominated by A, likewise B. If a region is a contiguous IR run, move it (whole) just before the other
region's first block, or just after the other region's last block. Also move a contiguous region before X's IR successor.
Scored with px2.py (real llc RA)."""
import sys,re,json,os,tempfile
from multiprocessing import Pool
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import px2
exec(open(T+'/irscan.py').read().split("src,outf=sys.argv")[0])
src,outf=sys.argv[1:3]
H,BL,TL=load(open(src).read())
names=[b[0] for b in BL]; idx={n:i for i,n in enumerate(names)}
def succ(b):
    t=' '.join(l for l in b[1] if l.strip().startswith(('br ','switch')) or l.strip().startswith(('i64 ','i32 ','i8 ','i1 ')) or l.strip()==']')
    return list(dict.fromkeys(x.strip('"') for x in re.findall(r'label %("[^"]+"|[\w.$-]+)',t)))
S={b[0]:succ(b) for b in BL}
P={n:[] for n in names}
for n,ss in S.items():
    for s in ss: P[s].append(n)
# dominators (iterative, RPO)
order=[];seen=set()
def dfs(n):
    stack=[(n,iter(S[n]))]; seen.add(n)
    while stack:
        x,it=stack[-1]
        for y in it:
            if y not in seen: seen.add(y); stack.append((y,iter(S[y]))); break
        else: order.append(x); stack.pop()
dfs(names[0]); rpo=order[::-1]; rn={n:i for i,n in enumerate(rpo)}
idom={names[0]:names[0]}
def inter(a,b):
    while a!=b:
        while rn[a]>rn[b]: a=idom[a]
        while rn[b]>rn[a]: b=idom[b]
    return a
ch=True
while ch:
    ch=False
    for n in rpo[1:]:
        ps=[p for p in P[n] if p in idom]
        if not ps: continue
        d=ps[0]
        for p in ps[1:]: d=inter(p,d)
        if idom.get(n)!=d: idom[n]=d; ch=True
def doms(a):
    out=[]
    for n in rpo:
        x=n
        while True:
            if x==a: out.append(n); break
            if x==idom[x]: break
            x=idom[x]
    return out
v0,v1=idx['bb6.i'],idx['bb65.i']
def contig(r):
    ii=sorted(idx[n] for n in r); return ii==list(range(ii[0],ii[-1]+1)) and not any(v0<=i<=v1 for i in ii)
jobs=set()
for i,b in enumerate(BL):
    if v0<=i<=v1: continue
    ss=S[b[0]]
    if len(ss)<2: continue
    R={s:doms(s) for s in ss}
    for a in ss:
        ra=R[a]
        if not ra or not contig(ra): continue
        ua=tuple(sorted(ra,key=idx.get))
        for c in ss:
            if c==a: continue
            rc=R[c]
            if rc and contig(rc):
                f=min(idx[n] for n in rc); l=max(idx[n] for n in rc)
                tgt=[names[f]]+([names[l+1]] if l+1<len(names) else [])
            else:
                tgt=[c]
            for t in tgt+([names[i+1]] if i+1<len(names) else []):
                if t not in ua: jobs.add((ua,t))
jobs=sorted(jobs,key=lambda j:(idx[j[0][0]],j[1]))
def run(j):
    u,p=j
    try: bl=move(BL,[short(x) for x in u],short(p))
    except Exception as e: return {'u':u[0],'n':len(u),'p':p,'err':str(e)[:100]}
    if [b[0] for b in bl]==names: return None
    with tempfile.TemporaryDirectory(dir=os.environ.get('TMPD')) as d:
        f=d+'/t.ll'; open(f,'w').write(dump(H,bl,TL)); r=px2.run(f)
    return {'u':u[0],'ul':u[-1],'n':len(u),'p':p,**r}
if __name__=='__main__':
    print(len(jobs),'jobs',flush=True)
    if os.environ.get('COUNT'):
        for j in jobs[:20]: print(len(j[0]),j[0][0][:40],j[0][-1][:30],'@',j[1][:40])
        sys.exit()
    with Pool(int(os.environ.get('NP','5'))) as Pp, open(outf,'w') as f:
        for r in Pp.imap_unordered(run,jobs,chunksize=1):
            if r: f.write(json.dumps(r)+'\n'); f.flush()
