import os
def edit(t):
    n=int(os.environ['N']); L=t.split('\n')
    s=next(i for i,l in enumerate(L) if l.startswith('define') and 'trade15buy_exact_quote17h' in l)
    i=next(i for i in range(s,s+300) if 'lifetime.start.p0(i64 48, ptr nonnull %val.sroa.5.i)' in L[i])
    a=next(i for i in range(s,s+300) if ' = alloca' in L[i])
    for k in range(n):
        L.insert(i+1,f'  call void @llvm.lifetime.start.p0(i64 8, ptr nonnull %dummy{k})')
    for k in range(n): L.insert(a,f'  %dummy{k} = alloca [8 x i8], align 8')
    return '\n'.join(L)
