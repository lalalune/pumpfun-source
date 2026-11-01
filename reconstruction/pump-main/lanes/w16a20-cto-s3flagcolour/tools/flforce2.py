#!/usr/bin/env python3
"""flforce2.py <m.ll> <force> [w ...]: like flforce.py but objects go through llcw.py (ares join-restore after RA), as
w16a08's forced pipeline does. SSC_WSET reaches the RA+SSC stage. Prints M/bytes natural and with flag:=w."""
import sys,os,json,re,subprocess,tempfile,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import flagcol as F, oracle
OUT=os.path.dirname(T); LLC=OUT+'/llvmb/bin/llc'
ll=sys.argv[1]; force=sys.argv[2]; ws=sys.argv[3:] or ['0.0005']
os.environ['RAPRIO_STICKY']='1'
if force and force!='-': os.environ['RAPRIO_FORCE']=force
else: os.environ.pop('RAPRIO_FORCE',None)
tmp=OUT+'/an/flf2.%d.mir'%os.getpid()
subprocess.run([LLC,*F.A,ll,'-stop-before=stack-slot-coloring','-o',tmp],capture_output=True)
mir=open(tmp).read().split('\n'); os.remove(tmp); flag=None
for i,l in enumerate(mir):
    m=re.match(r'\s+STB_V1 killed \$(r\d), killed \$(r\d), 165\b',l)
    if m:
        for j in range(i-1,max(i-6,0),-1):
            mm=re.match(r'\s+\$%s = LDD_V1 %%stack\.(\d+), 0\s*$'%m.group(1),mir[j])
            if mm: flag=int(mm.group(1)); break
        break
O=oracle.orig_window(); OM=oracle.mask(O)
def one(spec):
    env=dict(os.environ)
    if spec!='-': env['SSC_WSET']=spec
    fd,obj=tempfile.mkstemp(suffix='.o',dir=OUT+'/an'); os.close(fd)
    p=subprocess.run([sys.executable,T+'/llcw.py',*F.A,ll,'-filetype=obj','-o',obj],env=env,capture_output=True,text=True)
    if p.returncode: os.remove(obj); return ('err',p.stderr[-200:])
    b=oracle.elf_fn(obj,oracle.KEEP); os.remove(obj)
    sm=difflib.SequenceMatcher(None,OM,oracle.mask(b),autojunk=False)
    return (sum(x.size for x in sm.get_matching_blocks()),len(b))
out={'force':force[:50],'nf':len([x for x in force.split(',') if '=' in x]),'flag':flag}
for s in ['-']+[f'{flag}:={w}' for w in ws if flag]: out[s]=one(s)
print(json.dumps(out))
