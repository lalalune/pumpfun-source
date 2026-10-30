#!/usr/bin/env python3
"""slotpin.py: MIR-level stack-slot pin oracle for admin_cto::execute.
  slotpin.py prep <ex.bc> <dir>       : llc -stop-before=prologepilog (pre.mir) and -stop-after (post.mir); dir/objs.json
  slotpin.py run  <dir> <map.json|-> <out.txt> : rewrite pre.mir stack objects as fixed objects at offsets
        (identity = own PEI offsets; map.json {"<id>": <neg offset>} overrides), resume llc -start-before=prologepilog,
        dump execute as fn text (outgoing-arg [r10+X] -> [r10-(0x1000-X)] fix), print oratio.
"""
import sys,os,re,json,subprocess
B=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin'); T=os.path.dirname(os.path.abspath(__file__))
O=os.path.dirname(T); F=['-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections']
SYM='admin_cto7execute'
def fnrange(L):
    st=next(i for i,l in enumerate(L) if l.startswith('name:') and SYM in l)
    en=next((i for i in range(st+1,len(L)) if L[i].startswith('---') or L[i].startswith('...')),len(L))
    return st,en
def objs(path):
    t=open(path).read().split('\n'); st,en=fnrange(t); s='\n'.join(t[st:en])
    j=s.find('\nstack:'); k=min(x for x in (s.find('\ncallSites:',j),s.find('\nentry_values:',j),s.find('\nmachineFunctionInfo:',j)) if x>0)
    R={}
    for e in re.findall(r'\{ id: \d+,[^}]*\}',s[j:k]):
        e=' '.join(e.split())
        m=re.search(r"id: (\d+), name: ([^,]*), type: (\S+), offset: (-?\d+), size: (\d+), alignment: (\d+)",e)
        R[int(m.group(1))]=dict(name=m.group(2).strip("'"),type=m.group(3).rstrip(','),off=int(m.group(4)),size=int(m.group(5)),align=int(m.group(6)))
    return R
def stage(d):
    return open(d+'/stage').read().strip() if os.path.exists(d+'/stage') else 'prologepilog'
def prep(bc,d,st='prologepilog'):
    os.makedirs(d,exist_ok=True); open(d+'/stage','w').write(st)
    subprocess.run([B+'/llc']+F+[bc,f'-stop-before={st}','-o',d+'/pre.mir'],check=True)
    subprocess.run([B+'/llc']+F+[d+'/pre.mir',f'-start-before={st}','-stop-after=prologepilog','-o',d+'/post.mir'],check=True)
    subprocess.run([B+'/llc']+F+[d+'/pre.mir',f'-start-before={st}','-filetype=obj','-o',d+'/direct.o'],check=True)
    open(d+'/direct.txt','w').write(fntext(d+'/direct.o'))
    if st!='prologepilog':
        subprocess.run([B+'/llc']+F+[bc,'-filetype=obj','-o',d+'/real.o'],check=True); open(d+'/real.txt','w').write(fntext(d+'/real.o'))
    po=objs(d+'/post.mir'); pr=objs(d+'/pre.mir')
    if st!='prologepilog':  # parsed MIR renumbers frame indices sequentially: map by position
        assert len(po)==len(pr); po={a:po[b] for a,b in zip(sorted(pr),sorted(po))}
    json.dump(po,open(d+'/objs.json','w'))
def fntext(o):
    s=subprocess.run(['python3',T+'/objfn.py',o,SYM],capture_output=True,text=True).stdout
    return re.sub(r'\[r10 \+ 0x([0-9a-f]+)\]',lambda m:'[r10 - %#x]'%(0x1000-int(m.group(1),16)),s)
def rewrite(d,mp,out_mir):
    ob={int(k):v for k,v in json.load(open(d+'/objs.json')).items()}
    L=open(d+'/pre.mir').read().split('\n'); st,en=fnrange(L)
    i=next(i for i in range(st,en) if L[i].startswith('fixedStack:'))
    j=next(i for i in range(i,en) if L[i].startswith('stack:'))
    k=next(i for i in range(j,en) if re.match(r'^(callSites|entry_values|machineFunctionInfo|debugValueSubstitutions|constants):',L[i]))
    fx=L[i+1:j] if L[i].strip()!='fixedStack:      []' else []
    nfx=len(re.findall(r'\{ id: \d+',' '.join(fx)))
    ren={}; new=[]
    for n,(oid,o) in enumerate(sorted(ob.items())):
        fid=nfx+n; ren[oid]=fid; off=mp.get(str(oid),mp.get(oid,o['off']))
        new.append(f"  - {{ id: {fid}, type: default, offset: {off}, size: {o['size']}, alignment: {o['align']}, stack-id: default, isImmutable: false, isAliased: false, callee-saved-register: '', callee-saved-restored: true, debug-info-variable: '', debug-info-expression: '', debug-info-location: '' }}")
    head=L[:i]+['fixedStack:']+fx+new+['stack:           []']
    body='\n'.join(L[k:en])
    body=re.sub(r'%stack\.(\d+)(\.[A-Za-z0-9_.]+)?',lambda m:f'%fixed-stack.{ren[int(m.group(1))]}',body)
    open(out_mir,'w').write('\n'.join(head)+'\n'+body+'\n'+'\n'.join(L[en:]))
