# A: only the outer and -3 reads hopt from a lifetime-scoped volatile alloca (entry .. outer test); closure keeps %0
EDITS=[('start:\n','start:\n  %hm = alloca i8, align 1\n  call void @llvm.lifetime.start.p0(i64 1, ptr nonnull %hm)\n  store volatile i8 %0, ptr %hm, align 1\n'),
 ('  %45 = and i8 %0, -3\n','  %hl1 = load volatile i8, ptr %hm, align 1\n  call void @llvm.lifetime.end.p0(i64 1, ptr nonnull %hm)\n  %45 = and i8 %hl1, -3\n')]
