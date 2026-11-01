# A: hopt carried through a lifetime-scoped volatile 1-byte alloca from entry to the closure; both masks read it
EDITS=[('start:\n','start:\n  %hm = alloca i8, align 1\n  call void @llvm.lifetime.start.p0(i64 1, ptr nonnull %hm)\n  store volatile i8 %0, ptr %hm, align 1\n'),
 ('  %45 = and i8 %0, -3\n','  %hl1 = load volatile i8, ptr %hm, align 1\n  %45 = and i8 %hl1, -3\n'),
 ('  %46 = and i8 %0, 1\n','  %hl2 = load volatile i8, ptr %hm, align 1\n  call void @llvm.lifetime.end.p0(i64 1, ptr nonnull %hm)\n  %46 = and i8 %hl2, 1\n')]
