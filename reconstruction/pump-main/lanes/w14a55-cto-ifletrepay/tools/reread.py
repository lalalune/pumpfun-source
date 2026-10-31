#!/usr/bin/env python3
"""reread.py <mn.ll> <out.jsonl> clones... [--pairs] : post-opt IR re-read oracle (experiment only).
For a clone pointer X (= load ptr, ptr SRC), variant 'X:f' re-loads X from SRC right before field f's load
(f in key,lam,data,owner,rent,f40,f41,f42), emulating the source path read `a.<acct>.<field>` inside an
`x`-bound AccountInfo literal. Runs llc like rx.py; prints ratio/bytes/M."""
import sys,os,re,subprocess,json,itertools,tempfile,difflib
from concurrent.futures import ThreadPoolExecutor
T=os.path.dirname(os.path.abspath(__file__)); g={}; exec(open(T+'/rx.py').read().split("OUT=os.environ")[0],g)
ORIG=g['orig_window'](); OM=g['mask'](ORIG)
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
a=sys.argv[1:]; mll,out=a[0],a[1]; pairs='--pairs' in a; clones=[x for x in a[2:] if not x.startswith('--')]
L=open(mll).read().split('\n')
OFF={'key':0,'lam':8,'data':16,'owner':24,'rent':32,'f40':40,'f41':41,'f42':42}
def locate(X):
    xi=next(i for i,l in enumerate(L) if l.startswith('  '+X+' = load ptr, ptr '))
    src=re.match(r'  \S+ = load ptr, ptr (%\S+?),',L[xi]).group(1)
    sites={}
    for i in range(xi+1,min(xi+200,len(L))):
        l=L[i]
        m=re.match(r'  (%\S+) = getelementptr inbounds i8, ptr '+re.escape(X)+r', i64 (\d+)$',l)
        if m:
            gname,off=m.group(1),int(m.group(2))
            for j in range(i+1,min(i+120,len(L))):
                if re.search(r'= load \S+, ptr '+re.escape(gname)+r',',L[j]): sites.setdefault(off,(j,gname)); break
        if re.match(r'  %\S+ = load ptr, ptr '+re.escape(X)+r', align 8',L[i]) and 0 not in sites: sites[0]=(i,X)
    return xi,src,sites
def build(edits):
    # edits: list of (X, off)
    ins={}; rep={}
    for k,(X,off) in enumerate(edits):
        xi,src,sites=locate(X); j,gname=sites[off]
        xdef=L[xi]; rr='%%rr%d'%(k,)
        new=[xdef.replace('  '+X+' = ','  '+rr+' = ',1)]
        if off: new.append('  %%rg%d = getelementptr inbounds i8, ptr %s, i64 %d'%(k,rr,off)); tgt='%%rg%d'%(k,)
        else: tgt=rr
        ins.setdefault(j,[]).extend(new)
        rep[j]=(rep.get(j,L[j])).replace('ptr '+gname+',','ptr '+tgt+',',1)
    res=[]
    for i,l in enumerate(L):
        if i in ins: res.extend(ins[i])
        res.append(rep.get(i,l))
    return '\n'.join(res)
def run(job):
    lab='+'.join('%s:%s'%(X,[k for k,v in OFF.items() if v==o][0]) for X,o in job)
    try: txt=build(job)
    except Exception as e: return {'lab':lab,'err':repr(e)[:200]}
    d=tempfile.mkdtemp(dir=os.path.dirname(os.path.abspath(out))); p=d+'/m.ll'; open(p,'w').write(txt)
    r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',p,'-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
    if r.returncode: subprocess.run(['rm','-rf',d]); return {'lab':lab,'err':r.stderr[-200:]}
    c=g['elf_fn'](d+'/m.o',g['KEEP']); subprocess.run(['rm','-rf',d])
    cm=g['mask'](c); sm=difflib.SequenceMatcher(None,OM,cm,autojunk=False); M=sum(b.size for b in sm.get_matching_blocks())
    sd=g['metric'](c,ORIG)[1] if len(c)==len(ORIG) else None
    return {'lab':lab,'ratio':round(2*M/(len(OM)+len(cm)),5),'bytes':len(c),'M':M,'slots':sd}
singles=[]
for X in clones:
    xi,src,sites=locate(X); print(X,src,{k:v[0] for k,v in sorted(sites.items())},file=sys.stderr)
    singles+= [(X,o) for o in sorted(sites)]
jobs=[[s] for s in singles]
if os.environ.get('JOBS'):
    jobs=[[(t.split(':')[0],int(t.split(':')[1])) for t in l.split(',')] for l in open(os.environ['JOBS']).read().split()]
elif pairs: jobs+= [list(p) for p in itertools.combinations(singles,2)]
NT=int(os.environ.get('NT','3'))
with ThreadPoolExecutor(NT) as ex, open(out,'w') as f:
    for r in ex.map(run,jobs): f.write(json.dumps(r)+'\n'); f.flush()
