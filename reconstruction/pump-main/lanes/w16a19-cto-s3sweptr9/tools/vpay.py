#!/usr/bin/env python3
"""vpay.py <base m.ll> <lo> <hi> <outfile> [workers] [kind]: like w17a03 vscreen.py (one load/store made volatile = a
read_volatile/write_volatile shim at that IR site), but also reports the swept payload's registers (sweep-exit reloads,
the gate zero, the event store [r10-0x218]) so a pin that moves the payload into r9 is visible. Experiment only."""
import sys,os,re,subprocess,json,tempfile
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,os.path.dirname(__file__)); import oracle, bdis, relab as R
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
base,lo,hi,outf=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),sys.argv[4]
W=int(sys.argv[5]) if len(sys.argv)>5 else 3; kind=sys.argv[6] if len(sys.argv)>6 else 'load'
L=open(base).read().split('\n')
orig=oracle.orig_window()
def edit(i):
    l=L[i]
    if kind=='load':
        m=re.match(r'^(\s*%[\w.$"]+ = )load (?!volatile)(.*)$',l)
        return m.group(1)+'load volatile '+m.group(2) if m else None
    m=re.match(r'^(\s*)store (?!volatile)(.*)$',l)
    return m.group(1)+'store volatile '+m.group(2) if m else None
def pay(c):
    D=bdis.d(c); regs=[]
    for i in range(len(D)-2):
        o,s=D[i]
        if s.startswith('call') and 0x1d00<=o<=0x3e00:
            m1=re.match(r'ldxdw (r\d), \[r10-0x([0-9a-f]+)\]',D[i+1][1]); m2=re.match(r'ldxdw (r\d), \[r10-0x([0-9a-f]+)\]',D[i+2][1])
            if m1 and m2 and int(m2.group(2),16)==int(m1.group(2),16)+8: regs.append(m1.group(1)[1:])
    ev=[s[-1] for o,s in D if re.match(r'stxdw \[r10-0x218\], r\d',s)]
    return ''.join(regs),''.join(ev)
idx=[i for i in range(lo-1,hi-1) if edit(i)]
print(len(idx),'candidates',flush=True)
def run(i):
    T=L[:]; T[i]=edit(i)
    d=tempfile.mkdtemp(prefix='vp',dir=os.path.dirname(outf))
    p=d+'/m.ll'; open(p,'w').write('\n'.join(T))
    r=subprocess.run(['nice','-n','5',SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',p,'-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
    if r.returncode: res={'line':i+1,'err':r.stderr[-200:]}
    else:
        c=oracle.elf_fn(d+'/m.o',oracle.KEEP); rr,sd=oracle.metric(c,orig); ex,ev=pay(c)
        res={'line':i+1,'ratio':round(rr,5),'bytes':len(c),'M':R.M(c),'exits':ex,'ev218':ev,'src':L[i].strip()[:110]}
    subprocess.run(['rm','-rf',d])
    with open(outf,'a') as f: f.write(json.dumps(res)+'\n')
    return res
with ThreadPoolExecutor(W) as ex: list(ex.map(run,idx))
