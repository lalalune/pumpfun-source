import os
def edit(t):
    k='  %0 = getelementptr inbounds i8, ptr %ctx, i64 8\n'
    n=int(os.environ.get('N','1'))
    add=''.join(f'  call void @llvm.lifetime.start.p0(i64 16, ptr nonnull %_207.i)\n' for _ in range(n))
    return t.replace(k,add+k,1)
