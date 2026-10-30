#!/usr/bin/env python3
"""padgreedy.py <m.ll> <rounds> <N> <log>: greedy distributed padding upper bound (oracle only): each round adds N volatile
global stores at the top of the best block. Prints the chosen block and ratio per round."""
import sys,os,re,subprocess,json,concurrent.futures as cf
sys.path.insert(0,os.path.dirname(__file__)); import oracle
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
src,R,N,log=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),sys.argv[4]
t=open(src).read()+'\n@__padg = global i64 0, align 8\n'
orig=oracle.orig_window(); D=os.path.dirname(os.path.abspath(log))+'/padg'; os.makedirs(D,exist_ok=True)
def body(t):
    s=t.index('define hidden { i64, ptr } @_ZN14pump_recovered9admin_cto7execute'); e=t.index('\n}\n',s); return s,e
def ins(t,lab,k):
    s,e=body(t); b=t[s:e]; i=b.index('\n'+lab+':'); j=b.index('\n',i+1)+1
    while re.match(r'\s+%\S+ = phi ',b[j:b.index('\n',j)]): j=b.index('\n',j)+1
    return t[:s]+b[:j]+''.join('  store volatile i64 0, ptr @__padg, align 8\n' for _ in range(k))+b[j:]+t[e:]
def score(m,tag):
    f=D+'/'+tag; open(f+'.ll','w').write(m)
    r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',f+'.ll','-filetype=obj','-o',f+'.o'],capture_output=True,text=True)
    os.remove(f+'.ll')
    if r.returncode: return (0,0)
    c=oracle.elf_fn(f+'.o',oracle.KEEP); os.remove(f+'.o'); return (oracle.metric(c,orig)[0],len(c))
s,e=body(t); labels=re.findall(r'\n([\w.$"\-]+):',t[s:e])
cur=t
for rnd in range(R):
    def f(i): return (score(ins(cur,labels[i],N),'r%d_%d'%(rnd,i)),i)
    with cf.ThreadPoolExecutor(6) as ex: res=list(ex.map(f,range(len(labels))))
    (best,bb),i=max(res)
    cur=ins(cur,labels[i],N)
    open(log,'a').write(json.dumps({'round':rnd,'lab':labels[i],'ratio':round(best,5),'bytes':bb})+'\n')
open(log.replace('.jsonl','.ll'),'w').write(cur)
