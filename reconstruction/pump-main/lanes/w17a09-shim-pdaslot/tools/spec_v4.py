V={}
B=[('_17','bb2','bb4'),('_19','bb3','bb4'),('_25','bb7','bb8'),('_27','bb9','bb10')]
for nm,t,f in B:
    for val in ('true','false'):
        V[f'x{nm}{val[0]}']=[(f'  br i1 %{nm}, label %{t}, label %{f}\n', f'  %{nm}.x = call zeroext i1 @llvm.expect.i1(i1 zeroext %{nm}, i1 zeroext {val})\n  br i1 %{nm}.x, label %{t}, label %{f}\n')]
# hk short-lived: end hk's lifetime right after the holder_key copy (like v3)
V['hkshort']=[('  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %holder_key, ptr align 1 %_15, i64 32, i1 false)\n','  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %holder_key, ptr align 1 %_15, i64 32, i1 false)\n  call void @llvm.lifetime.end.p0(i64 33, ptr %hk)\n')]
