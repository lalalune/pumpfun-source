#!/usr/bin/env python3
"""asgen.py <slim.ll> <edits.jsonl> [kinds]: enumerate llvm.assume cells on the pre-opt bodies of admin_cto
validate/execute/wallet/sweep (experiment only). kinds (comma list, default all):
  eq  : assume(y==x) for a load y and a dominating earlier load x of the same type and symbolic address
        (nearest and earliest dominating x)
  rg  : assume(v<=1) / assume(v<=2) on i8 loads (no !range) and assume(v<=1) on Option<bool>-range loads
Edit format = w17a06 screen.py (rep: {line: [new lines]}, extra: [decls])."""
import sys,re,json,collections
FN={'validate':r'admin_cto8validate17h','execute':r'admin_cto7execute17h','wallet':r'admin_cto7execute6wallet17h','sweep':r'admin_cto7execute5sweep17h'}
VAL=r'(%[\w.$-]+|%"[^"]+")'
def ranges(L):
    R={}
    for i,l in enumerate(L):
        if l.startswith('define '):
            for k,p in FN.items():
                if re.search(p,l.split('(')[0]):
                    j=i
                    while L[j]!='}': j+=1
                    R[k]=(i,j)
    return R
def parse_fn(L,a,b):
    blocks=[]; cur=None; lineblk={}
    for i in range(a+1,b):
        l=L[i]
        m=re.match(r'^("?[\w.$-]+"?):',l)
        if m: cur=m.group(1); blocks.append([cur,i,[]]); continue
        if cur is None and l.strip(): cur='start'; blocks.append([cur,i,[]])
        if cur: lineblk[i]=cur
    succ=collections.defaultdict(list)
    for name,st,_ in blocks:
        pass
    # successors: scan terminator lines
    bl={b_[0]:b_ for b_ in blocks}
    order=[b_[0] for b_ in blocks]
    for idx,(name,st,_) in enumerate(blocks):
        en=blocks[idx+1][1] if idx+1<len(blocks) else b
        for i in range(st,en):
            l=L[i].strip()
            if l.startswith('br ') or l.startswith('switch ') or l.startswith(']') or re.match(r'i\d+ -?\d+, label',l):
                for t in re.findall(r'label %("?[\w.$-]+"?)',l): succ[name].append(t)
            if l.startswith('switch'):
                j=i+1
                while not L[j].strip().startswith(']'):
                    for t in re.findall(r'label %("?[\w.$-]+"?)',L[j]): succ[name].append(t)
                    j+=1
    return order,succ,lineblk
def doms(order,succ):
    pred=collections.defaultdict(list)
    for x in order:
        for y in succ[x]: pred[y].append(x)
    # reachable RPO
    seen=set(); post=[]
    def dfs(x):
        st=[(x,iter(succ[x]))]; seen.add(x)
        while st:
            n,it=st[-1]
            nx=next(it,None)
            if nx is None: post.append(n); st.pop()
            elif nx not in seen: seen.add(nx); st.append((nx,iter(succ[nx])))
    dfs(order[0]); rpo=post[::-1]; idx={x:i for i,x in enumerate(rpo)}
    idom={rpo[0]:rpo[0]}
    def inter(a,b):
        while a!=b:
            while idx[a]>idx[b]: a=idom[a]
            while idx[b]>idx[a]: b=idom[b]
        return a
    ch=True
    while ch:
        ch=False
        for x in rpo[1:]:
            ps=[p for p in pred[x] if p in idom]
            if not ps: continue
            n=ps[0]
            for p in ps[1:]: n=inter(p,n)
            if idom.get(x)!=n: idom[x]=n; ch=True
    def dominates(a,b):
        if b not in idom or a not in idom: return False
        while True:
            if a==b: return True
            if b==idom[b]: return False
            b=idom[b]
    return dominates,idx
