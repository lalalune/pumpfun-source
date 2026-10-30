import re
def edit(f):
    for p in ('_3','_49'):
        v=f'%{p}.sroa.5.0._0.sroa_idx.i'
        f=f.replace(f'call void @llvm.memset.p0.i64(ptr noundef nonnull align 8 dereferenceable(32) {v}, i8 0, i64 32, i1 false)',f'call void @llvm.memset.p0.i64(ptr noundef nonnull align 8 dereferenceable(33) {v}, i8 0, i64 33, i1 false)')
        f=re.sub(r'\n  store i8 0, ptr %'+p+r'\.sroa\.6\.0\._0\.sroa_idx\.i, align 8[^\n]*','',f)
    return f