def run(d,mpf,out):
    mp=json.load(open(mpf)) if mpf!='-' else {}
    mir=out+'.mir'; rewrite(d,mp,mir)
    r=subprocess.run([B+'/llc']+F+[mir,f'-start-before={stage(d)}','-filetype=obj','-o',out+'.o'],capture_output=True,text=True)
    if r.returncode: sys.stderr.write(r.stderr[-3000:]); sys.exit(1)
    open(out,'w').write(fntext(out+'.o')); os.remove(mir); os.remove(out+'.o')
    print(subprocess.run(['python3',T+'/oratio.py',O+'/orig_fn.txt',out],capture_output=True,text=True).stdout.strip())
if __name__=='__main__':
    c=sys.argv[1]
    if c=='prep': prep(sys.argv[2],sys.argv[3],*(sys.argv[4:5]))
    elif c=='run': run(*sys.argv[2:5])

# ---- mapping: align cand vs ref (frame-masked tokens), vote object -> ref base offset ----
def _rd(f):
    A=[];Tk=[]
    for l in open(f):
        p=l.split(None,1)
        if len(p)<2: continue
        s=p[1].strip(); A.append(s)
        s=re.sub(r'^call .*','call',s); s=re.sub(r'lddw (r\d+), .*',r'lddw \1',s)
        s=re.sub(r'r10 - 0x[0-9a-f]+','r10-X',s); s=re.sub(r'add64 (r\d), -0x[0-9a-f]+',r'add64 \1, -X',s); Tk.append(s)
    return A,Tk
def _offs(a):
    """frame offsets (as negative ints) referenced by insn list a: r10 mem operands and mov rX,r10; add64 rX,-K pairs"""
    R=[None]*len(a); src={}
    for i,s in enumerate(a):
        m=re.search(r'\[r10 - (0x[0-9a-f]+)\]',s)
        if m: R[i]=-int(m.group(1),16)
        m2=re.match(r'mov64 (r\d), r10$',s)
        m3=re.match(r'add64 (r\d), -(0x[0-9a-f]+)$',s)
        if m3 and src.get(m3.group(1))==i-1: R[i]=-int(m3.group(2),16)
        if m2: src[m2.group(1)]=i
        else:
            m4=re.match(r'\S+ (r\d),',s)
            if m4 and not m3: src.pop(m4.group(1),None)
    return R
def mkmap(d,ref,kinds='spill',out=None):
    import difflib,collections
    ob={int(k):v for k,v in json.load(open(d+'/objs.json')).items()}
    a,ta=_rd(d+'/direct.txt'); b,tb=_rd(ref); oa=_offs(a); obb=_offs(b)
    V=collections.defaultdict(collections.Counter)
    def find(x):
        for i,o in ob.items():
            if o['off']<=x<o['off']+o['size']: return i
    for t,i1,i2,j1,j2 in difflib.SequenceMatcher(None,ta,tb,autojunk=False).get_opcodes():
        if t!='equal': continue
        for k in range(i2-i1):
            x,y=oa[i1+k],obb[j1+k]
            if x is None or y is None: continue
            i=find(x)
            if i is None: continue
            if kinds=='spill' and ob[i]['type']!='spill-slot': continue
            V[i][y-(x-ob[i]['off'])]+=1
    # greedy one-to-one on (vote) ; targets must not overlap among chosen
    cands=sorted(((n,i,t) for i,c in V.items() for t,n in c.items()),reverse=True)
    mp={}; used=[]
    for n,i,t in cands:
        if i in mp: continue
        sz=ob[i]['size']
        if not os.environ.get('MERGE') and any(t<u+us and u<t+sz for u,us in used): continue
        mp[i]=t; used.append((t,sz))
    if out: json.dump({str(k):v for k,v in mp.items()},open(out,'w'))
    moved=sum(1 for i,t in mp.items() if t!=ob[i]['off'])
    return mp,moved,len(V)
if __name__=='__main__' and sys.argv[1]=='map':
    d,ref,kinds,out=sys.argv[2:6]; mp,mv,nv=mkmap(d,ref,kinds,out); print(f'mapped {len(mp)} of {nv} voted objs, moved {mv}')

