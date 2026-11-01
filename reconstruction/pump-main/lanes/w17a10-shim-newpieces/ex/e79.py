exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w17a10-shim-newpieces/ex/c1.py').read())
HDR='(ptr noalias nocapture noundef align 1 dereferenceable(33) %new) unnamed_addr #1 {\nstart:\n'
def hdr(t):
    i=t.index('@_ZN14pump_recovered9admin_cto7execute17h'); j=t.index('start:\n',i)+len('start:\n')
    return t[:j]+'  %e7 = alloca [7 x i8], align 1\n  %e9 = alloca [9 x i8], align 1\n'+t[j:]
B15='  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_45, ptr align 1 %new, i64 33, i1 false)\n'
def ent(vol=True,order='79'):
    v='true' if vol else 'false'
    s7=f'  %ez.s1 = getelementptr inbounds i8, ptr %new, i64 1\n  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %e7, ptr align 1 %ez.s1, i64 7, i1 {v})\n'
    s9=f'  %ez.s24 = getelementptr inbounds i8, ptr %new, i64 24\n  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %e9, ptr align 1 %ez.s24, i64 9, i1 {v})\n'
    return B15+(s7+s9 if order=='79' else s9+s7)
A20='  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_63, ptr align 1 %_45, i64 33, i1 false)\n'
ARM=('  %jz.t = load i8, ptr %_45, align 1\n  store i8 %jz.t, ptr %_63, align 1\n'
 '  %jz.d1 = getelementptr inbounds i8, ptr %_63, i64 1\n  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %jz.d1, ptr align 1 %e7, i64 7, i1 false)\n'
 '  %jz.s8 = getelementptr inbounds i8, ptr %_45, i64 8\n  %jz.w8 = load i64, ptr %jz.s8, align 1\n  %jz.d8 = getelementptr inbounds i8, ptr %_63, i64 8\n  store i64 %jz.w8, ptr %jz.d8, align 1\n'
 '  %jz.s16 = getelementptr inbounds i8, ptr %_45, i64 16\n  %jz.w16 = load i64, ptr %jz.s16, align 1\n  %jz.d16 = getelementptr inbounds i8, ptr %_63, i64 16\n  store i64 %jz.w16, ptr %jz.d16, align 1\n'
 '  %jz.d24 = getelementptr inbounds i8, ptr %_63, i64 24\n  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %jz.d24, ptr align 1 %e9, i64 9, i1 false)\n')
C1A=(VAL,piece('%sharing_update16','%val8'))
V={
 'e79v':[hdr,(B15,ent()),(A20,ARM),C1A],
 'e97v':[hdr,(B15,ent(order='97')),(A20,ARM),C1A],
 'e79n':[hdr,(B15,ent(vol=False)),(A20,ARM),C1A],
 'e79v_noc1':[hdr,(B15,ent()),(A20,ARM)],
}
ARM9=('  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_63, ptr align 1 %_45, i64 33, i1 false)\n'
 '  %jz.d24 = getelementptr inbounds i8, ptr %_63, i64 24\n  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %jz.d24, ptr align 1 %e9, i64 9, i1 false)\n')
ARM7=('  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_63, ptr align 1 %_45, i64 33, i1 false)\n'
 '  %jz.d1 = getelementptr inbounds i8, ptr %_63, i64 1\n  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %jz.d1, ptr align 1 %e7, i64 7, i1 false)\n')
def ent1(which):
    s=''
    if '7' in which: s+='  %ez.s1 = getelementptr inbounds i8, ptr %new, i64 1\n  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %e7, ptr align 1 %ez.s1, i64 7, i1 true)\n'
    if '9' in which: s+='  %ez.s24 = getelementptr inbounds i8, ptr %new, i64 24\n  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %e9, ptr align 1 %ez.s24, i64 9, i1 true)\n'
    return B15+s
V={
 'e9only':[hdr,(B15,ent1('9')),(A20,ARM9)],
 'e7only':[hdr,(B15,ent1('7')),(A20,ARM7)],
 'e9only_dead':[hdr,(B15,ent1('9'))],
 'e79_dead':[hdr,(B15,ent1('79'))],
}
