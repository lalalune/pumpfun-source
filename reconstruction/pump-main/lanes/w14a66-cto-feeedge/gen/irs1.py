CH="""  %107 = getelementptr inbounds i8, ptr %_49, i64 1
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
"""
import sys;sys.path.insert(0,"/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a66-cto-feeedge/tools");from fx import inexec
EDITS=[inexec([(CH,""),
("""bb20:                                             ; preds = %bb19
""","""bb20:                                             ; preds = %bb19
  %x107a = getelementptr inbounds i8, ptr %_49, i64 1
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %target, ptr align 1 %x107a, i64 32, i1 false)
"""),
("""bb22:                                             ; preds = %bb74
""","""bb22:                                             ; preds = %bb74
  %x107b = getelementptr inbounds i8, ptr %_49, i64 1
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %target, ptr align 1 %x107b, i64 32, i1 false)
""")])]
