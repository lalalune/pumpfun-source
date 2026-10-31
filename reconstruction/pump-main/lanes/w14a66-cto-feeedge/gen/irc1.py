EDITS=[("""  %107 = getelementptr inbounds i8, ptr %_49, i64 1
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_405, ptr align 1 %107, i64 32, i1 false)
  %108 = getelementptr inbounds i8, ptr %_48, i64 1
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %108, ptr align 1 %_405, i64 32, i1 false)
  store i8 0, ptr %_48, align 8
  call void @llvm.lifetime.end.p0(i64 32, ptr %_405)
  call void @llvm.lifetime.end.p0(i64 40, ptr %_49)
  %109 = getelementptr inbounds i8, ptr %_48, i64 1
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %val, ptr align 1 %109, i64 32, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %target, ptr align 1 %val, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 40, ptr %_48)
""","""  %107 = getelementptr inbounds i8, ptr %_49, i64 1
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %target, ptr align 1 %107, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_405)
  call void @llvm.lifetime.end.p0(i64 40, ptr %_49)
  call void @llvm.lifetime.end.p0(i64 40, ptr %_48)
""")]
