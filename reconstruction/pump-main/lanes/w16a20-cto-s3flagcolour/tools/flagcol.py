#!/usr/bin/env python3
"""flagcol.py <m.ll> <tag> <ss,ss..> [SPEC ...]: SSC weight-override oracle (experiment only). For each SSC_WSET spec, runs the
private llc with -debug-only=stack-slot-coloring, reports M/ratio/slots/bytes and, for each watched SS#, its weight rank,
assigned colour fi and final offset (colour k -> -2264-8k by FI order of used colours; checked against PEI when KEEPPEI=1)."""
import sys,os,json,subprocess,tempfile,re,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle
OUT=os.path.dirname(T); LLC=OUT+'/llvmb/bin/llc'
O=oracle.orig_window(); OM=oracle.mask(O)
A=['-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections']
def parse(log):
    pre=log.split('Color spill slot intervals:')[0]
    iv={int(a):float(w) for a,w in re.findall(r'^SS#(\d+) .*?weight:(\S+)$',pre,re.M)}
    asg={int(a):int(c) for a,c in re.findall(r'Assigning fi#(\d+) to fi#(\d+)',log)}
    return iv,asg
def run(ll,spec,watch,extra=()):
    env=dict(os.environ)
    if spec and spec!='-': env['SSC_WSET']=spec
    else: env.pop('SSC_WSET',None)
    fd,obj=tempfile.mkstemp(suffix='.o',dir=OUT+'/an'); os.close(fd)
    p=subprocess.run([LLC,*A,ll,'-filetype=obj','-o',obj,'-debug-only=stack-slot-coloring',*extra],env=env,capture_output=True,text=True)
    if p.returncode: os.remove(obj); return {'spec':spec,'err':p.stderr[-300:]}
    b=oracle.elf_fn(obj,oracle.KEEP); os.remove(obj)
    c=oracle.mask(b); sm=difflib.SequenceMatcher(None,OM,c,autojunk=False)
    M=sum(x.size for x in sm.get_matching_blocks()); r,sd=oracle.metric(b,O)
    iv,asg=parse(p.stderr)
    cols=sorted(set(asg.get(s,s) for s in iv))
    rank={s:i for i,s in enumerate(sorted(iv,key=lambda s:-iv[s]))}
    res={'spec':spec,'M':M,'ratio':round(r,5),'slots':sd,'bytes':len(b),'ncol':len(cols)}
    for s in watch:
        if s not in iv: res[f'SS{s}']=None; continue
        fi=asg.get(s,s); k=cols.index(fi)
        res[f'SS{s}']=dict(w=round(iv[s],5),rank=rank[s],fi=fi,k=k,off=-2264-8*k)
    return res,b
if __name__=='__main__':
    ll=sys.argv[1]; tag=sys.argv[2]; watch=[int(x) for x in sys.argv[3].split(',') if x]; specs=sys.argv[4:] or ['-']
    for s in specs:
        r=run(ll,s,watch)
        if isinstance(r,tuple): r=r[0]
        r['tag']=tag; print(json.dumps(r),flush=True)
