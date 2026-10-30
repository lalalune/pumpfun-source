#!/usr/bin/env python3
"""pad.py scan <m.ll> <out.jsonl> N [-j J] | pad.py apply <m.ll> lab:N,lab:N...
Oracle only: insert N `ja +0` inline-asm pads (8 B each, no registers) at the top of an execute block (after phis), llc, score."""
import sys,os,re,subprocess,json,concurrent.futures as cf
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import oracle, difflib
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a15-cto-skelunion')
def rng(t):
    s=t.index('admin_cto7execute'); s=t.rindex('define',0,s); e=t.index('\n}\n',s); return s,e
def labels(t):
    s,e=rng(t); return re.findall(r'\n([\w.$"\-]+):',t[s:e])
def ins(t,lab,k):
    s,e=rng(t); b=t[s:e]; i=b.index('\n'+lab+':'); j=b.index('\n',i+1)+1
    while re.match(r'\s+%\S+ = (phi|landingpad) ',b[j:b.index('\n',j)]): j=b.index('\n',j)+1
    return t[:s]+b[:j]+''.join('  call void asm sideeffect "ja +0", ""()\n' for _ in range(k))+b[j:]+t[e:]
orig=oracle.orig_window()
def score(m,tag):
    import tempfile
    with tempfile.TemporaryDirectory(dir=O) as d:
        open(d+'/m.ll','w').write(m)
        r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
        if r.returncode: return {'err':r.stderr[-200:]}
        c=oracle.elf_fn(d+'/m.o',oracle.KEEP); rr,sd=oracle.metric(c,orig)
        return {'ratio':round(rr,5),'bytes':len(c),'slots':sd}
if __name__=='__main__':
    cmd=sys.argv[1]; t=open(sys.argv[2]).read()
    if cmd=='scan':
        out,N=sys.argv[3],int(sys.argv[4]); J=int(sys.argv[sys.argv.index('-j')+1]) if '-j' in sys.argv else 2
        done=set()
        if os.path.exists(out): done={json.loads(l)['lab'] for l in open(out)}
        f=open(out,'a')
        def go(l):
            r={'lab':l,'N':N,**score(ins(t,l,N),l)}; f.write(json.dumps(r)+'\n'); f.flush()
        with cf.ThreadPoolExecutor(J) as ex: list(ex.map(go,[l for l in labels(t) if l not in done]))
    else:
        for x in sys.argv[3].split(','):
            l,k=x.rsplit(':',1); t=ins(t,l,int(k))
        print(json.dumps(score(t,'apply')))
