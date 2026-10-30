def edit(f):
    v='%_3.sroa.5.0._0.sroa_idx.i'
    return f.replace(f'call void @llvm.memset.p0.i64(ptr noundef nonnull align 8 dereferenceable(32) {v}, i8 0, i64 32, i1 false)','call void @llvm.donothing()')
