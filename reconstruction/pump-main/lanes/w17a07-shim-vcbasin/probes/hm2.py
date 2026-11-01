# A: only the closure's and 1 reads hopt from the alloca; the outer test keeps %0
EDITS=[('start:\n','start:\n  %hm = alloca i8, align 1\n  call void @llvm.lifetime.start.p0(i64 1, ptr nonnull %hm)\n  store volatile i8 %0, ptr %hm, align 1\n'),
 ('  %46 = and i8 %0, 1\n','  %hl2 = load volatile i8, ptr %hm, align 1\n  call void @llvm.lifetime.end.p0(i64 1, ptr nonnull %hm)\n  %46 = and i8 %hl2, 1\n')]
