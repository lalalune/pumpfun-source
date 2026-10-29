import os,re
def edit(t):
    X=os.environ['X']
    i=t.index('define hidden { i64, ptr } @_ZN14pump_recovered5trade4sell17h'); j=t.index('\n}',i)
    f=t[i:j]
    f2=re.sub(r'\n\s+call void @llvm\.lifetime\.(start|end)\.p0\(i64 \d+, ptr nonnull '+re.escape(X)+r'\)[^\n]*','',f)
    k='  call void @llvm.lifetime.start.p0(i64 48, ptr nonnull %_184.i)\n'
    pos=os.environ.get('POS','top')
    sz=re.search(re.escape(X)+r' = alloca \[(\d+) x i8\]',f).group(1)
    ins=f'  call void @llvm.lifetime.start.p0(i64 {sz}, ptr nonnull {X})\n'
    if pos=='top': f2=f2.replace(k,ins+k,1)
    else: f2=f2.replace('  %0 = getelementptr inbounds i8, ptr %ctx, i64 8\n',ins+'  %0 = getelementptr inbounds i8, ptr %ctx, i64 8\n',1)
    # add lifetime.end before ret? skip
    return t[:i]+f2+t[j:]
