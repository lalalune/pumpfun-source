# E3 copy of `new` as separate 7 B and 9 B pieces pinned by llvm.var.annotation (w17a10 e79 layout, vann instead of
# volatile memcpy), on main m1 (2f3597f99) slim pre-opt IR. args copy = %_59, shared-arm payload = %_79.
HDR_OLD='(ptr noalias nocapture noundef readonly align 8 dereferenceable(48) %ctx, i8 noundef %0, i64 noundef %1, i64 %2, ptr noalias nocapture noundef align 1 dereferenceable(33) %new) unnamed_addr #1 {\nstart:\n'
def hdr(t,extra='  %e7 = alloca [7 x i8], align 1\n  %e9 = alloca [9 x i8], align 1\n'):
    i=t.index('@_ZN14pump_recovered9admin_cto7execute17h'); j=t.index('start:\n',i)+len('start:\n')
    return t[:j]+extra+t[j:]
ANN=lambda p:f'  call void @llvm.var.annotation.p0.p0(ptr {p}, ptr null, ptr null, i32 0, ptr null)\n'
B='  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_59, ptr align 1 %new, i64 33, i1 false)\n'
def ent(order='79',pin='after',lt=False):
    s7='  %ez.s1 = getelementptr inbounds i8, ptr %new, i64 1\n'+('  call void @llvm.lifetime.start.p0(i64 7, ptr %e7)\n' if lt else '')+'  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %e7, ptr align 1 %ez.s1, i64 7, i1 false)\n'
    s9='  %ez.s24 = getelementptr inbounds i8, ptr %new, i64 24\n'+('  call void @llvm.lifetime.start.p0(i64 9, ptr %e9)\n' if lt else '')+'  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %e9, ptr align 1 %ez.s24, i64 9, i1 false)\n'
    a=ANN('%e7')+ANN('%e9')
    body=(s7+s9) if order=='79' else (s9+s7)
    return B+(a+body if pin=='before' else body+a)
A='  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_79, ptr align 1 %_59, i64 33, i1 false)\n'
ARM=('  %jz.t = load i8, ptr %_59, align 1\n  store i8 %jz.t, ptr %_79, align 1\n'
 '  %jz.d1 = getelementptr inbounds i8, ptr %_79, i64 1\n  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %jz.d1, ptr align 1 %e7, i64 7, i1 false)\n'
 '  %jz.s8 = getelementptr inbounds i8, ptr %_59, i64 8\n  %jz.w8 = load i64, ptr %jz.s8, align 1\n  %jz.d8 = getelementptr inbounds i8, ptr %_79, i64 8\n  store i64 %jz.w8, ptr %jz.d8, align 1\n'
 '  %jz.s16 = getelementptr inbounds i8, ptr %_59, i64 16\n  %jz.w16 = load i64, ptr %jz.s16, align 1\n  %jz.d16 = getelementptr inbounds i8, ptr %_79, i64 16\n  store i64 %jz.w16, ptr %jz.d16, align 1\n'
 '  %jz.d24 = getelementptr inbounds i8, ptr %_79, i64 24\n  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %jz.d24, ptr align 1 %e9, i64 9, i1 false)\n')
LTEND='  call void @llvm.lifetime.end.p0(i64 7, ptr %e7)\n  call void @llvm.lifetime.end.p0(i64 9, ptr %e9)\n'
V={
 'e3v':[hdr,(B,ent()),(A,ARM)],
 'e3v97':[hdr,(B,ent(order='97')),(A,ARM)],
 'e3vpb':[hdr,(B,ent(pin='before')),(A,ARM)],
 'e3v_dead':[hdr,(B,ent())],
 'e3v_lt':[hdr,(B,ent(lt=True)),(A,ARM+LTEND)],
 'w59':[(B,B+ANN('%_59'))],
}
