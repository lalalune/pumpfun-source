#!/usr/bin/env python3
"""Diagnostic only: IR permutation scanner for v3_buy_costs on the one-function llc oracle.
mut.py <class,...> [--pairs N] : generate single mutations (commute, icmpswap, invert, move, phiord, phiinc, alloca, flag)
run llc on each, print (minus-lines, bytes, sret-signature, tag) sorted."""
import re,sys,subprocess,os,difflib,tempfile,itertools,json
from concurrent.futures import ThreadPoolExecutor
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w7r1-v3buycosts-regsched')
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools')
BASE=os.environ.get('IRBASE',OUT+'/ir/base/one.ll')
T=open(BASE).read()
M=re.search(r'^define[^\n]*12v3_buy_costs[^\n]*\{\n.*?^\}\n',T,re.M|re.S)
SYM=re.search(r'@(\S+?)\(',M.group(0)).group(1)
F0=M.group(0)
def norm(lines):
    return [re.sub(r'([+-]0x[0-9a-f]+)$','J',l.strip()) if re.match(r'(ja|j[a-z]+ )',l.strip()) else l.strip() for l in lines]
ORIG=norm(open(OUT+'/notes/orig-norm.txt').read().splitlines())
os.makedirs(OUT+'/tmp',exist_ok=True)
def llc(f,keep=None):
    tt=T[:M.start()]+f+T[M.end():]
    d=tempfile.mkdtemp(dir=OUT+'/tmp')
    open(d+'/m.ll','w').write(tt)
    r=subprocess.run([SDK+'/llvm/bin/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
    if r.returncode:
        subprocess.run(['rm','-rf',d]); return None,r.stderr[-400:]
    fn=subprocess.run(['sh',OUT+'/bin/fn.sh',d+'/m.o',SYM],capture_output=True,text=True).stdout
    if keep:
        os.makedirs(keep,exist_ok=True); open(keep+'/fn.ll','w').write(f)
    subprocess.run(['rm','-rf',d])
    fn=re.sub(r'call -?0x[0-9a-f]+','call X',fn); fn=re.sub(r'lddw (r\d+), 0x[0-9a-f]+',r'lddw \1, X',fn)
    return norm(fn.splitlines()),None
def score(c):
    diff=list(difflib.unified_diff(ORIG,c,n=0,lineterm=''))
    mi=sum(1 for l in diff if l[:1]=='-' and l[:3]!='---')
    sz=sum(16 if l.startswith('lddw') else 8 for l in c)
    sig='E' if c[2:3]==['stxdw [r10 - 0x190], r1'] else 'e'
    sig+=str(sum(1 for l in c if re.match(r'ldxdw r3, \[r10 - 0x190\]',l)))
    sig+='/'+str(sum(1 for l in c if '[r10 - 0x190]' in l))
    return mi,sz,sig
def run(job):
    tag,f=job
    c,err=llc(f)
    if c is None: return (9999,0,'ERR',tag)
    return score(c)+(tag,)
# ---------- IR helpers ----------
def blocks(f):
    head,body=f.split('\n',1)
    body=body.rsplit('}',1)[0]
    return head,re.split(r'\n\n',body.strip('\n'))
def join(head,bl): return head+'\n'+'\n\n'.join(bl)+'\n}\n'
def ilines(b):
    return b.split('\n')
def is_instr(l): return l.startswith('  ') and not l.lstrip().startswith(';')
DEF=re.compile(r'^\s*(%[\w.$]+|%"[^"]+") =')
def defs(l):
    m=DEF.match(l); return m.group(1) if m else None
def uses(l):
    d=defs(l); s=l.split('=',1)[1] if d else l
    return set(re.findall(r'%[\w.$]+|%"[^"]+"',s))
MEM=re.compile(r'\b(load|store|call|memcpy|tail call)\b')
def gen_commute(f):
    out=[]
    for i,l in enumerate(f.split('\n')):
        m=re.match(r'^(\s*%\S+ = (?:add|mul|or|and|xor)(?: nuw| nsw)* \w+ )(\S+), (\S+)$',l)
        if m:
            out.append(('commute:'+l.strip()[:40],i,m.group(1)+m.group(3)+', '+m.group(2)))
        m=re.match(r'^(.*@llvm\.uadd\.with\.overflow\.i64\()i64 (\S+), i64 (\S+)\)$',l)
        if m:
            out.append(('commute:'+l.strip()[:40],i,m.group(1)+'i64 '+m.group(3)+', i64 '+m.group(2)+')'))
    return out
SW={'ult':'ugt','ugt':'ult','ule':'uge','uge':'ule','slt':'sgt','sgt':'slt','eq':'eq','ne':'ne'}
INV={'ult':'uge','uge':'ult','ugt':'ule','ule':'ugt','eq':'ne','ne':'eq','slt':'sge','sge':'slt','sgt':'sle','sle':'sgt'}
def apply_line(f,i,new):
    L=f.split('\n'); L[i]=new; return '\n'.join(L)
def gen_icmpswap(f):
    out=[]
    for i,l in enumerate(f.split('\n')):
        m=re.match(r'^(\s*%\S+ = icmp )(\w+) (\w+) (\S+), (\S+)$',l)
        if m and not m.group(5).lstrip('-').isdigit() and m.group(5)!='null':
            out.append(('icmpswap:'+l.strip()[:40],i,m.group(1)+SW[m.group(2)]+' '+m.group(3)+' '+m.group(5)+', '+m.group(4)))
    return out
def muts_single(f,classes):
    res=[]
    L=f.split('\n')
    if 'commute' in classes:
        for tag,i,new in gen_commute(f): res.append((tag,apply_line(f,i,new)))
    if 'icmpswap' in classes:
        for tag,i,new in gen_icmpswap(f): res.append((tag,apply_line(f,i,new)))
    if 'invert' in classes:
        for i,l in enumerate(L):
            m=re.match(r'^(\s*)(%\S+) = icmp (\w+) (.*)$',l)
            if not m: continue
            v=m.group(2)
            users=[j for j,x in enumerate(L) if j!=i and re.search(re.escape(v)+r'(?![\w.$])',x)]
            if len(users)!=1: continue
            j=users[0]; bm=re.match(r'^(\s*br i1 )'+re.escape(v)+r', label (\S+), label (\S+)$',L[j])
            if not bm: continue
            L2=L[:]; L2[i]=m.group(1)+v+' = icmp '+INV[m.group(3)]+' '+m.group(4); L2[j]=bm.group(1)+v+', label '+bm.group(3)+', label '+bm.group(2)
            res.append(('invert:'+l.strip()[:40],'\n'.join(L2)))
        for j,l in enumerate(L):
            bm=re.match(r'^(\s*br i1 )(%\S+), label (\S+), label (\S+)$',l)
            if bm:
                v=bm.group(2)
                L2=L[:]; L2.insert(j,'  %%inv%d = xor i1 %s, true'%(j,v)); L2[j+1]=bm.group(1)+'%%inv%d, label %s, label %s'%(j,bm.group(4),bm.group(3))
                res.append(('xorinv:'+l.strip()[:40],'\n'.join(L2)))
    if 'move' in classes or 'moveall' in classes:
        head,bl=blocks(f)
        for bi,b in enumerate(bl):
            BL=b.split('\n')
            idx=[k for k,x in enumerate(BL) if is_instr(x) and not re.search(r'\b(phi|br|ret|unreachable|alloca)\b',x)]
            term=max(k for k,x in enumerate(BL) if is_instr(x))
            firstnonphi=min(k for k,x in enumerate(BL) if is_instr(x) and ' phi ' not in x)
            for k in idx:
                x=BL[k]
                # comment line attached before calls
                for p in range(firstnonphi,term+1):
                    if p in (k,k+1): continue
                    BL2=BL[:]; item=BL2.pop(k); q=p if p<k else p-1
                    BL2.insert(q,item)
                    # legality: defs before uses within block, memory order (no moving across mem ops if self is mem, except load-load)
                    ok=True; seen=set()
                    pos={}
                    for kk,y in enumerate(BL2):
                        if not is_instr(y): continue
                        d=defs(y)
                        if d: pos[d]=kk
                    for kk,y in enumerate(BL2):
                        if not is_instr(y) or ' phi ' in y: continue
                        for u in uses(y):
                            if u in pos and pos[u]>kk: ok=False
                    lo,hi=min(k,q),max(k,q)
                    span=[y for y in BL[lo:hi+1] if is_instr(y) and y is not x]
                    if MEM.search(x) and 'lifetime' not in x:
                        for y in span:
                            if MEM.search(y) and 'lifetime' not in y:
                                if not (re.search(r'= load',x) and re.search(r'= load',y)): ok=False
                    if 'lifetime' in x and 'moveall' not in classes:
                        ok=False
                    if not ok: continue
                    bl2=bl[:]; bl2[bi]='\n'.join(BL2)
                    res.append(('move:%s:%d->%d %s'%(BL[0].split(':')[0][:30],k,q,x.strip()[:40]),join(head,bl2)))
    if 'phiord' in classes:
        head,bl=blocks(f)
        for bi,b in enumerate(bl):
            BL=b.split('\n'); ph=[k for k,x in enumerate(BL) if ' = phi ' in x]
            if len(ph)<2: continue
            for perm in itertools.permutations(ph):
                if list(perm)==ph: continue
                BL2=BL[:]
                for a,bb in zip(ph,perm): BL2[a]=BL[bb]
                bl2=bl[:]; bl2[bi]='\n'.join(BL2); res.append(('phiord:%s:%s'%(BL[0][:20],perm),join(head,bl2)))
    if 'phiinc' in classes:
        for i,l in enumerate(L):
            m=re.match(r'^(\s*%\S+ = phi \S+ )(.*)$',l)
            if not m: continue
            inc=re.findall(r'\[ [^\]]+ \]',m.group(2))
            if len(inc)<2 or len(inc)>4: continue
            for perm in itertools.permutations(inc):
                if list(perm)==inc: continue
                res.append(('phiinc:%s:%s'%(l.strip()[:25],[inc.index(p) for p in perm]),apply_line(f,i,m.group(1)+', '.join(perm))))
    if 'alloca' in classes:
        al=[i for i,l in enumerate(L) if ' = alloca ' in l]
        for a in al:
            for b in al:
                if a<b:
                    L2=L[:]; L2[a],L2[b]=L[b],L[a]; res.append(('alloca:%d<->%d'%(a,b),'\n'.join(L2)))
    return res
if __name__=='__main__':
    classes=sys.argv[1].split(',')
    f=F0
    if os.environ.get('EDIT'):
        import runpy
        for e in os.environ['EDIT'].split(':'): f=runpy.run_path(e)['edit'](f)
    jobs=muts_single(f,classes)
    print(len(jobs),'jobs',file=sys.stderr)
    with ThreadPoolExecutor(int(os.environ.get('J','6'))) as ex: res=list(ex.map(run,jobs))
    base=run(('base',f)); print('BASE',base)
    res.sort()
    json.dump(res,open(OUT+'/scan-%s.json'%('_'.join(classes)),'w'))
    from collections import Counter
    print(Counter((r[0],r[1],r[2]) for r in res).most_common(12))
    for r in res[:int(os.environ.get('TOP','25'))]: print(r)

def gen_extra(f,classes):
    res=[]
    L=f.split('\n')
    if 'ltdel' in classes:
        for i,l in enumerate(L):
            if 'llvm.lifetime.' in l and 'call' in l:
                L2=L[:]; del L2[i]; res.append(('ltdel:%d:%s'%(i,l.strip()[25:70]),'\n'.join(L2)))
    if 'esplit' in classes:
        head,bl=blocks(f)
        names=[re.match(r'("[^"]+"|[\w.$]+):',b).group(1) for b in bl[1:]]
        allb=['start']+names
        k=len(re.findall(r'\nzs\d+:',f))
        for bi,b in enumerate(bl):
            nm=allb[bi]
            BL=b.split('\n'); ti=max(i for i,x in enumerate(BL) if is_instr(x))
            if not BL[ti].strip().startswith('br '): continue
            succ=re.findall(r'label %("[^"]+"|[\w.$]+)',BL[ti])
            for si,s in enumerate(succ):
                if succ.count(s)>1: continue
                nb='zs%d'%(k+1000*bi+si)
                for mark in ('  call void @llvm.lifetime.start.p0(i64 0, ptr nonnull %_11.i.i29)',''):
                    BL2=BL[:]; BL2[ti]=re.sub(r'label %'+re.escape(s)+r'(?=[,\s]|$)','label %'+nb,BL2[ti],count=1)
                    bl2=bl[:]; bl2[bi]='\n'.join(BL2)
                    tj=allb.index(s)
                    bl2[tj]=re.sub(r'(\[ [^\]]+?, %)'+re.escape(nm)+r'( \])',lambda mm: mm.group(1)+nb+mm.group(2),bl2[tj])
                    newb=nb+':\n'+(mark+'\n' if mark else '')+'  br label %'+s
                    for pos in ('after','end'):
                        bl3=bl2[:]
                        if pos=='after': bl3.insert(bi+1,newb)
                        else: bl3.append(newb)
                        res.append(('esplit:%s->%s:%s:%s'%(nm[:20],s[:20],'m' if mark else 'e',pos),join(head,bl3)))
    if 'bmove' in classes:
        head,bl=blocks(f)
        for i in range(1,len(bl)):
            for j in range(1,len(bl)):
                if i==j: continue
                bl2=bl[:]; x=bl2.pop(i); bl2.insert(j,x); res.append(('bmove:%d->%d'%(i,j),join(head,bl2)))
    return res
def allmuts(f,classes):
    return muts_single(f,classes)+gen_extra(f,classes)
