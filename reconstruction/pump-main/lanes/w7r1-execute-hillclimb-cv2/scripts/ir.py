#!/usr/bin/env python3
"""IR oracle (diagnostic only): ir.py NAME edit.py|file.ll [base.ll]. llc the slimmed module, diff execute vs original (normalized)."""
import sys,subprocess,re,os,runpy,difflib
L=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w7r1-execute-hillclimb-cv2')
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
sys.path.insert(0,L+'/scripts'); import slim
def norm(txt):
    out=[]
    for l in txt.splitlines():
        m=re.match(r'^\s*[0-9a-f]+:\s+(.*)$',l)
        if not m: continue
        s=m.group(1).strip(); s=re.sub(r'\s+<[^>]*>','',s)
        s=re.sub(r'call -?0x[0-9a-f]+','call X',s); s=re.sub(r'call -?\d+','call X',s)
        s=re.sub(r'lddw (r\d+), -?0x[0-9a-f]+',r'lddw \1, X',s)
        out.append(s)
    return out
ORIG=None
def orig():
    p=L+'/orig-norm.txt'
    if not os.path.exists(p):
        so=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w7r1-execute-blockorder-b/orig-norm.txt')
        import shutil; shutil.copy(so,p)
    return open(p).read().splitlines()
def fn_of(obj):
    sy=subprocess.check_output([SDK+'/llvm-readelf','-sW',obj],text=True)
    for l in sy.splitlines():
        f=l.split()
        if len(f)>=8 and re.search(r'create_v27execute',f[7]): a=int(f[1],16); n=int(f[2]); break
    t=subprocess.check_output([SDK+'/llvm-objdump','-d','--no-show-raw-insn','--start-address=%#x'%a,'--stop-address=%#x'%(a+n),obj],text=True)
    return norm(t)
def getslim(p):
    q=p+'.slim'
    if not os.path.exists(q) or os.path.getmtime(q)<os.path.getmtime(p): open(q,'w').write(slim.slim(open(p).read()))
    return open(q).read()
def run_text(name,t2,extra=()):
    d=L+'/irexp/'+name; os.makedirs(d,exist_ok=True); ll=d+'/m.ll'; open(ll,'w').write(t2)
    r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext',ll,'-filetype=obj','-o',d+'/m.o',*extra],capture_output=True,text=True)
    if r.returncode: return None,r.stderr[-1500:]
    c=fn_of(d+'/m.o'); open(d+'/fn.txt','w').write('\n'.join(c)+'\n'); os.remove(d+'/m.o')
    o=orig(); sm=difflib.SequenceMatcher(None,o,c,autojunk=False)
    diff=list(difflib.unified_diff(o,c,'orig','cand',n=0,lineterm=''))
    nd=sum(1 for l in diff if l[:1] in '+-' and l[:3] not in('+++','---'))
    return (len(c),nd,round(sm.ratio(),5)),diff
if __name__=='__main__':
    name,src=sys.argv[1],sys.argv[2]; base=sys.argv[3] if len(sys.argv)>3 else L+'/ir/b2297/pump_recovered.ll'
    t=getslim(base)
    t2=runpy.run_path(src)['edit'](t) if src.endswith('.py') else getslim(src)
    m,diff=run_text(name,t2)
    print(name,m); print('\n'.join(diff[:int(os.environ.get('N','60'))]) if m else diff)
