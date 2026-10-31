# original-like entry copy of new: 7-byte piece and 9-byte piece memcpy'd into fresh allocas at entry, +8/+16 as SSA values;
# validate's non-holder arm (bb45.i) reads the copies instead of new
def f(t):
    t=t.replace("start:\n","start:\n  %ne7 = alloca [7 x i8], align 1\n  %ne9 = alloca [9 x i8], align 1\n",1)
    a="  %_45.sroa.5.0.new.sroa_idx = getelementptr inbounds i8, ptr %new, i64 1\n"; assert t.count(a)==1
    h=("  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %ne7, ptr align 1 %_45.sroa.5.0.new.sroa_idx, i64 7, i1 false)\n"
       "  %nh8p = getelementptr inbounds i8, ptr %new, i64 8\n  %nh8 = load i64, ptr %nh8p, align 1\n"
       "  %nh16p = getelementptr inbounds i8, ptr %new, i64 16\n  %nh16 = load ptr, ptr %nh16p, align 1\n"
       "  %nh24p = getelementptr inbounds i8, ptr %new, i64 24\n"
       "  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %ne9, ptr align 1 %nh24p, i64 9, i1 false)\n")
    t=t.replace(a,a+h)
    old=("  %target.i.sroa.7.0..sroa_idx = getelementptr inbounds i8, ptr %new, i64 8\n"
         "  %target.i.sroa.7.0.copyload284 = load i64, ptr %target.i.sroa.7.0..sroa_idx, align 1, !noalias !8570\n"
         "  %target.i.sroa.8.0..sroa_idx = getelementptr inbounds i8, ptr %new, i64 16\n"
         "  %target.i.sroa.8.0.copyload285 = load ptr, ptr %target.i.sroa.8.0..sroa_idx, align 1, !noalias !8570\n"
         "  %target.i.sroa.9.0..sroa_idx = getelementptr inbounds i8, ptr %new, i64 24\n")
    assert t.count(old)==1
    t=t.replace(old,"  %target.i.sroa.7.0.copyload284 = add i64 %nh8, 0\n  %target.i.sroa.8.0.copyload285 = getelementptr i8, ptr %nh16, i64 0\n  %target.i.sroa.9.0..sroa_idx = getelementptr i8, ptr %ne9, i64 0\n")
    a="dereferenceable(7) %target.i.sroa.0, ptr noundef nonnull align 1 dereferenceable(7) %_45.sroa.5.0.new.sroa_idx, i64 7"
    assert t.count(a)==1, t.count(a)
    t=t.replace(a,"dereferenceable(7) %target.i.sroa.0, ptr noundef nonnull align 1 dereferenceable(7) %ne7, i64 7")
    return t
EDITS=[f]
