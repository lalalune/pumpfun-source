A="  call void @llvm.lifetime.start.p0(i64 32, ptr %_341)\n  %92 = load i8, ptr %_44"
EDITS=[(A,"  call void @llvm.memset.p0.i64(ptr align 1 %new, i8 0, i64 33, i1 false)\n"+A)]
