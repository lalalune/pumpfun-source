#!/usr/bin/env python3
"""rscan.py <mn.ll> <out.jsonl> <threads> <clone...>: re-read oracle for hand/inlined AccountInfo clones.
For each clone X (= load ptr, ptr G) and each field read (key, owner, rent, f40, f41, f42, lam, data), re-load X from G
right before that field's read and use the re-load (source form: the field read as a.<acct>.<field>). Singles and
within-clone pairs. Experiment only."""
import sys,os,re,subprocess,json,itertools,tempfile
from concurrent.futures import ThreadPoolExecutor
T=os.path.dirname(os.path.abspath(__file__)); src=open(T+'/rx.py').read(); g={}; exec(src.split("OUT=os.environ")[0],g)
ORIG=g['orig_window']()
mll,out,NT=sys.argv[1],sys.argv[2],int(sys.argv[3]); clones=sys.argv[4:]
L=open(mll).read().split('\n')
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
def info(X):
    xi=next(i for i,l in enumerate(L) if l.startswith('  '+X+' = '))
    G=re.match(r'  \S+ = load ptr, ptr (%\S+), ',L[xi]).group(1)
    def find(pat):
        for i in range(xi,xi+120):
            if re.match(pat,L[i]): return i
    f={}
    k=find(r'  %\S+ = load ptr, ptr '+re.escape(X)+r', align 8')
    if k: f['key']=[k]
    for nm,o in (('lam',8),('data',16),('owner',24),('rent',32),('f40',40),('f41',41),('f42',42)):
        i=find(r'  (%\S+) = getelementptr inbounds i8, ptr '+re.escape(X)+r', i64 '+str(o)+'$')
        if i: f[nm]=[i,i+1]
    return xi,G,f
def build(jobs):
    ins={}; rep={}
    for n,(X,nm) in enumerate(jobs):
        xi,G,f=info(X); lines=f[nm]; nn='%rr'+str(n)+'.'+X.lstrip('%').replace('"','')
        d=L[xi].replace('  '+X+' = ','  '+nn+' = ',1)
        ins.setdefault(lines[0],[]).append(d)
        for i in lines: rep[i]=(X,nn)
    res=[]
    for i,l in enumerate(L):
        if i in ins: res.extend(ins[i])
        if i in rep:
            X,nn=rep[i]; l=l.replace('ptr '+X+',','ptr '+nn+',')
        res.append(l)
    return '\n'.join(res)
def run(jobs):
    lab='+'.join(X+'@'+nm for X,nm in jobs)
    d=tempfile.mkdtemp(dir=os.path.dirname(os.path.abspath(out))); p=d+'/m.ll'; open(p,'w').write(build(jobs))
    r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',p,'-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
    if r.returncode: subprocess.run(['rm','-rf',d]); return {'lab':lab,'err':r.stderr[-200:]}
    c=g['elf_fn'](d+'/m.o',g['KEEP']); rr,sd=g['metric'](c,ORIG); subprocess.run(['rm','-rf',d])
    return {'lab':lab,'ratio':round(rr,5),'bytes':len(c),'slots':sd}
J=[[]]
for X in clones:
    xi,G,f=info(X); fs=sorted(f)
    J+=[[(X,a)] for a in fs]
    if os.environ.get('PAIRS'): J+=[[(X,a),(X,b)] for a,b in itertools.combinations(fs,2)]
with ThreadPoolExecutor(NT) as ex, open(out,'w') as fo:
    for r in ex.map(run,J): fo.write(json.dumps(r)+'\n'); fo.flush()
