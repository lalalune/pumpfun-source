#!/usr/bin/env python3
"""ir.py <name> <ll|edit.py> [base.ll]: llc IR (optionally edited), diff create_v2::execute vs original window (normalized text)."""
import sys,subprocess,re,os,runpy,difflib
L=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w4-createv2')
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
ORIGSO='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/restore/reconstruction/base/original.so'
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
def orig():
    p=L+'/orig-norm.txt'
    if not os.path.exists(p):
        t=subprocess.check_output([SDK+'/llvm-objdump','-d','--no-show-raw-insn','--start-address=0x1e7c0','--stop-address=%#x'%(0x1e7c0+15576),ORIGSO],text=True)
        open(p,'w').write('\n'.join(norm(t))+'\n')
    return open(p).read().splitlines()
def fn_of(obj):
    sy=subprocess.check_output([SDK+'/llvm-readelf','-sW',obj],text=True)
    for l in sy.splitlines():
        f=l.split()
        if len(f)>=8 and re.search(r'create_v27execute',f[7]):
            a=int(f[1],16); n=int(f[2]); break
    t=subprocess.check_output([SDK+'/llvm-objdump','-d','--no-show-raw-insn','--start-address=%#x'%a,'--stop-address=%#x'%(a+n),obj],text=True)
    return norm(t)
def getslim(p):
    import hashlib,sys; sys.path.insert(0,L+'/scripts'); import slim
    q=p+'.slim'
    if not os.path.exists(q) or os.path.getmtime(q)<os.path.getmtime(p): open(q,'w').write(slim.slim(open(p).read()))
    return open(q).read()
def frame(name,ll=None):
    d=L+'/irexp/'+name; ll=ll or d+'/m.ll'
    subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-stop-after=prologepilog',ll,'-o',d+'/m.mir'],check=True)
    t=open(d+'/m.mir').read(); h=t[:t.find('\nbody:')]
    st=re.sub(r'\s+',' ',h.split('\nstack:')[1]); rows=[]
    for m in re.finditer(r"id: (\d+), name: ([^,]*), type: (\S+), offset: (-?\d+), size: (\d+)",st):
        i_,n,ty,o,s_=m.groups(); rows.append((int(i_),-int(o),int(s_),n,ty))
    return rows
def run(name,src,base=None,extra=()):
    d=L+'/irexp/'+name; os.makedirs(d,exist_ok=True)
    if src.endswith('.py'):
        t=getslim(base or (L+'/out/ir-t01/pump_recovered.ll')); t2=runpy.run_path(src)['edit'](t); assert t2!=t,'edit changed nothing'
        open(d+'/m.ll','w').write(t2); ll=d+'/m.ll'
    else:
        open(d+'/m.ll','w').write(getslim(src)); ll=d+'/m.ll'
    r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext',ll,'-filetype=obj','-o',d+'/m.o',*extra],capture_output=True,text=True)
    if r.returncode: print(r.stderr[-3000:]); sys.exit(1)
    c=fn_of(d+'/m.o'); open(d+'/fn.txt','w').write('\n'.join(c)+'\n')
    o=orig()
    sm=difflib.SequenceMatcher(None,o,c,autojunk=False)
    diff=list(difflib.unified_diff(o,c,'orig','cand',n=1,lineterm=''))
    nd=sum(1 for l in diff if l[:1] in '+-' and l[:3] not in('+++','---'))
    print(f'{name}: insns orig={len(o)} cand={len(c)} difflines={nd} ratio={sm.ratio():.5f}')
    return diff
if __name__=='__main__':
    diff=run(sys.argv[1],sys.argv[2],sys.argv[3] if len(sys.argv)>3 else None)
    print('\n'.join(diff[:int(os.environ.get('N','40'))]))
