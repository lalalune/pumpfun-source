#!/usr/bin/env python3
"""fscr.py <base m.ll> <cells.jsonl> <out.jsonl> [--par N] [--llc sdk|p] [--forces f1.bin,f2.bin,..]
llc-only screen of post-opt IR cells with a force-realisation metric (experiment only).
cell: {"id":..,"ops":[["rep",line,text],["ins",line,text],["del",line],["meta",text]], "env":{..}}
line = 0-based line index into the base file; "ins" inserts BEFORE that line; "meta" appends a module-level line.
Per cell: M (scorer metric vs the original), bytes, sig, and for each force bin F: segF = number of F's
main->F replacement segments (masked token runs, >=2 tokens) present in the cell, of segN total; eqF = cell == F."""
import sys,os,json,subprocess,tempfile,hashlib,difflib
from concurrent.futures import ThreadPoolExecutor
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle
OUT=os.path.dirname(T)
LLC={'sdk':os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin/llc'),
     'p':os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w16a20-cto-s3flagcolour/llvmb/bin/llc')}
LLCA=['-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections']
O=oracle.mask(oracle.orig_window())
OPT=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/rust/lib/rustlib/aarch64-apple-darwin/bin/opt')
PRE=False
def toks(b): return oracle.mask(b)
def mset(c):
    sm=difflib.SequenceMatcher(None,O,c,autojunk=False); S=set()
    for x in sm.get_matching_blocks(): S.update(range(x.a,x.a+x.size))
    return S
_HAVE=None
def apply(lines,ops):
    global _HAVE
    import re as _re
    if _HAVE is None:
        _HAVE=set(_re.findall(r'^declare [^@]*(@[\w.$-]+)\(','\n'.join(x for x in lines if x.startswith('declare')),_re.M))
    L=list(lines); meta=[]
    ins={}; rep={}; dele=set()
    for op in ops:
        if op[0]=='rep': rep[op[1]]=op[2]
        elif op[0]=='ins': ins.setdefault(op[1],[]).append(op[2])
        elif op[0]=='del': dele.add(op[1])
        elif op[0]=='meta':
            mm=_re.match(r'^declare [^@]*(@[\w.$-]+)\(',op[1])
            if mm and mm.group(1) in _HAVE: continue
            if op[1] not in meta: meta.append(op[1])
    out=[]
    for i,l in enumerate(L):
        if i in ins: out.extend(ins[i])
        if i in dele: continue
        out.append(rep.get(i,l))
    out.extend(meta)
    return '\n'.join(out)
class Force:
    """P = original tokens the force gains over main, N = original tokens it loses."""
    def __init__(self,main_set,path):
        self.name=os.path.basename(path).replace('.bin','')
        F=toks(open(path,'rb').read()); self.F=F; fs=mset(F)
        self.P=fs-main_set; self.N=main_set-fs
    def score(self,cs,c):
        return len(cs&self.P),len(self.P),len(self.N-cs),len(self.N),c==self.F
def main():
    a=sys.argv[1:]; base,cellf,outf=a[0],a[1],a[2]
    par=int(a[a.index('--par')+1]) if '--par' in a else 6
    llc=a[a.index('--llc')+1] if '--llc' in a else 'sdk'
    fl=a[a.index('--forces')+1].split(',') if '--forces' in a else []
    global PRE
    PRE='--pre' in a
    lines=open(base).read().split('\n')
    mb=a[a.index('--main')+1] if '--main' in a else OUT+'/fx/m0/fn.bin'
    ms=mset(toks(open(mb,'rb').read()))
    FS=[Force(ms,p) for p in fl]
    cells=[json.loads(l) for l in open(cellf) if l.strip()]
    done=set()
    if os.path.exists(outf):
        for l in open(outf):
            try: done.add(json.loads(l)['id'])
            except Exception: pass
    cells=[c for c in cells if c['id'] not in done]
    td=tempfile.mkdtemp(prefix='fscr_',dir=OUT+'/lx')
    def one(c):
        k=hashlib.sha1((c['id']+str(id(c))).encode()).hexdigest()[:12]
        p=f'{td}/{k}.ll'; o=f'{td}/{k}.o'
        open(p,'w').write(apply(lines,c['ops']))
        env=dict(os.environ); env.update(c.get('env',{}))
        if PRE:
            r=subprocess.run(['nice','-n','5',OPT,'-O3',p,'-S','-o',p+'.o3'],capture_output=True,text=True)
            os.remove(p)
            if r.returncode: return {'id':c['id'],'err':'opt:'+r.stderr[-300:]}
            open(p,'w').write(oracle.slim(open(p+'.o3').read())); os.remove(p+'.o3')
        r=subprocess.run(['nice','-n','5',LLC[llc],*LLCA,p,'-filetype=obj','-o',o],capture_output=True,text=True,env=env)
        os.remove(p)
        if r.returncode: return {'id':c['id'],'err':r.stderr[-300:]}
        b=oracle.elf_fn(o,oracle.KEEP); os.remove(o)
        t=toks(b); cs=mset(t)
        res={'id':c['id'],'M':len(cs),'bytes':len(b),'sig':hashlib.sha1(b''.join(t)).hexdigest()[:12]}
        for F in FS:
            p,pn,n,nn,eq=F.score(cs,t); res[F.name]=[p,pn,n,nn]
            if eq: res[F.name+'_eq']=True
        if 'save' in c: open(OUT+'/lx/'+c['save']+'.bin','wb').write(b)
        return res
    with ThreadPoolExecutor(par) as ex, open(outf,'a') as fo:
        for r in ex.map(one,cells):
            fo.write(json.dumps(r)+'\n'); fo.flush()
    import shutil; shutil.rmtree(td,ignore_errors=True)
if __name__=='__main__': main()
