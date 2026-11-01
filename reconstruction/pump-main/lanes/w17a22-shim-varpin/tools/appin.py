# accounts pointer kept in a pinned 8 B local (vann), re-read from that slot at every use: the original reloads the
# accounts pointer from the stack per clone (T1/C1). On main m3 (53ec7fb) slim pre-opt IR.
import re
FN={'execute':r'admin_cto7execute17h','wallet':r'admin_cto7execute6wallet17h','sweep':r'admin_cto7execute5sweep17h'}
ANN='  call void @llvm.var.annotation.p0.p0(ptr %apx, ptr null, ptr null, i32 0, ptr null)'
def rng(L,p):
    a=[i for i,l in enumerate(L) if l.startswith('define') and re.search(p,l.split('(')[0])][0]; b=a
    while L[b]!='}': b+=1
    return a,b
def pin(fn,mode='all',skip=0):
    def f(t):
        L=t.split('\n'); a,b=rng(L,FN[fn])
        geps=set()
        for i in range(a,b):
            m=re.match(r'^\s+(%\S+) = getelementptr inbounds i8, ptr %ctx, i64 8$',L[i])
            if m: geps.add(m.group(1))
        loads=[i for i in range(a,b) if (lambda m: m and m.group(2) in geps)(re.match(r'^\s+(%\S+) = load ptr, ptr (%\S+), align 8',L[i]))]
        first=loads[0]
        m=re.match(r'^\s+(%\S+) = load ptr, ptr (%\S+), align 8',L[first]); v0=m.group(1)
        out=list(L)
        # alloca in entry block
        k=a+1
        while not L[k].startswith('start:'): k+=1
        ins={k+1:['  %apx = alloca [8 x i8], align 8']}
        ins.setdefault(first+1,[]).extend(['  store ptr %s, ptr %%apx, align 8'%v0, ANN])
        rep={}
        if fn=='execute':
            for n,i in enumerate(loads[1:]):
                if n<skip: continue
                rep[i]=re.sub(r'load ptr, ptr %\S+, align 8','load ptr, ptr %apx, align 8',L[i],count=1)
        else:
            # one load: re-read at every non-phi use after the def
            c=0
            for i in range(first+1,b):
                l=L[i]
                if re.search(re.escape(v0)+r'(?![\w.$-])',l) and not re.match(r'^\s+%\S+ = phi',l):
                    nv='%%apr%d'%c; c+=1
                    ins.setdefault(i,[]).append('  %s = load ptr, ptr %%apx, align 8'%nv)
                    rep[i]=re.sub(re.escape(v0)+r'(?![\w.$-])',nv,l)
        res=[]
        for i,l in enumerate(out):
            if i in ins and i!=first+1: res.extend(ins[i])
            res.append(rep.get(i,l))
            if i==first and (first+1) in ins: res.extend(ins[first+1])
        return '\n'.join(res)
    return f
V={'ap_exe':[pin('execute')],'ap_sweep':[pin('sweep')],'ap_wallet':[pin('wallet')],
   'ap_exe_sweep':[pin('execute'),pin('sweep')],'ap_all':[pin('execute'),pin('sweep'),pin('wallet')]}
