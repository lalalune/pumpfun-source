VAL='  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %val8, ptr align 1 %sharing_update16, i64 33, i1 false)\n'
B15='  call void @llvm.lifetime.start.p0(i64 33, ptr %_45)\n  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_45, ptr align 1 %new, i64 33, i1 false)\n'
def entry(vol=True,ty='i64',which=(8,16),pos='pre'):
    v=' volatile' if vol else ''
    s=''.join(f'  %nz.p{o} = getelementptr inbounds i8, ptr %new, i64 {o}\n  %nz.w{o} = load{v} {ty}, ptr %nz.p{o}, align 1\n' for o in which)
    return (s+B15) if pos=='pre' else (B15+s)
def c1(mode='split',which=(8,16),ty='i64'):
    st=''.join(f'  %nz.d{o} = getelementptr inbounds i8, ptr %val8, i64 {o}\n  store {ty} %nz.w{o}, ptr %nz.d{o}, align 1\n' for o in which)
    if mode=='over': return VAL+st
    t='  %nz.t = load i8, ptr %sharing_update16, align 1\n  store i8 %nz.t, ptr %val8, align 1\n'
    s7='  %nz.s1 = getelementptr inbounds i8, ptr %sharing_update16, i64 1\n  %nz.d1 = getelementptr inbounds i8, ptr %val8, i64 1\n  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %nz.d1, ptr align 1 %nz.s1, i64 7, i1 false)\n'
    s9='  %nz.s24 = getelementptr inbounds i8, ptr %sharing_update16, i64 24\n  %nz.d24 = getelementptr inbounds i8, ptr %val8, i64 24\n  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %nz.d24, ptr align 1 %nz.s24, i64 9, i1 false)\n'
    if mode=='split': return t+s7+st+s9
    if mode=='split2': return t+s7+s9+st
V={
 'x3a':[(B15,entry()),(VAL,c1('split'))],
 'x3b':[(B15,entry()),(VAL,c1('over'))],
 'x3c':[(B15,entry(vol=False)),(VAL,c1('split'))],
 'x3d':[(B15,entry(pos='post')),(VAL,c1('split'))],
 'x3e':[(B15,entry(which=(16,8))),(VAL,c1('split',which=(16,8)))],
 'x3f':[(B15,entry()),(VAL,c1('split2'))],
 'x3g':[(B15,entry(ty='ptr')),(VAL,c1('split',ty='ptr'))],
}
V2={
 'x3h_entry_only':[(B15,entry())],
 'x3i_c1_only_split_from_su':[(VAL,c1('split').replace('%nz.w8','%nz.q8').replace('%nz.w16','%nz.q16').replace('  %nz.d8 =','  %nz.e8 = getelementptr inbounds i8, ptr %sharing_update16, i64 8\n  %nz.q8 = load i64, ptr %nz.e8, align 1\n  %nz.d8 =').replace('  %nz.d16 =','  %nz.e16 = getelementptr inbounds i8, ptr %sharing_update16, i64 16\n  %nz.q16 = load i64, ptr %nz.e16, align 1\n  %nz.d16 ='))],
 'x3j_c1_memcpy_tagsplit':[(VAL,'  %nz.t = load i8, ptr %sharing_update16, align 1\n  store i8 %nz.t, ptr %val8, align 1\n  %nz.s1 = getelementptr inbounds i8, ptr %sharing_update16, i64 1\n  %nz.d1 = getelementptr inbounds i8, ptr %val8, i64 1\n  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %nz.d1, ptr align 1 %nz.s1, i64 32, i1 false)\n')],
}
V=V2
