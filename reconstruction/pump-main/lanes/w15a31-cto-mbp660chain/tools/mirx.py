#!/usr/bin/env python3
"""mirx.py <src rx> <out name> [succ:BB:a,b ...]: edit successor probabilities (BB numbers, hex-free floats) in the pre-MBP MIR,
then llc -start-before=block-placement, score (ratio, bytes, M). Experiment oracle only."""
import sys,os,re,subprocess,json,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle
OUT=os.path.dirname(T); D=os.path.expanduser('~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin')
src,name,*eds=sys.argv[1:]
t=open(f'{OUT}/rx/{src}/pre.mir').read()
for e in eds:
    k,bb,v=e.split(':',2)
    if k=='succ':
        ps=[float(x) for x in v.split(',')]
        m=re.search(rf'^  bb\.{bb}\.?[^\n]*:\n    successors: ([^\n]*)\n',t,re.M); s=re.findall(r'%bb\.(\d+)\(0x[0-9a-f]+\)',m[1]); assert len(s)==len(ps),(s,ps)
        tot=sum(ps); hx=[int(round(p/tot*2**31)) for p in ps]; hx[-1]=2**31-sum(hx[:-1])
        new=', '.join(f'%bb.{x}(0x{h:08x})' for x,h in zip(s,hx)); t=t[:m.start(1)]+new+t[m.end(1):]
    elif k=='sub':  # sub:BB:old=>new  (within block BB body)
        old,new=v.split('=>'); m=re.search(rf'^  bb\.{bb}\.?[^\n]*:\n((?:    [^\n]*\n|  \n)*)',t,re.M); body=m[1]; assert body.count(old)==1,(bb,old); t=t[:m.start(1)]+body.replace(old,new)+t[m.end(1):]
d=f'{OUT}/rx/{name}'; os.makedirs(d,exist_ok=True); open(d+'/pre.mir','w').write(t)
args=['-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections','-start-before=block-placement',d+'/pre.mir','-filetype=obj','-o',d+'/m.o']
if os.environ.get('BP'): args+=['-debug-only=block-placement']
r=subprocess.run([D+'/llc',*args],capture_output=True,text=True)
if os.environ.get('BP'): open(d+'/bp.txt','w').write(r.stderr)
if r.returncode: print(r.stderr[-2000:]); sys.exit(1)
cand=oracle.elf_fn(d+'/m.o',oracle.KEEP); open(d+'/fn.bin','wb').write(cand)
O=oracle.orig_window(); ot=oracle.mask(O); ct=oracle.mask(cand)
M=sum(b.size for b in difflib.SequenceMatcher(None,ot,ct,autojunk=False).get_matching_blocks())
rr,sd=oracle.metric(cand,O)
print(json.dumps({'name':name,'ratio':round(rr,5),'bytes':len(cand),'slots_diff':sd,'M':M}))
