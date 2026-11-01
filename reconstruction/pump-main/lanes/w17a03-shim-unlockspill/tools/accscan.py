import re,subprocess,os,sys,json,tempfile
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,'t2'); import oracle
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
base,lo,hi,outf=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),sys.argv[4]
L=open(base).read().split('\n'); orig=oracle.orig_window()
# account pointer reload loads: load ptr, ptr %G where %G = gep %_270, K  (or %_270 itself)
geps={}
for i in range(2500,6360):
    m=re.match(r'^\s*(%[\w.$"]+) = getelementptr inbounds i8, ptr %_270, i64 (\d+)$',L[i-1])
    if m: geps[m.group(1)]=int(m.group(2))
lds=[i for i in range(lo,hi) if (m:=re.match(r'^\s*(%[\w.$"]+) = load (?!volatile)ptr, ptr (%[\w.$"]+),',L[i-1])) and (m.group(2) in geps or m.group(2)=='%_270')]
tops=[]
for i in range(lo,hi):
    if re.match(r'^[\w."$-]+:',L[i-1]) and ' = phi ' not in L[i]: tops.append(i+1)
cands=[(i,p) for i in lds for p in tops if p<i]
print(len(lds),'loads',len(tops),'tops',len(cands),'cands',flush=True)
def run(c):
    i,p=c
    T=L[:]; seg=T[i-1].replace(' = load ',' = load volatile ',1)
    out=[]
    for j in range(1,len(T)+1):
        if j==p: out.append(seg)
        if j==i: continue
        out.append(T[j-1])
    d=tempfile.mkdtemp(prefix='ac',dir='scr'); open(d+'/m.ll','w').write('\n'.join(out))
    r=subprocess.run(['nice','-n','5',SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
    if r.returncode: res={'line':i,'pos':p,'err':r.stderr[-100:]}
    else:
        cb=oracle.elf_fn(d+'/m.o',oracle.KEEP); rr,sd=oracle.metric(cb,orig); res={'line':i,'pos':p,'ratio':round(rr,5),'bytes':len(cb),'slots':sd,'src':L[i-1].strip()[:60]}
    subprocess.run(['rm','-rf',d])
    with open(outf,'a') as f: f.write(json.dumps(res)+'\n')
with ThreadPoolExecutor(3) as ex: list(ex.map(run,cands))
