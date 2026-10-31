#!/usr/bin/env python3
"""sscw.py <m.ll> <tag> [SPEC ...]: exact spill-colour oracle (experiment only). Runs the private SSC-hook llc
(llvmb/bin/llc, SSC_WSET="ss:=w,ss:+d") on a slimmed post-opt module and scores admin_cto with the measure.sh masking.
Each SPEC is one SSC_WSET string ('-' = none). Prints one JSON row per spec: M, ratio, slots, bytes, plus the colour order
of the top intervals (SS# in rank order) when DBG=1."""
import sys,os,json,subprocess,tempfile,re,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle
OUT=os.path.dirname(T); LLC=OUT+'/llvmb/bin/llc'
O=oracle.orig_window(); OM=oracle.mask(O)
def run(ll,spec,dbg=False,keep=None):
    env=dict(os.environ)
    if spec and spec!='-': env['SSC_WSET']=spec
    else: env.pop('SSC_WSET',None)
    fd,obj=tempfile.mkstemp(suffix='.o',dir=OUT+'/an'); os.close(fd)
    args=[LLC,'-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',ll,'-filetype=obj','-o',obj]
    if dbg: args+=['-debug-only=stack-slot-coloring']
    p=subprocess.run(args,env=env,capture_output=True,text=True)
    if p.returncode: os.remove(obj); return {'spec':spec,'err':p.stderr[-300:]}
    b=oracle.elf_fn(obj,oracle.KEEP); os.remove(obj)
    if keep: open(keep,'wb').write(b)
    c=oracle.mask(b); sm=difflib.SequenceMatcher(None,OM,c,autojunk=False)
    M=sum(x.size for x in sm.get_matching_blocks()); r,sd=oracle.metric(b,O)
    res={'spec':spec,'M':M,'ratio':round(r,5),'slots':sd,'bytes':len(b)}
    if dbg:
        order=[(int(a),int(c)) for a,c in re.findall(r'Assigning fi#(\d+) to fi#(\d+)',p.stderr)]
        res['order']=order[:20]
    return res
if __name__=='__main__':
    ll=sys.argv[1]; tag=sys.argv[2]; specs=sys.argv[3:] or ['-']
    for s in specs:
        r=run(ll,s,dbg=os.environ.get('DBG')=='1'); r['tag']=tag; print(json.dumps(r),flush=True)
