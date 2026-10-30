A="  call void @llvm.lifetime.start.p0(i64 32, ptr %_341)\n  %92 = load i8, ptr %_44"
EDITS=[(A,"  store i8 0, ptr %new, align 1\n"+A)]
