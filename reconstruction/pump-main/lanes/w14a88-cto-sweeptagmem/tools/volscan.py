#!/usr/bin/env python3
"""volscan.py <base mn.ll> <ptr> <out.jsonl> [jobs]: insert a volatile i8 load of <ptr> at the top of every execute block (after phis); llc+score."""
import sys,os,re,subprocess,json,difflib,tempfile,concurrent.futures as cf
D=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+'/'
A=sys.argv[1:]; sys.argv=['x','n']
exec(open(D+'tools/rx.py').read().split('OUT=os.environ')[0])
sys.path.insert(0,D+'tools'); from mv import span,fnspan
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
base,ptr,out=A[0],A[1],A[2]; J=int(A[3]) if len(A)>3 else 5
POS=os.environ.get('POS','top')
t=open(base).read(); a,b=fnspan(t)
labels=re.findall(r'\n([\w.$"-]+):',t[a:b])
ORIG=mask(orig_window())
def ins(t,L):
    i,j=span(t,L); blk=t[i:j].split('\n')
    k=1
    while k<len(blk) and re.match(r'\s+%[\w.$"-]+ = phi ',blk[k]): k+=1
    if POS=='end': k=len(blk)-1
    blk.insert(k,'  %%volx = load volatile i8, ptr %s, align 1'%ptr)
    return t[:i]+'\n'.join(blk)+t[j:]
def run(L):
    v=ins(t,L)
    fd,p=tempfile.mkstemp(suffix='.ll',dir=D+'px'); os.write(fd,v.encode()); os.close(fd)
    o=p[:-3]+'.o'
    r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',p,'-filetype=obj','-o',o],capture_output=True,text=True)
    os.remove(p)
    if r.returncode: return {'at':L,'error':r.stderr[-200:]}
    c=mask(elf_fn(o,KEEP)); os.remove(o)
    sm=difflib.SequenceMatcher(None,ORIG,c,autojunk=False); M=sum(x.size for x in sm.get_matching_blocks())
    return {'at':L,'M':M,'bytes':sum(len(x) for x in c),'ratio':round(sm.ratio(),5)}
with open(out,'w') as f, cf.ThreadPoolExecutor(J) as ex:
    for r in ex.map(run,labels):
        f.write(json.dumps(r)+'\n'); f.flush()
