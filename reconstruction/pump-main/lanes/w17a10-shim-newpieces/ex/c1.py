VAL='  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %val8, ptr align 1 %sharing_update16, i64 33, i1 false)\n'
def piece(src,dst,mid='i64',order=(8,16),nine=True,tagfirst=True,vol=False):
    v=' volatile' if vol else ''
    s=[]
    t=f'  %pz.t = load{v} i8, ptr {src}, align 1\n  store i8 %pz.t, ptr {dst}, align 1\n'
    s7=f'  %pz.s1 = getelementptr inbounds i8, ptr {src}, i64 1\n  %pz.d1 = getelementptr inbounds i8, ptr {dst}, i64 1\n  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %pz.d1, ptr align 1 %pz.s1, i64 7, i1 false)\n'
    def w(o): return f'  %pz.s{o} = getelementptr inbounds i8, ptr {src}, i64 {o}\n  %pz.w{o} = load{v} {mid}, ptr %pz.s{o}, align 1\n  %pz.d{o} = getelementptr inbounds i8, ptr {dst}, i64 {o}\n  store {mid} %pz.w{o}, ptr %pz.d{o}, align 1\n'
    s9=f'  %pz.s24 = getelementptr inbounds i8, ptr {src}, i64 24\n  %pz.d24 = getelementptr inbounds i8, ptr {dst}, i64 24\n  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %pz.d24, ptr align 1 %pz.s24, i64 9, i1 false)\n'
    body=(t if tagfirst else '')+s7+''.join(w(o) for o in order)+s9+('' if tagfirst else t)
    return body
V={
 'c1a':[(VAL,piece('%sharing_update16','%val8'))],
 'c1b':[(VAL,piece('%sharing_update16','%val8',order=(16,8)))],
 'c1c':[(VAL,piece('%sharing_update16','%val8',mid='ptr'))],
 'c1d':[(VAL,piece('%sharing_update16','%val8',tagfirst=False))],
}
