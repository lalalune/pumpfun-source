exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w17a10-shim-newpieces/ex/c1.py').read())
A20='  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_63, ptr align 1 %_45, i64 33, i1 false)\n'
def arm(vol=True,src8='%new',order=(8,16)):
    v=' volatile' if vol else ''
    s='  %jz.t = load i8, ptr %_45, align 1\n  store i8 %jz.t, ptr %_63, align 1\n'
    s+='  %jz.s1 = getelementptr inbounds i8, ptr %_45, i64 1\n  %jz.d1 = getelementptr inbounds i8, ptr %_63, i64 1\n  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %jz.d1, ptr align 1 %jz.s1, i64 7, i1 false)\n'
    for o in order:
        s+=f'  %jz.s{o} = getelementptr inbounds i8, ptr {src8}, i64 {o}\n  %jz.w{o} = load{v} i64, ptr %jz.s{o}, align 1\n  %jz.d{o} = getelementptr inbounds i8, ptr %_63, i64 {o}\n  store i64 %jz.w{o}, ptr %jz.d{o}, align 1\n'
    s+='  %jz.s24 = getelementptr inbounds i8, ptr %_45, i64 24\n  %jz.d24 = getelementptr inbounds i8, ptr %_63, i64 24\n  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %jz.d24, ptr align 1 %jz.s24, i64 9, i1 false)\n'
    return s
C1A=(VAL,piece('%sharing_update16','%val8'))
V={
 'j1v':[(A20,arm()),C1A],
 'j1v45':[(A20,arm(src8='%_45')),C1A],
 'j1n':[(A20,arm(vol=False)),C1A],
 'j1v_noc1':[(A20,arm())],
}
