#!/usr/bin/env python3
"""irinst.py <mn.ll> <out.jsonl>: experiment-only post-opt IR INSTRUCTION-order scan of admin_cto::execute outside
validate. For each pure instruction (gep/load/icmp/cast/extractvalue/arith/select/pure intrinsic) in a block: hoist it to
just after its last same-block operand def (loads: also after the last call/store/memcpy/memset), or sink it to just
before its first same-block use (loads: before the first call/store). Models statement / let-binding order. px2.py."""
import sys,re,json,os,tempfile
from multiprocessing import Pool
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import px2
exec(open(T+'/irscan.py').read().split("src,outf=sys.argv")[0])
src,outf=sys.argv[1:3]
H,BL,TL=load(open(src).read())
names=[b[0] for b in BL]; v0,v1=names.index('bb6.i'),names.index('bb65.i')
PURE=re.compile(r'^\s*(%[\w.$"-]+) = (getelementptr|load|icmp|zext|sext|trunc|ptrtoint|inttoptr|extractvalue|insertvalue|select|add|sub|and|or|xor|shl|lshr|ashr|mul|call i64 @llvm\.usub\.sat|call i64 @llvm\.umin|call i64 @llvm\.umax)\b')
def isbar(l):
    s=l.strip()
    if s.startswith('store ') or '@llvm.memcpy' in s or '@llvm.memset' in s: return True
    if re.search(r'\bcall\b',s) and not re.search(r'@llvm\.(lifetime|experimental\.noalias|usub|umin|umax|assume)',s): return True
    return False
def defs(l):
    m=re.match(r'^\s*(%[\w.$"-]+) =',l); return m.group(1) if m else None
def uses(l): 
    rhs=l.split('=',1)[1] if defs(l) else l
    return set(re.findall(r'%[\w.$-]+|%"[^"]+"',rhs))
jobs=[]
for bi,(n,lines) in enumerate(BL):
    if v0<=bi<=v1: continue
    body=list(range(1,len(lines)))
    # skip label line 0; skip phis and terminator and comments/blank
    ins=[k for k in body if lines[k].strip() and not lines[k].strip().startswith(';')]
    if not ins: continue
    term=ins[-1]; ins=[k for k in ins[:-1] if ' = phi ' not in lines[k]]
    firstnonphi=min([k for k in body if lines[k].strip() and ' = phi ' not in lines[k]]+[term])
    for k in ins:
        l=lines[k]; m=PURE.match(l)
        if not m: continue
        d=m.group(1); u=uses(l); isload=m.group(2)=='load'
        # hoist target
        lo=firstnonphi
        for j in ins:
            if j>=k: break
            if defs(lines[j]) in u or (isload and isbar(lines[j])): lo=j+1
        ALL=os.environ.get('ALLPOS')
        if ALL and (not isload)!=bool(os.environ.get('NONLOAD')): continue
        if ALL:
            for t in range(lo,k): jobs.append((bi,k,t))
        elif lo<k and any(lines[j].strip() and not lines[j].strip().startswith(';') for j in range(lo,k)): jobs.append((bi,k,lo))
        hi=term
        for j in ins+[term]:
            if j<=k: continue
            if d in uses(lines[j]) or (isload and isbar(lines[j])): hi=j; break
        if ALL:
            for t in range(k+2,hi+1): jobs.append((bi,k,t))
        elif hi>k+1: jobs.append((bi,k,hi))
def run(j):
    bi,k,t=j; bl=[list(b) for b in BL]; L=list(bl[bi][1]); x=L[k]
    if t<k: L=L[:t]+[x]+L[t:k]+L[k+1:]
    else: L=L[:k]+L[k+1:t]+[x]+L[t:]
    bl[bi]=[bl[bi][0],L]
    with tempfile.TemporaryDirectory(dir=os.environ.get('TMPD')) as d:
        f=d+'/t.ll'; open(f,'w').write(dump(H,bl,TL)); r=px2.run(f)
    return {'b':BL[bi][0][:60],'k':k,'t':t,'ins':x.strip()[:120],**r}
if __name__=='__main__':
    print(len(jobs),'jobs',flush=True)
    if os.environ.get('COUNT'): sys.exit()
    with Pool(int(os.environ.get('NP','5'))) as P, open(outf,'w') as f:
        for r in P.imap_unordered(run,jobs,chunksize=2):
            if r: f.write(json.dumps(r)+'\n'); f.flush()
