#!/usr/bin/env python3
"""padscan.py <m.ll> <out.jsonl> [N]: oracle upper bound: insert N volatile i64 stores to a dummy global at the top of each
execute block (after phis), llc, score at the resulting size. Experiment only."""
import sys,os,re,subprocess,json,concurrent.futures as cf
sys.path.insert(0,os.path.dirname(__file__)); import oracle
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
src,out=sys.argv[1],sys.argv[2]; N=int(sys.argv[3]) if len(sys.argv)>3 else 30
t=open(src).read()
s=t.index('define hidden { i64, ptr } @_ZN14pump_recovered9admin_cto7execute'); e=t.index('\n}\n',s)
body=t[s:e]
labels=re.findall(r'\n([\w.$"\-]+):',body)
if os.environ.get("ONLY"): labels=[l for l in labels if l in os.environ["ONLY"].split(",")]
D=os.path.dirname(os.path.abspath(out))+'/pad'; os.makedirs(D,exist_ok=True)
orig=oracle.orig_window()
def run(lab):
    b=body; i=b.index('\n'+lab+':'); j=b.index('\n',i+1)+1
    while re.match(r'\s+%\S+ = phi ',b[j:b.index('\n',j)]): j=b.index('\n',j)+1
    pad=''.join('  store volatile i64 0, ptr @__padg, align 8\n' for _ in range(N))
    m=t[:s]+b[:j]+pad+b[j:]+t[e:]
    m=m+'\n@__padg = global i64 0, align 8\n'
    f=D+'/'+re.sub(r'\W','_',lab); open(f+'.ll','w').write(m)
    r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',f+'.ll','-filetype=obj','-o',f+'.o'],capture_output=True,text=True)
    os.remove(f+'.ll')
    if r.returncode: return {'lab':lab,'err':r.stderr[-200:]}
    c=oracle.elf_fn(f+'.o',oracle.KEEP); os.remove(f+'.o'); rr,sd=oracle.metric(c,orig)
    return {'lab':lab,'ratio':round(rr,5),'bytes':len(c),'slots':sd}
with cf.ThreadPoolExecutor(6) as ex, open(out,'w') as fo:
    for r in ex.map(run,labels): fo.write(json.dumps(r)+'\n'); fo.flush()
