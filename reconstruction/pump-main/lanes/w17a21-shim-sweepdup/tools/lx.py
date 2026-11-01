#!/usr/bin/env python3
"""lx.py <m.ll> <name> [--llc sdk|dbg|p] [-- extra llc args]: llc-only oracle on a post-opt slim module (experiment only)."""
import sys,os,subprocess,json,hashlib,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle
OUT=os.path.dirname(T)
LLCS={'sdk':os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin/llc'),
      'dbg':os.path.expanduser('~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin/llc'),
      'p':os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w16a20-cto-s3flagcolour/llvmb/bin/llc')}
LLCA=['-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections']
_O=None
def O():
    global _O
    if _O is None: _O=oracle.mask(oracle.orig_window())
    return _O
_B=None
def BASE():
    global _B
    if _B is None: _B=oracle.mask(oracle.elf_fn(os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so'),oracle.KEEP))
    return _B
def score_bin(b):
    c=oracle.mask(b); sm=difflib.SequenceMatcher(None,O(),c,autojunk=False)
    M=sum(x.size for x in sm.get_matching_blocks())
    ob=b''.join(O()); cb=b''.join(c)
    sd=sum(1 for i in range(0,len(ob),8) if ob[i:i+8]!=cb[i:i+8]) if len(ob)==len(cb) else None
    return {'M':M,'ratio':round(2*M/(len(O())+len(c)),5),'bytes':len(b),'slots':sd,'eq_main':c==BASE(),'sig':hashlib.sha1(b''.join(c)).hexdigest()[:12]}
def run(path,name,llc='sdk',extra=(),env=None,keepobj=False):
    d=os.path.join(OUT,'lx',name); os.makedirs(d,exist_ok=True)
    r=subprocess.run(['nice','-n','5',LLCS[llc],*LLCA,path,'-filetype=obj','-o',d+'/m.o',*extra],capture_output=True,text=True,env=env)
    open(d+'/llc.err','w').write(r.stderr)
    if r.returncode: return {'name':name,'err':r.stderr[-800:]}
    b=oracle.elf_fn(d+'/m.o',oracle.KEEP); open(d+'/fn.bin','wb').write(b)
    if not keepobj: os.remove(d+'/m.o')
    res={'name':name}; res.update(score_bin(b)); return res
if __name__=='__main__':
    a=sys.argv[1:]; extra=[]
    if '--' in a: k=a.index('--'); extra=a[k+1:]; a=a[:k]
    llc='sdk'
    if '--llc' in a: k=a.index('--llc'); llc=a[k+1]; del a[k:k+2]
    print(json.dumps(run(a[0],a[1],llc,extra)))
