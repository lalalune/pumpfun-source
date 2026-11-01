#!/usr/bin/env python3
"""winscan.py <base.ll> <lo> <hi> <out.jsonl> [maxback]: move each load (with its adjacent GEP) of [lo,hi) EARLIER into an
Rc inc_strong window (just before the strong-count store) of a preceding clone, volatile. Realisable in source with a manual
Rc increment that reads the field volatile between the count load and the store, keeping the value in a local for its
later field position."""
import re,subprocess,os,sys,json,tempfile
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,os.path.dirname(__file__)); import oracle
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
base,lo,hi,outf=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),sys.argv[4]; maxback=int(sys.argv[5]) if len(sys.argv)>5 else 120
L=open(base).read().split('\n'); orig=oracle.orig_window()
defre=re.compile(r'^\s*(%[\w.$"]+) = ')
defline={}
for i in range(2500,6360):
    m=defre.match(L[i-1])
    if m: defline[m.group(1)]=i
wins=[i for i in range(lo-200,hi) if re.match(r'^\s*store i64 %strong1[\w.]*, ptr ',L[i-1])]
lre=re.compile(r'^(\s*)(%[\w.$"]+) = load (?:volatile )?(\S+), ptr (%[\w.$"]+)(.*)$')
cands=[]
for i in range(lo,hi):
    m=lre.match(L[i-1])
    if not m or m.group(3)=='i64' and 'self.val' in m.group(2): continue
    ptr=m.group(4); moved=[i]
    gm=defre.match(L[i-2])
    if gm and gm.group(1)==ptr and 'getelementptr' in L[i-2]:
        moved=[i-1,i]; basep=re.search(r'ptr (%[\w.$"]+), i64',L[i-2]); basep=basep.group(1) if basep else None
    else: basep=ptr
    bdef=defline.get(basep,0)
    for w in wins:
        if w<i-maxback or w>=moved[0] or w<=bdef: continue
        cands.append((i,w,moved))
print(len(cands),flush=True)
def run(c):
    i,w,moved=c
    T=L[:]; seg=[T[j-1] for j in moved]; seg[-1]=re.sub(r' = load (?!volatile)',' = load volatile ',seg[-1],count=1)
    out=[]
    for j in range(1,len(T)+1):
        if j==w: out.extend(seg)
        if j in moved: continue
        out.append(T[j-1])
    txt='\n'.join(out)
    for l in seg:
        mm=re.match(r'^\s*%(\d+) = ',l)
        if mm: txt=re.sub(r'%'+mm.group(1)+r'(?![\w.])','%mv'+mm.group(1),txt)
    d=tempfile.mkdtemp(prefix='ws',dir=os.path.dirname(os.path.abspath(outf))); open(d+'/m.ll','w').write(txt)
    r=subprocess.run(['nice','-n','5',SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
    if r.returncode: res={'line':i,'win':w,'err':r.stderr[-120:]}
    else:
        cb=oracle.elf_fn(d+'/m.o',oracle.KEEP); rr,sd=oracle.metric(cb,orig)
        res={'line':i,'win':w,'ratio':round(rr,5),'bytes':len(cb),'slots':sd,'src':L[i-1].strip()[:80]}
    subprocess.run(['rm','-rf',d])
    with open(outf,'a') as f: f.write(json.dumps(res)+'\n')
with ThreadPoolExecutor(3) as ex: list(ex.map(run,cands))
