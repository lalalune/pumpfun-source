import re
def edit(t):
    S='%_5.sroa.5.i'
    a=f"  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) {S}, ptr noundef nonnull align 8 dereferenceable(24) %64, i64 24, i1 false)\n"
    assert a in t
    t=t.replace(a,f"  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull {S})\n"+a)
    b=f"  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %rent.i, ptr noundef nonnull align 8 dereferenceable(24) {S}, i64 24, i1 false)\n"
    assert b in t
    t=t.replace(b,b+f"  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull {S})\n")
    m=re.search(r'(  %\d+ = call \{ i64, ptr \} @"_ZN107_\$LT\$anchor_lang..error..Error\$u20\$as\$u20\$core..convert..From\$LT\$solana_program_error..ProgramError\$GT\$\$GT\$4from[^\n]*'+re.escape(S)+r'\)[^\n]*\n)',t)
    t=t.replace(m.group(1),m.group(1)+f"  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull {S})\n")
    return t
