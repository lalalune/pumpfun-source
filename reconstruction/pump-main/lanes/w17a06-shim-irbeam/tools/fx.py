#!/usr/bin/env python3
"""fx.py: fast raw-IR oracle on a pre-slimmed module (experiment only).
score(text,name) -> dict(M,bytes,ratio,ok,...). opt -O3 (SDK rustlib opt) -> slim -> llc (fastbuild flags) -> M."""
import sys,os,subprocess,json,time,difflib,tempfile,shutil
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle
OUT=os.environ.get('LANE_OUT',os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w17a06-shim-irbeam'))
OPT=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/rust/lib/rustlib/aarch64-apple-darwin/bin/opt')
LLC=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin/llc')
LLCA=['-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections']
_O=None
def O():
    global _O
    if _O is None: _O=oracle.mask(oracle.orig_window())
    return _O
def Mof(b):
    c=oracle.mask(b); sm=difflib.SequenceMatcher(None,O(),c,autojunk=False)
    m=sum(x.size for x in sm.get_matching_blocks()); return m, 2*m/(len(O())+len(c))
def run(text,name,keep=False,mp=False,nice=True):
    d=os.path.join(OUT,'fx',name); os.makedirs(d,exist_ok=True); t0=time.time()
    open(d+'/in.ll','w').write(text)
    pre=['nice','-n','5'] if nice else []
    r=subprocess.run(pre+[OPT,'-O3',d+'/in.ll','-S','-o',d+'/o3.ll'],capture_output=True,text=True)
    if r.returncode: return {'name':name,'err':'opt:'+r.stderr[-600:]}
    o=open(d+'/o3.ll').read(); m=oracle.slim(o); open(d+'/m.ll','w').write(m)
    if not keep: os.remove(d+'/in.ll'); os.remove(d+'/o3.ll')
    r=subprocess.run(pre+[LLC,*LLCA,d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
    if r.returncode: return {'name':name,'err':'llc:'+r.stderr[-600:]}
    b=oracle.elf_fn(d+'/m.o',oracle.KEEP); open(d+'/fn.bin','wb').write(b); os.remove(d+'/m.o')
    M,ratio=Mof(b)
    import hashlib
    res={'name':name,'M':M,'ratio':round(ratio,5),'bytes':len(b),'secs':round(time.time()-t0,1),'sig':hashlib.sha1(b''.join(oracle.mask(b))).hexdigest()[:12]}
    if mp:
        q=subprocess.run(['python3',T+'/mp.py','mp_'+name,d+'/m.ll'],capture_output=True,text=True)
        try:
            j=json.loads(q.stdout.strip().splitlines()[-1]); res.update({k:j[k] for k in ('Mperm','Mhc') if k in j})
        except Exception as e: res['mperr']=(q.stdout[-200:]+q.stderr[-200:])
    return res
if __name__=='__main__':
    a=sys.argv[1:]; p=a[0]; name=a[1]; mp='--mp' in a
    print(json.dumps(run(open(p).read(),name,keep='--keep' in a,mp=mp)))
