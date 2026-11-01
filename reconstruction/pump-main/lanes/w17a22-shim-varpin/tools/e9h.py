# frame-neutral E3: write new[24..33) (and new[1..8)) into hkx's unused 40 B tail (hkx base -0x6a0; tail -0x680..-0x658),
# where the original keeps new[24..33) at -0x668 (hkx+56). main m3 (53ec7fb) slim pre-opt IR.
B='  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_59, ptr align 1 %new, i64 33, i1 false)\n'
ANN=lambda p:f'  call void @llvm.var.annotation.p0.p0(ptr {p}, ptr null, ptr null, i32 0, ptr null)\n'
def cp(dst_off,src_off,n,tag,vol='false'):
    return (f'  %h{tag}.d = getelementptr inbounds i8, ptr %hkx, i64 {dst_off}\n  %h{tag}.s = getelementptr inbounds i8, ptr %new, i64 {src_off}\n'
            f'  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %h{tag}.d, ptr align 1 %h{tag}.s, i64 {n}, i1 {vol})\n')
A='  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_79, ptr align 1 %_59, i64 33, i1 false)\n'
ARM9=('  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_79, ptr align 1 %_59, i64 24, i1 false)\n'
      '  %jh.d24 = getelementptr inbounds i8, ptr %_79, i64 24\n  %jh.s = getelementptr inbounds i8, ptr %hkx, i64 56\n'
      '  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %jh.d24, ptr align 8 %jh.s, i64 9, i1 false)\n')
ARM9V=('  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_79, ptr align 1 %_59, i64 24, i1 false)\n'
      '  %jh.d24 = getelementptr inbounds i8, ptr %_79, i64 24\n  %jh.s = getelementptr inbounds i8, ptr %hkx, i64 56\n'
      '  %jh.w = load volatile i64, ptr %jh.s, align 8\n  store i64 %jh.w, ptr %jh.d24, align 1\n'
      '  %jh.s8 = getelementptr inbounds i8, ptr %hkx, i64 64\n  %jh.b = load volatile i8, ptr %jh.s8, align 8\n  %jh.d32 = getelementptr inbounds i8, ptr %_79, i64 32\n  store i8 %jh.b, ptr %jh.d32, align 1\n')
V={
 'e9h_dead':[(B,B+cp(56,24,9,'9'))],
 'e9h_deadv':[(B,B+cp(56,24,9,'9')+ANN('%hkx'))],
 'e9h_arm':[(B,B+cp(56,24,9,'9')),(A,ARM9)],
 'e9h_armv':[(B,B+cp(56,24,9,'9')),(A,ARM9V)],
 'e9h_vol':[(B,B+cp(56,24,9,'9','true')),(A,ARM9V)],
}