def main(src,dst,kinds='eq,rg'):
    kinds=set(kinds.split(','))
    L=open(src).read().split('\n'); R=ranges(L); E=[]; seq=0
    for fn,(a,b) in R.items():
        order,succ,lineblk=parse_fn(L,a,b)
        dominates,rpoi=doms(order,succ)
        defs={}
        for i in range(a+1,b):
            m=re.match(r'^\s+'+VAL+r' = (.*)$',L[i])
            if m: defs[m.group(1)]=(i,m.group(2))
        memo={}
        def addr(v,d=0):
            if v in memo: return memo[v]
            r=(v,0)
            if d<16 and v in defs:
                i,rhs=defs[v]
                m=re.match(r'getelementptr inbounds i8, ptr '+VAL+r', i64 (-?\d+)$',rhs)
                if m:
                    bb,o=addr(m.group(1),d+1); r=(bb,o+int(m.group(2)))
                else:
                    m=re.match(r'load (ptr), ptr '+VAL+r'(,.*)?$',rhs)
                    if m:
                        bb,o=addr(m.group(2),d+1); r=('*(%s+%d)'%(bb,o),0)
            memo[v]=r; return r
        loads=[]
        for v,(i,rhs) in sorted(defs.items(),key=lambda kv:kv[1][0]):
            m=re.match(r'load (volatile )?(ptr|i\d+), ptr '+VAL+r'(,.*)?$',rhs)
            if not m or m.group(1): continue
            loads.append((i,v,m.group(2),addr(m.group(3)),m.group(4) or ''))
        G=collections.defaultdict(list)
        for x in loads: G[(x[2],x[3])].append(x)
        def avail(x,y):
            bx,by=lineblk[x[0]],lineblk[y[0]]
            if bx==by: return x[0]<y[0]
            return dominates(bx,by)
        if 'eq' in kinds:
            for key,xs in G.items():
                if len(xs)<2: continue
                for j,y in enumerate(xs):
                    ds=[x for x in xs if x is not y and avail(x,y)]
                    if not ds: continue
                    picks=[]
                    near=max(ds,key=lambda x:(rpoi.get(lineblk[x[0]],0),x[0])); picks.append(('n',near))
                    far=min(ds,key=lambda x:(rpoi.get(lineblk[x[0]],0),x[0]))
                    if far is not near: picks.append(('f',far))
                    for tag,x in picks:
                        seq+=1; c='%%asq%d'%seq; t=y[2]
                        rep={y[0]:[L[y[0]],'  %s = icmp eq %s %s, %s'%(c,t,y[1],x[1]),'  call void @llvm.assume(i1 noundef zeroext %s)'%c]}
                        E.append({'id':'eq%s:%s:%d:%d'%(tag,fn,y[0],x[0]),'kind':'eq','cls':t,'fn':fn,'rep':rep,'extra':[],
                                  'src':L[y[0]].strip()[:100],'x':L[x[0]].strip()[:100],'addr':'%s+%d'%key[1]})
        if 'rg' in kinds:
            for (i,v,t,ad,md) in loads:
                if t!='i8': continue
                rng=re.search(r'!range !(\d+)',md)
                bounds=[]
                if not rng: bounds=[1,2]
                else:
                    # find metadata
                    mdl=[l for l in L[-400:] if l.startswith('!%s = '%rng.group(1))]
                    if mdl and 'i8 0, i8 3' in mdl[0]: bounds=[1]
                for k in bounds:
                    seq+=1; c='%%asr%d'%seq
                    rep={i:[L[i],'  %s = icmp ule i8 %s, %d'%(c,v,k),'  call void @llvm.assume(i1 noundef zeroext %s)'%c]}
                    E.append({'id':'rg%d:%s:%d'%(k,fn,i),'kind':'rg','cls':'le%d'%k,'fn':fn,'rep':rep,'extra':[],'src':L[i].strip()[:100],'addr':'%s+%d'%ad})

        if 'cc' in kinds:
            preds=collections.defaultdict(list)
            for x_ in order:
                for y_ in succ[x_]: preds[y_].append(x_)
            blkfirst={}
            for i in range(a+1,b):
                if i in lineblk and lineblk[i] not in blkfirst: blkfirst[lineblk[i]]=i
            def cond_fact(c):
                # returns (loadline, value-name, type, addr, const_if_true, const_if_false) or None
                if c not in defs: return None
                i,rhs=defs[c]
                m=re.match(r'trunc i8 '+VAL+r' to i1$',rhs)
                if m and m.group(1) in defs:
                    j,r2=defs[m.group(1)]
                    mm=re.match(r'load i8, ptr '+VAL,r2)
                    if mm: return ('i8',addr(mm.group(1)),1,0)
                m=re.match(r'xor i1 '+VAL+r', true$',rhs)
                if m:
                    f=cond_fact(m.group(1))
                    if f: return (f[0],f[1],f[3],f[2])
                m=re.match(r'icmp (eq|ne) (i\d+|ptr) '+VAL+r', (-?\d+|null)$',rhs)
                if m and m.group(3) in defs:
                    j,r2=defs[m.group(3)]
                    mm=re.match(r'load (i\d+|ptr), ptr '+VAL,r2)
                    if mm:
                        C=m.group(4)
                        return (m.group(2),addr(mm.group(2)),C,None) if m.group(1)=='eq' else (m.group(2),addr(mm.group(2)),None,C)
                return None
            facts=[]
            for i in range(a+1,b):
                m=re.match(r'^\s+br i1 '+VAL+r', label %("?[\w.$-]+"?), label %("?[\w.$-]+"?)',L[i])
                if not m: continue
                f=cond_fact(m.group(1))
                if not f: continue
                B=lineblk[i]
                for S,C in ((m.group(2),f[2]),(m.group(3),f[3])):
                    if C is None or len(preds[S])!=1: continue
                    facts.append((S,f[0],f[1],C,i))
            print(fn,'facts',len(facts),file=sys.stderr)
            seen=set()
            for (S,t,ad,C,bi) in facts:
                for (i,v,lt,lad,md) in loads:
                    if lt!=t or lad!=ad: continue
                    if not dominates(S,lineblk[i]): continue
                    key=(i,C)
                    if key in seen: continue
                    seen.add(key)
                    seq+=1; c='%%asc%d'%seq
                    rep={i:[L[i],'  %s = icmp eq %s %s, %s'%(c,t,v,C),'  call void @llvm.assume(i1 noundef zeroext %s)'%c]}
                    E.append({'id':'cc:%s:%d:%s'%(fn,i,C),'kind':'cc','cls':t,'fn':fn,'rep':rep,'extra':[],'src':L[i].strip()[:100],'x':L[bi].strip()[:80],'addr':'%s+%d'%ad})

        if 'st' in kinds:
            # store->load facts: load y after a dominating store of value w to the same (non-alloca) symbolic address
            stores=[]
            for i in range(a+1,b):
                m=re.match(r'^\s+store (i\d+|ptr) ([^,]+), ptr '+VAL+r'(,.*)?$',L[i])
                if not m: continue
                ad=addr(m.group(3))
                base=ad[0]
                if base in defs and defs[base][1].startswith('alloca'): continue
                stores.append((i,m.group(1),m.group(2).strip(),ad))
            print(fn,'stores',len(stores),file=sys.stderr)
            for (i,v,lt,lad,md) in loads:
                ds=[s_ for s_ in stores if s_[1]==lt and s_[3]==lad and (lineblk[s_[0]]==lineblk[i] and s_[0]<i or lineblk[s_[0]]!=lineblk[i] and dominates(lineblk[s_[0]],lineblk[i]))]
                if not ds: continue
                s_=max(ds,key=lambda z:(rpoi.get(lineblk[z[0]],0),z[0]))
                w=s_[2]
                if w.startswith('%') and w not in defs and not re.match(r'^%\d+$',w) and False: continue
                seq+=1; c='%%ast%d'%seq
                rep={i:[L[i],'  %s = icmp eq %s %s, %s'%(c,lt,v,w),'  call void @llvm.assume(i1 noundef zeroext %s)'%c]}
                E.append({'id':'st:%s:%d:%d'%(fn,i,s_[0]),'kind':'st','cls':lt,'fn':fn,'rep':rep,'extra':[],'src':L[i].strip()[:100],'x':L[s_[0]].strip()[:80],'addr':'%s+%d'%lad})

        if 'r64' in kinds:
            for (i,v,t,ad,md) in loads:
                if t!='i64': continue
                if '!range' in md: continue
                base=ad[0]
                for k in (1,2):
                    seq+=1; c='%%asw%d'%seq
                    rep={i:[L[i],'  %s = icmp ule i64 %s, %d'%(c,v,k),'  call void @llvm.assume(i1 noundef zeroext %s)'%c]}
                    E.append({'id':'r64_%d:%s:%d'%(k,fn,i),'kind':'r64','cls':'le%d'%k,'fn':fn,'rep':rep,'extra':[],'src':L[i].strip()[:100],'addr':'%s+%d'%ad})
    with open(dst,'w') as f:
        for e in E: f.write(json.dumps(e)+'\n')
    print(len(E),collections.Counter((e['fn'],e['kind']) for e in E))
if __name__=='__main__': main(*sys.argv[1:])
