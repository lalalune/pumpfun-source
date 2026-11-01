#!/usr/bin/env python3
"""fx.py <m.ll> <tag> [FORCE] : RAPRIO sticky llc (forces), score M/ratio/slots/bytes and window rotation. Experiment only."""
import sys,os,json,subprocess,tempfile,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); sys.path.insert(0,os.path.dirname(T)+'/t2')
import oracle
import winrot
OUT=os.path.dirname(T); LLC=OUT+'/llvmb/bin/llc'
O=oracle.orig_window(); OM=oracle.mask(O)
def run(ll,force='',keep=None,extra=()):
    env=dict(os.environ,RAPRIO_STICKY='1')
    if force: env['RAPRIO_FORCE']=force
    fd,obj=tempfile.mkstemp(suffix='.o',dir=OUT+'/an'); os.close(fd)
    p=subprocess.run([LLC,'-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',ll,'-filetype=obj','-o',obj,*extra],env=env,capture_output=True,text=True)
    if p.returncode: os.remove(obj); return {'force':force,'err':p.stderr[-300:]}
    b=oracle.elf_fn(obj,oracle.KEEP); os.remove(obj)
    if keep: open(keep,'wb').write(b)
    c=oracle.mask(b); M=sum(x.size for x in difflib.SequenceMatcher(None,OM,c,autojunk=False).get_matching_blocks())
    r,sd=oracle.metric(b,O); n,diff,cm=winrot.rot(b)
    return {'force':force,'M':M,'ratio':round(r,5),'slots':sd,'bytes':len(b),'rot':n}
if __name__=='__main__':
    ll,tag=sys.argv[1],sys.argv[2]; fs=sys.argv[3:] or ['']
    for f in fs:
        r=run(ll,f); r['tag']=tag; print(json.dumps(r),flush=True)
