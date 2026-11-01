# carry the closure's masked holder through a NEW volatile alloca WITH lifetime markers (def .. curve store)
EDITS=[('start:\n','start:\n  %hslot = alloca i8, align 1\n'),
 ('  %46 = and i8 %0, 1\n','  %46 = and i8 %0, 1\n  call void @llvm.lifetime.start.p0(i64 1, ptr nonnull %hslot)\n  store volatile i8 %46, ptr %hslot, align 1\n'),
 ('  store i8 %46, ptr %674, align 1\n','  %hv = load volatile i8, ptr %hslot, align 1\n  call void @llvm.lifetime.end.p0(i64 1, ptr nonnull %hslot)\n  store i8 %hv, ptr %674, align 1\n')]
