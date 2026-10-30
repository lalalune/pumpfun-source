import re
def edit(f):
    m=re.search(r'call void @llvm.memcpy.p0.p0.i64\(ptr noundef nonnull align 8 dereferenceable\(32\) (%_148.sroa.5.0._0.sroa_idx.i), ptr noundef nonnull align 1 dereferenceable\(32\) %mint_key.i, i64 32, i1 false\)[^\n]*',f)
    d=m.group(1)
    new=f'%mk.w0 = load ptr, ptr %mint_key.i, align 1\n  store ptr %mk.w0, ptr {d}, align 8\n  %mk.s1 = getelementptr inbounds i8, ptr %mint_key.i, i64 8\n  %mk.d1 = getelementptr inbounds i8, ptr {d}, i64 8\n  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %mk.d1, ptr align 1 %mk.s1, i64 24, i1 false)'
    return f[:m.start()]+new+f[m.end():]
