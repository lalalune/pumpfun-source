#!/usr/bin/env python3
"""mvscan.py <base mn.ll> <block> <out.jsonl> [jobs]: move <block> after every other block of execute, llc+score each."""
import sys,os,re,subprocess,json,difflib,tempfile,concurrent.futures as cf
D=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+'/'
A=sys.argv[1:]; sys.argv=['x','n']
exec(open(D+'tools/rx.py').read().split('OUT=os.environ')[0])
sys.path.insert(0,D+'tools'); from mv import span,fnspan,mvafter
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
base,blk,out=A[0],A[1],A[2]; J=int(A[3]) if len(A)>3 else 4
t=open(base).read(); a,b=fnspan(t)
labels=re.findall(r'\n([\w.$"-]+):',t[a:b])
ORIG=mask(orig_window())
def run(L):
    try: v=mvafter(t,blk,L)
    except Exception as e: return {'after':L,'error':str(e)[:100]}
    fd,p=tempfile.mkstemp(suffix='.ll',dir=D+'px'); os.write(fd,v.encode()); os.close(fd)
    o=p[:-3]+'.o'
    r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',p,'-filetype=obj','-o',o],capture_output=True,text=True)
    os.remove(p)
    if r.returncode: return {'after':L,'error':r.stderr[-200:]}
    c=mask(elf_fn(o,KEEP)); os.remove(o)
    sm=difflib.SequenceMatcher(None,ORIG,c,autojunk=False); M=sum(x.size for x in sm.get_matching_blocks())
    return {'after':L,'M':M,'bytes':sum(len(x) for x in c),'ratio':round(sm.ratio(),5)}
with open(out,'w') as f, cf.ThreadPoolExecutor(J) as ex:
    for r in ex.map(run,[L for L in labels if L!=blk]):
        f.write(json.dumps(r)+'\n'); f.flush()
