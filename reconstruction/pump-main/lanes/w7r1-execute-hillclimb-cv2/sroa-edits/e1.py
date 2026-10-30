import re
def edit(f):
    for v in ('%_3.sroa.5.0._0.sroa_idx.i','%_49.sroa.5.0._0.sroa_idx.i'):
        f=re.sub(r'call void @llvm.memset.p0.i64\(ptr noundef nonnull align 8 dereferenceable\(32\) '+re.escape(v)+r', i8 0, i64 32, i1 false\)',
          f'store ptr null, ptr {v}, align 8\n  %{v[1:]}.w1 = getelementptr inbounds i8, ptr {v}, i64 8\n  call void @llvm.memset.p0.i64(ptr align 8 %{v[1:]}.w1, i8 0, i64 24, i1 false)',f)
    return f
