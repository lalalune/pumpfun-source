#!/usr/bin/env python3
"""mvscreen.py <base m.ll> <lo> <hi> <out.jsonl> [workers]: move+pin oracle. For every load of execute in [lo,hi), move it
(with its adjacent defining GEP) to the top of its block, before the block's last store, or before the terminator, and
make it volatile (= a read_volatile statement placed there in source). llc + score. Invalid moves are skipped."""
import sys,os,re,subprocess,json,tempfile
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,os.path.dirname(__file__)); import oracle
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
base,lo,hi,outf=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),sys.argv[4]; W=int(sys.argv[5]) if len(sys.argv)>5 else 3
L=open(base).read().split('\n'); orig=oracle.orig_window()
# blocks
blocks=[]; cur=None
for i in range(2500,6360):
    l=L[i-1]
    if re.match(r'^[\w.$"-]+:',l) or l.startswith('start:'):
        cur=[i,None]; blocks.append(cur)
    elif cur and re.match(r'^\s+(br|ret|switch|unreachable|resume)\b',l): cur[1]=i
def blk(i):
    for b in blocks:
        if b[1] and b[0]<i<=b[1]: return b
lre=re.compile(r'^(\s*)(%[\w.$"]+) = load (?!volatile)(\S+), ptr (%[\w.$"]+)(.*)$')
defre=re.compile(r'^\s*(%[\w.$"]+) = ')
def defs_in(a,b):
    d={}
    for j in range(a,b+1):
        m=defre.match(L[j-1]); 
        if m: d[m.group(1)]=j
    return d
cands=[]
for i in range(lo,hi):
    m=lre.match(L[i-1])
    if not m: continue
    b=blk(i)
    if not b: continue
    name,ptr=m.group(2),m.group(4)
    moved=[i]
    g=L[i-2]; gm=defre.match(g)
    if gm and gm.group(1)==ptr and 'getelementptr' in g: moved=[i-1,i]
    s,e=b
    lastst=max([j for j in range(s+1,e) if re.match(r'^\s*store ',L[j-1])] or [0])
    first=s+1
    while first<e and (L[first-1].strip().startswith('%') and ' = phi ' in L[first-1] or L[first-1].strip()=='' ): first+=1
    # operands of moved lines and uses of their results
    mdefs=[defre.match(L[j-1]).group(1) for j in moved]
    ops=set(re.findall(r'%[\w.$"]+',' '.join(L[j-1].split('=',1)[1] for j in moved)))-set(mdefs)
    blockdefs=defs_in(s+1,e)
    uses=[j for j in range(s+1,e+1) if j not in moved and any(re.search(re.escape(d)+r'\b',L[j-1]) for d in mdefs)]
    for tag,pos in (('top',first),('prestore',lastst),('preterm',e)):
        if not pos or pos in moved or (moved[0]<=pos<=moved[-1]): continue
        if any(blockdefs.get(o,0)>=pos for o in ops): continue
        if any(u<pos for u in uses): continue
        cands.append((i,tag,pos,moved))
print(len(cands),'candidates',flush=True)
def run(c):
    i,tag,pos,moved=c
    T=L[:]; seg=[T[j-1] for j in moved]
    m=lre.match(seg[-1]); seg[-1]=m.group(1)+m.group(2)+' = load volatile '+m.group(3)+', ptr '+m.group(4)+m.group(5)
    out=[]
    for j in range(1,len(T)+1):
        if j==pos: out.extend(seg)
        if j in moved: continue
        out.append(T[j-1])
    txt='\n'.join(out)
    for l in seg:
        mm=re.match(r'^\s*%(\d+) = ',l)
        if mm: txt=re.sub(r'%'+mm.group(1)+r'(?![\w.])','%mv'+mm.group(1),txt)
    d=tempfile.mkdtemp(prefix='mv',dir=os.path.dirname(os.path.abspath(outf)))
    open(d+'/m.ll','w').write(txt)
    r=subprocess.run(['nice','-n','5',SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
    if r.returncode: res={'line':i,'tag':tag,'err':r.stderr[-160:]}
    else:
        cb=oracle.elf_fn(d+'/m.o',oracle.KEEP); rr,sd=oracle.metric(cb,orig)
        res={'line':i,'tag':tag,'pos':pos,'ratio':round(rr,5),'bytes':len(cb),'slots':sd,'src':L[i-1].strip()[:90]}
    subprocess.run(['rm','-rf',d])
    with open(outf,'a') as f: f.write(json.dumps(res)+'\n')
with ThreadPoolExecutor(W) as ex: list(ex.map(run,cands))
