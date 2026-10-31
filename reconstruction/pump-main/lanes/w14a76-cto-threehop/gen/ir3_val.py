import re
VF='define internal void @_ZN14pump_recovered9admin_cto8validate17h'
def inval(t):
    k=t.index(VF); e=t.index('\n}\n',k); b=t[k:e]
    def rep(x,y,n=1):
        nonlocal b; c=b.count(x); assert c==n,(c,x[:100]); b=b.replace(x,y)
    rep('  call void @llvm.lifetime.start.p0(i64 32, ptr %target)\n','')
    rep('  call void @llvm.lifetime.end.p0(i64 32, ptr %target)\n','',2)
    rep('call void @llvm.memcpy.p0.p0.i64(ptr align 1 %target, ptr align 1 %t, i64 32, i1 false)',
        '%w3a = getelementptr inbounds i8, ptr %_0, i64 1\n  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %w3a, ptr align 1 %t, i64 32, i1 false)')
    rep('call void @llvm.memcpy.p0.p0.i64(ptr align 1 %target, ptr align 1 %holder_key, i64 32, i1 false)',
        '%w3b = getelementptr inbounds i8, ptr %_0, i64 1\n  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %w3b, ptr align 1 %holder_key, i64 32, i1 false)')
    rep('''  call void @llvm.lifetime.start.p0(i64 32, ptr %_136)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_136, ptr align 1 %target, i64 32, i1 false)
  %101 = getelementptr inbounds i8, ptr %_0, i64 1
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %101, ptr align 1 %_136, i64 32, i1 false)
  store i8 0, ptr %_0, align 8
  call void @llvm.lifetime.end.p0(i64 32, ptr %_136)
''','''  store i8 0, ptr %_0, align 8
''')
    return t[:k]+b+t[e:]
