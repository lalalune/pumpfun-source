#!/usr/bin/env python3
"""vscreen.py <base m.ll> <lo> <hi> <outfile> [workers] [kind]: for every load (kind=load) or store (kind=store) of execute
whose line number is in [lo,hi), make it volatile, llc, score. Appends JSON lines to outfile."""
import sys,os,re,subprocess,json,tempfile
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,os.path.dirname(__file__)); import oracle
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
base,lo,hi,outf=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),sys.argv[4]
W=int(sys.argv[5]) if len(sys.argv)>5 else 3; kind=sys.argv[6] if len(sys.argv)>6 else 'load'
L=open(base).read().split('\n')
orig=oracle.orig_window()
def edit(i):
    l=L[i]
    if kind=='load':
        m=re.match(r'^(\s*%[\w.$"]+ = )load (?!volatile)(.*)$',l)
        if not m: return None
        return m.group(1)+'load volatile '+m.group(2)
    elif kind=='memcpy':
        if 'call void @llvm.memcpy' not in l or not l.rstrip().endswith('i1 false)'): return None
        return l.rstrip()[:-len('i1 false)')]+'i1 true)'
    else:
        m=re.match(r'^(\s*)store (?!volatile)(.*)$',l)
        if not m: return None
        return m.group(1)+'store volatile '+m.group(2)
idx=[i for i in range(lo-1,hi-1) if edit(i)]
print(len(idx),'candidates',flush=True)
def run(i):
    T=L[:]; T[i]=edit(i)
    d=tempfile.mkdtemp(prefix='vs',dir=os.path.dirname(outf))
    p=d+'/m.ll'; open(p,'w').write('\n'.join(T))
    r=subprocess.run(['nice','-n','5',SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',p,'-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
    if r.returncode: res={'line':i+1,'err':r.stderr[-200:]}
    else:
        c=oracle.elf_fn(d+'/m.o',oracle.KEEP); rr,sd=oracle.metric(c,orig)
        res={'line':i+1,'ratio':round(rr,5),'bytes':len(c),'slots':sd,'src':L[i].strip()[:110]}
    subprocess.run(['rm','-rf',d])
    with open(outf,'a') as f: f.write(json.dumps(res)+'\n')
    return res
with ThreadPoolExecutor(W) as ex: list(ex.map(run,idx))
