import runpy,os
E=runpy.run_path(os.path.join(os.path.dirname(__file__),'nh1.py'))['EDITS']
T='''  %_39.sroa.0.0.copyload = load i8, ptr %new, align 1
'''
M7='''  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(7) %target.i.sroa.0, ptr noundef nonnull align 1 dereferenceable(7) %_39.sroa.5.0.new.sroa_idx, i64 7, i1 false), !noalias !8575
'''
M9='''  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(9) %target.i.sroa.9, ptr noundef nonnull align 1 dereferenceable(9) %target.i.sroa.9.0..sroa_idx, i64 9, i1 false), !noalias !8575
'''
AL='''  %target.i.sroa.0 = alloca [7 x i8], align 1
'''
EDITS0=[(AL,AL+'  %nc7 = alloca [7 x i8], align 1\n  %nc9 = alloca [9 x i8], align 1\n'),
 (M7,M7.replace('%target.i.sroa.0, ptr noundef nonnull align 1 dereferenceable(7) %_39.sroa.5.0.new.sroa_idx','%target.i.sroa.0, ptr noundef nonnull align 1 dereferenceable(7) %nc7')),
 (M9,M9.replace('%target.i.sroa.9.0..sroa_idx, i64 9','%nc9, i64 9')),
 (T+'  %_39.sroa.5.0.new.sroa_idx = getelementptr inbounds i8, ptr %new, i64 1\n', T+'  %_39.sroa.5.0.new.sroa_idx = getelementptr inbounds i8, ptr %new, i64 1\n  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %nc7, ptr align 1 %_39.sroa.5.0.new.sroa_idx, i64 7, i1 false)\n  %nc9src = getelementptr inbounds i8, ptr %new, i64 24\n  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %nc9, ptr align 1 %nc9src, i64 9, i1 false)\n')]
EDITS=[EDITS0[-1]]+E+EDITS0[:-1]
