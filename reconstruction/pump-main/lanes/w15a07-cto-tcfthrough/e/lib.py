import re
def regep(lines_):
    def f(t):
        L=t.split('\n')
        for k,n in enumerate(sorted(lines_,reverse=True)):
            i=n-1; s=L[i]; assert '%330' in s,(n,s[:80])
            L[i]=re.sub(r'%330(?=[,)])','%%hv%d'%n,s)
            L.insert(i,'  %%hv%d = getelementptr inbounds i8, ptr %%_270, i64 264'%n)
        return '\n'.join(L)
    return f
BUMP_OLD='  store i8 %ctx.val62, ptr %_113.i, align 1, !noalias !8628\n'
BUMP_NEW='  %bmpp = getelementptr inbounds i8, ptr %ctx, i64 35\n  %bmpv = load i8, ptr %bmpp, align 1\n  store i8 %bmpv, ptr %_113.i, align 1, !noalias !8628\n'
NAT_OLD='  br i1 %326, label %bb26.i137, label %bb34.i\n'
NAT_NEW='''  %nq1 = getelementptr inbounds i8, ptr %_270, i64 24
  %nq2 = load ptr, ptr %nq1, align 8
  %nq3 = getelementptr inbounds i8, ptr %nq2, i64 88
  %nq4 = load ptr, ptr %nq3, align 8
  %nq5 = load ptr, ptr %nq4, align 8
  %nqc = call i32 @memcmp(ptr noundef nonnull dereferenceable(32) %nq5, ptr noundef nonnull dereferenceable(32) @alloc_e953c1d75e6a4349f2dca6892c168ab2, i64 32)
  %nqe = icmp eq i32 %nqc, 0
  br i1 %nqe, label %bb26.i137, label %bb34.i
'''
def regep_auto(t):
    L=t.split('\n'); out=[]; n=0
    for i,s in enumerate(L):
        if '%330' in s and not s.lstrip().startswith('%330 =') and ('ensure_rent_exempt' in s or 'collect_transfer_native' in s or ('clone17h' in s and s.rstrip().endswith('%330) #27, !noalias !8632'))):
            n+=1; out.append('  %%hv%d = getelementptr inbounds i8, ptr %%_270, i64 264'%n); s=re.sub(r'%330(?=[,)])','%%hv%d'%n,s)
        out.append(s)
    assert n==3,n
    return '\n'.join(out)
def bump_auto(t):
    m=re.search(r'\n  store i8 %ctx\.val62, ptr (%[\w.]+), align 1, !noalias !8628\n',t); assert m
    p=m.group(1)
    return t.replace(m.group(0),'\n  %%bmpp = getelementptr inbounds i8, ptr %%ctx, i64 35\n  %%bmpv = load i8, ptr %%bmpp, align 1\n  store i8 %%bmpv, ptr %s, align 1, !noalias !8628\n'%p,1)
def nat_auto(t):
    m=re.search(r'\n  br i1 %326, label (%[\w.]+), label (%[\w.]+)\n',t); assert m
    return t.replace(m.group(0),'\n'+NAT_NEW.replace('%bb26.i137',m.group(1)).replace('%bb34.i',m.group(2)),1)
ENTRY='start:\n  %_11.i285 = alloca [0 x i8], align 1\n'
def spd(which,pos='first'):
    """spill-at-def via allocas for a subset of 'h' (&holder_creator_vault), 'b' (bump), 'n' (native)"""
    def f(t):
        al=''
        if 'h' in which: al+='  %sp_hcv = alloca ptr, align 8\n'
        if 'b' in which: al+='  %sp_bmp = alloca i64, align 8\n'
        if 'n' in which: al+='  %sp_nat = alloca i64, align 8\n'
        assert t.count(ENTRY)==1
        t=t.replace(ENTRY, ENTRY+al if pos=='last' else 'start:\n'+al+ENTRY[len('start:\n'):])
        if 'h' in which:
            d='  %330 = getelementptr inbounds i8, ptr %_270, i64 264\n'; assert t.count(d)==1
            t=t.replace(d,d+'  store ptr %330, ptr %sp_hcv, align 8\n')
            L=t.split('\n'); out=[]; n=0
            for s in L:
                if '%330' in s and ('ensure_rent_exempt' in s or 'collect_transfer_native' in s or ('clone17h' in s and s.rstrip().endswith('%330) #27, !noalias !8632'))):
                    n+=1; out.append('  %%hl%d = load ptr, ptr %%sp_hcv, align 8'%n); s=re.sub(r'%330(?=[,)])','%%hl%d'%n,s)
                out.append(s)
            assert n==3; t='\n'.join(out)
        if 'b' in which:
            d='  %ctx.val62 = load i8, ptr %322, align 1\n'; assert t.count(d)==1
            t=t.replace(d,d+'  %bz = zext i8 %ctx.val62 to i64\n  store i64 %bz, ptr %sp_bmp, align 8\n')
            m=re.search(r'\n  store i8 %ctx\.val62, ptr (%[\w.]+), align 1, !noalias !8628\n',t)
            t=t.replace(m.group(0),'\n  %%bl = load i64, ptr %%sp_bmp, align 8\n  %%bt = trunc i64 %%bl to i8\n  store i8 %%bt, ptr %s, align 1, !noalias !8628\n'%m.group(1),1)
        if 'n' in which:
            d='  %326 = icmp eq i32 %325, 0\n'; assert t.count(d)==1
            t=t.replace(d,d+'  %nz = zext i1 %326 to i64\n  store i64 %nz, ptr %sp_nat, align 8\n')
            m=re.search(r'\n  br i1 %326, label (%[\w.]+), label (%[\w.]+)\n',t)
            t=t.replace(m.group(0),'\n  %%nl = load i64, ptr %%sp_nat, align 8\n  %%nt = trunc i64 %%nl to i1\n  br i1 %%nt, label %s, label %s\n'%(m.group(1),m.group(2)),1)
        return t
    return f
