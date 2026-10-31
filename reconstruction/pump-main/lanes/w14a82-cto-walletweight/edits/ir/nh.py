# hoist new's target piece loads (+8 i64, +16 ptr, +24 i64, +32 i8) to the entry, right after the tag byte load; bb45.i stores the hoisted values
def f(t):
    a="  %_45.sroa.0.0.copyload = load i8, ptr %new, align 1\n"; assert t.count(a)==1
    h=("  %nh8p = getelementptr inbounds i8, ptr %new, i64 8\n  %nh8 = load i64, ptr %nh8p, align 1\n"
       "  %nh16p = getelementptr inbounds i8, ptr %new, i64 16\n  %nh16 = load ptr, ptr %nh16p, align 1\n"
       "  %nh24p = getelementptr inbounds i8, ptr %new, i64 24\n  %nh24 = load i64, ptr %nh24p, align 1\n"
       "  %nh32p = getelementptr inbounds i8, ptr %new, i64 32\n  %nh32 = load i8, ptr %nh32p, align 1\n")
    t=t.replace(a,a+h)
    old=("  %target.i.sroa.7.0..sroa_idx = getelementptr inbounds i8, ptr %new, i64 8\n"
         "  %target.i.sroa.7.0.copyload284 = load i64, ptr %target.i.sroa.7.0..sroa_idx, align 1, !noalias !8570\n"
         "  %target.i.sroa.8.0..sroa_idx = getelementptr inbounds i8, ptr %new, i64 16\n"
         "  %target.i.sroa.8.0.copyload285 = load ptr, ptr %target.i.sroa.8.0..sroa_idx, align 1, !noalias !8570\n"
         "  %target.i.sroa.9.0..sroa_idx = getelementptr inbounds i8, ptr %new, i64 24\n")
    assert t.count(old)==1
    t=t.replace(old,"  %target.i.sroa.7.0.copyload284 = add i64 %nh8, 0\n  %target.i.sroa.8.0.copyload285 = getelementptr i8, ptr %nh16, i64 0\n")
    k="  %target.i.sroa.8.0.copyload285 = getelementptr i8, ptr %nh16, i64 0\n"; j=t.index(k)+len(k)
    line=t[j:t.index('\n',j)+1]; assert 'llvm.memcpy' in line and 'target.i.sroa.9.0..sroa_idx' in line, line
    t=t[:j]+"  store i64 %nh24, ptr %target.i.sroa.9, align 1\n  %nh9p = getelementptr inbounds i8, ptr %target.i.sroa.9, i64 8\n  store i8 %nh32, ptr %nh9p, align 1\n"+t[j+len(line):]
    return t
EDITS=[f]
