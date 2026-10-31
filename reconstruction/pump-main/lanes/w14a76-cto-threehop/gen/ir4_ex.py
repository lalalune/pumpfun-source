import sys;sys.path.insert(0,"/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a76-cto-threehop/tools");from fx import inexec
CH="""  %107 = getelementptr inbounds i8, ptr %_49, i64 1
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_410, ptr align 1 %107, i64 32, i1 false)
  %108 = getelementptr inbounds i8, ptr %_48, i64 1
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %108, ptr align 1 %_410, i64 32, i1 false)
  store i8 0, ptr %_48, align 8
  call void @llvm.lifetime.end.p0(i64 32, ptr %_410)
  call void @llvm.lifetime.end.p0(i64 40, ptr %_49)
  %109 = getelementptr inbounds i8, ptr %_48, i64 1
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %val, ptr align 1 %109, i64 32, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %target, ptr align 1 %val, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 40, ptr %_48)
  call void @llvm.lifetime.start.p0(i64 1, ptr %_549)
  call void @llvm.lifetime.start.p0(i64 33, ptr %_550)
  call void @llvm.lifetime.start.p0(i64 1, ptr %_551)
"""
LT="""  call void @llvm.lifetime.start.p0(i64 1, ptr %_549)
  call void @llvm.lifetime.start.p0(i64 33, ptr %_550)
  call void @llvm.lifetime.start.p0(i64 1, ptr %_551)
"""
def cp(tag): return f"""  %x{tag} = getelementptr inbounds i8, ptr %_49, i64 1
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %target, ptr align 1 %x{tag}, i64 32, i1 false)
"""
H19="bb19:                                             ; preds = %bb76\n"
H20="bb20:                                             ; preds = %bb19\n"
H22="bb22:                                             ; preds = %bb76\n"
MODE=globals().get('MODE','arms')
P=[(CH,"")]
if MODE=='arms':   # copy in bb20 (shared holder) and bb22 (not shared); bb21 overwrites with creator
    P+=[(H19,H19+LT),(H20,H20+cp('a')),(H22,H22+LT+cp('b'))]
elif MODE=='all3': # copy also in bb21 before the creator overwrite
    P+=[(H19,H19+LT),(H20,H20+cp('a')),(H22,H22+LT+cp('b')),("bb21:                                             ; preds = %bb19\n","bb21:                                             ; preds = %bb19\n"+cp('c'))]
elif MODE=='keeplt':  # chain gone, lifetimes stay in bb76, copies in arms
    P=[(CH,LT),(H20,H20+cp('a')),(H22,H22+cp('b'))]
EX=inexec(P)
