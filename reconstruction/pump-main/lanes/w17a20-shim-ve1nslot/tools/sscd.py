#!/usr/bin/env python3
"""sscd.py <m.ll|post-opt module> <name> [--sa SECS]: build ssc/<name> (slim m.ll, ssc.log, ns.log, ns.o, main.o) with the
private llc, then report: M, votes on current colour, entry-interval colours vs the original's, votes-ideal bound,
optional annealing ceiling. Experiment only."""
import sys,os,subprocess,json,re,difflib,collections,random,math,time
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
OUT=os.path.dirname(T)
sys.path.insert(0,OUT+'/t6'); import oracle
import sscsim, votes
PL=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w16a20-cto-s3flagcolour/llvmb/bin/llc')
LLCA=['-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections']
OBJ=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin/llvm-objdump')
def mk(src,name):
    d=f'{OUT}/ssc/{name}'; os.makedirs(d,exist_ok=True)
    t=open(src).read()
    if 'define' in t and t.count('\ndefine ')>1: t=oracle.slim(t)
    open(d+'/m.ll','w').write(t)
    r=subprocess.run([PL,*LLCA,d+'/m.ll','-filetype=obj','-o',d+'/main.o','-debug-only=stack-slot-coloring'],capture_output=True,text=True)
    open(d+'/ssc.log','w').write(r.stderr)
    r=subprocess.run([PL,*LLCA,d+'/m.ll','-filetype=obj','-o',d+'/ns.o','-no-stack-slot-sharing','-debug-only=stack-slot-coloring'],capture_output=True,text=True)
    open(d+'/ns.log','w').write(r.stderr)
    return d
def entry(S,k):
    """first spill store of each interval within the first 140 instructions of the no-share code -> (insn, ss, colour)"""
    r=subprocess.run([OBJ,'-d','--no-show-raw-insn','--section=.text._ZN14pump_recovered9admin_cto7execute17h3bd6d7f34f2e30d7E',S.d+'/ns.o'],capture_output=True,text=True)
    out=[]; seen=set()
    for l in [l for l in r.stdout.splitlines() if re.match(r'\s*[0-9]+:',l)][:140]:
        m=re.search(r'stxdw \[r10 - 0x([0-9a-f]+)\], (r\d)',l)
        if m:
            off=-int(m.group(1),16)
            if off in S.ns_off and S.ns_off[off] not in seen:
                s=S.ns_off[off]; seen.add(s); out.append((l.split(':')[0].strip(),m.group(2),s,k[s],round(S.W[s],4)))
    return out
def report(d,sa=0):
    S,V,n=votes.run(d); S.d=d
    k=S.colour(S.order); m,r=S.M(S.relabel(k))
    good=sum(V[s][k[s]] for s in V); tot=sum(sum(V[s].values()) for s in V)
    kk=dict(k)
    for s,c in V.items():
        if c: kk[s]=c.most_common(1)[0][0]
    mi,_=S.M(S.relabel(kk))
    res={'M':m,'bytes':len(S.ns),'votes_ok':good,'votes_tot':tot,'votes_ideal':mi,'ncol':max(k.values())+1}
    res['entry']=[(i,reg,s,'k%d'%c,'orig:'+('/'.join('k%d'%x for x,_ in V[s].most_common(2)) if V.get(s) else '-'),w) for i,reg,s,c,w in entry(S,k)]
    if sa:
        random.seed(1); cur=list(S.order); mm=m; best=m; cache={}; t0=time.time()
        while time.time()-t0<sa:
            temp=2.0*(1-(time.time()-t0)/sa)+0.05
            o=list(cur); i=random.randrange(len(o)); s=o.pop(i)
            j=min(len(o),max(0,i+int(random.gauss(0,12)))) if random.random()<0.7 else random.randrange(len(o)+1)
            o.insert(j,s); kq=S.colour(o); key=tuple(kq[x] for x in S.fis)
            if key in cache: q=cache[key]
            else: q=S.M(S.relabel(kq))[0]; cache[key]=q
            if q>=mm or random.random()<math.exp((q-mm)/temp):
                cur,mm=o,q; best=max(best,q)
        res['sa']=best
    return res
if __name__=='__main__':
    a=sys.argv[1:]; sa=0
    if '--sa' in a: i=a.index('--sa'); sa=float(a[i+1]); a=a[:i]+a[i+2:]
    d=mk(a[0],a[1]); print(json.dumps(report(d,sa)))
