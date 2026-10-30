import re
CP="  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_59, ptr align 1 %_27, i64 33, i1 false)\n"
SPL="""  %ec.t = load i8, ptr %_27, align 1
  store i8 %ec.t, ptr %_59, align 1
  %ec.s1 = getelementptr inbounds i8, ptr %_27, i64 1
  %ec.d1 = getelementptr inbounds i8, ptr %_59, i64 1
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %ec.d1, ptr align 1 %ec.s1, i64 7, i1 false)
  %ec.s8 = getelementptr inbounds i8, ptr %_27, i64 8
  %ec.d8 = getelementptr inbounds i8, ptr %_59, i64 8
  %ec.v8 = load i64, ptr %ec.s8, align 1
  store i64 %ec.v8, ptr %ec.d8, align 1
  %ec.s16 = getelementptr inbounds i8, ptr %_27, i64 16
  %ec.d16 = getelementptr inbounds i8, ptr %_59, i64 16
  %ec.v16 = load i64, ptr %ec.s16, align 1
  store i64 %ec.v16, ptr %ec.d16, align 1
  %ec.s24 = getelementptr inbounds i8, ptr %_27, i64 24
  %ec.d24 = getelementptr inbounds i8, ptr %_59, i64 24
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %ec.d24, ptr align 1 %ec.s24, i64 9, i1 false)
"""
def clob(t):
    m=re.search(r'; call pump_recovered::admin_cto::validate\n  call void @\S+validate\S+\(.*\n',t)
    return t[:m.end()]+"  call void @llvm.memset.p0.i64(ptr align 1 %new, i8 0, i64 33, i1 false)\n"+t[m.end():]
MC="  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_27, ptr align 1 %new, i64 33, i1 false)\n"
SKS="  call void @llvm.lifetime.start.p0(i64 32, ptr %sk)\n"
def mv(t):
    assert t.count(MC)==1 and t.count(SKS)==1
    t=t.replace(MC,''); return t.replace(SKS,MC+SKS)
VALC="; call pump_recovered::admin_cto::validate\n"
def mv2(t):
    t=t.replace(MC,''); return t.replace(VALC,MC+VALC)