def colmap(d,out):
    """pre-colouring stage: map each object to its offset in the real (coloured) build, by line-aligned identical code"""
    import collections
    ob={int(k):v for k,v in json.load(open(d+'/objs.json')).items()}
    a=[l.split(None,1)[1] for l in open(d+'/direct.txt')]; b=[l.split(None,1)[1] for l in open(d+'/real.txt')]
    assert len(a)==len(b)
    oa=_offs(a); obb=_offs(b); V=collections.defaultdict(collections.Counter)
    for x,y in zip(oa,obb):
        if x is None: continue
        for i,o in ob.items():
            if o['off']<=x<o['off']+o['size']: V[i][y-(x-o['off'])]+=1; break
    mp={str(i):c.most_common(1)[0][0] for i,c in V.items()}
    bad=sum(sum(c.values())-c.most_common(1)[0][1] for c in V.values())
    json.dump(mp,open(out,'w')); return mp,bad
if __name__=='__main__' and sys.argv[1]=='colmap':
    mp,bad=colmap(sys.argv[2],sys.argv[3]); print('objs',len(mp),'inconsistent accesses',bad)

DL=os.path.expanduser('~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin/llc')
def liveness(bc,d):
    f=d+'/ss_live.json'
    if os.path.exists(f): return {int(k):v for k,v in json.load(open(f)).items()}
    r=subprocess.run([DL]+F+[bc,'-filetype=obj','-o',d+'/_dbg.o','-debug-only=stack-slot-coloring'],capture_output=True,text=True)
    t=r.stderr; i=t.find('Function: _ZN14pump_recovered9admin_cto7execute'); t=t[i:t.find('Color spill slot intervals',i)]
    R={}
    for m in re.finditer(r'SS#(\d+) (.*?) 0@',t):
        R[int(m.group(1))]=[(int(a),int(b)) for a,b in re.findall(r'\[(\d+)[rBed],(\d+)[rBed]:',m.group(2))]
    os.remove(d+'/_dbg.o'); json.dump(R,open(f,'w')); return R
def ovl(A,B):
    i=j=0
    while i<len(A) and j<len(B):
        if A[i][0]<B[j][1] and B[j][0]<A[i][1]: return True
        if A[i][1]<=B[j][1]: i+=1
        else: j+=1
    return False
def mkmap2(d,ref,bc,out=None,kinds='all',alignsrc=None,raw=False):
    """interval-level (pre-colouring) map with valid colouring: intervals may share a target slot only if their live ranges are disjoint"""
    import difflib,collections
    LV=liveness(bc,d)
    ob={int(k):v for k,v in json.load(open(d+'/objs.json')).items()}
    a,ta=_rd(d+'/direct.txt'); b,tb=_rd(ref); oa=_offs(a); obb=_offs(b)
    if alignsrc:
        a2,ta2=_rd(alignsrc); assert len(a2)==len(a)
        if raw: ta2=[re.sub(r'^call .*','call',x) for x in a2]; tb=[re.sub(r'^call .*','call',x) for x in b]; ta2=[re.sub(r'lddw (r\d+), .*',r'lddw \1',x) for x in ta2]; tb=[re.sub(r'lddw (r\d+), .*',r'lddw \1',x) for x in tb]
        ta=ta2
    V=collections.defaultdict(collections.Counter)
    ops=difflib.SequenceMatcher(None,ta,tb,autojunk=False).get_opcodes()
    for t,i1,i2,j1,j2 in ops:
        if t not in ('equal','replace') or (t=='replace' and (i2-i1)!=(j2-j1)): continue
        for k in range(i2-i1):
            if t=='replace' and re.sub(r'r10 - 0x[0-9a-f]+','X',a[i1+k])!=re.sub(r'r10 - 0x[0-9a-f]+','X',b[j1+k]): continue
            x,y=oa[i1+k],obb[j1+k]
            if x is None or y is None: continue
            for i,o in ob.items():
                if o['off']<=x<o['off']+o['size']:
                    if kinds=='all' or o['type']=='spill-slot': V[i][y-(x-o['off'])]+=1
                    break
    cands=sorted(((n,i,t) for i,c in V.items() for t,n in c.items()),reverse=True)
    mp={}; used=[]  # (t,size,id)
    for n,i,t in cands:
        if i in mp: continue
        sz=ob[i]['size']; ok=True
        for u,us,j in used:
            if t<u+us and u<t+sz:
                if ob[i]['type']=='spill-slot' and ob[j]['type']=='spill-slot' and u==t and i in LV and j in LV and not ovl(LV[i],LV[j]): continue
                ok=False; break
        if ok: mp[i]=t; used.append((t,sz,i))
    if out: json.dump({str(k):v for k,v in mp.items()},open(out,'w'))
    return mp
if __name__=='__main__' and sys.argv[1]=='map2':
    mp=mkmap2(*sys.argv[2:6]); print('mapped',len(mp))
