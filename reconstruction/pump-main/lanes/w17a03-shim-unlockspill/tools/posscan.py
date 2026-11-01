import re,subprocess,os,sys,json,tempfile
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,'t2'); import oracle
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
base=sys.argv[1]; src=[int(x) for x in sys.argv[2].split(',')]; lo,hi=int(sys.argv[3]),int(sys.argv[4]); outf=sys.argv[5]; ren=sys.argv[6].split(',') if len(sys.argv)>6 and sys.argv[6] else []
L=open(base).read().split('\n'); orig=oracle.orig_window()
def ok_pos(p):
    prev=L[p-2].strip(); cur=L[p-1]
    if prev=='' or prev.endswith(':') or re.match(r'^[\w."$-]+:',L[p-2]): 
        # first instr of a block: allowed unless phi follows
        return ' = phi ' not in cur
    if re.match(r'^\s+(br|ret|switch|unreachable)\b',L[p-2]): return False
    return cur.startswith('  ') and ' = phi ' not in cur
def run(p):
    T=L[:]; seg=[T[j-1] for j in src]; seg[-1]=seg[-1].replace(' = load ',' = load volatile ',1)
    out=[]
    for j in range(1,len(T)+1):
        if j==p: out.extend(seg)
        if j in src: continue
        out.append(T[j-1])
    txt='\n'.join(out)
    for n in ren: txt=re.sub(r'%'+n+r'(?![\w.])','%mv'+n,txt)
    d=tempfile.mkdtemp(prefix='ps',dir='scr'); open(d+'/m.ll','w').write(txt)
    r=subprocess.run(['nice','-n','5',SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
    if r.returncode: res={'pos':p,'err':r.stderr[-120:]}
    else:
        cb=oracle.elf_fn(d+'/m.o',oracle.KEEP); rr,sd=oracle.metric(cb,orig); res={'pos':p,'ratio':round(rr,5),'bytes':len(cb),'slots':sd,'at':L[p-1].strip()[:80]}
    subprocess.run(['rm','-rf',d])
    with open(outf,'a') as f: f.write(json.dumps(res)+'\n')
P=[p for p in range(lo,hi) if p not in src and ok_pos(p)]
print(len(P),flush=True)
with ThreadPoolExecutor(3) as ex: list(ex.map(run,P))
