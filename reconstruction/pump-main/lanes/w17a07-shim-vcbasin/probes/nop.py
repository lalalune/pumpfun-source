# new unused alloca with lifetime markers only in the entry (frame-shift calibration)
EDITS=[('start:\n','start:\n  %hslot = alloca i8, align 1\n  call void @llvm.lifetime.start.p0(i64 1, ptr nonnull %hslot)\n  store volatile i8 %0, ptr %hslot, align 1\n  call void @llvm.lifetime.end.p0(i64 1, ptr nonnull %hslot)\n')]
