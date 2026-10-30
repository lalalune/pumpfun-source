import re
def f(t):
    i=t.index('define hidden { i64, ptr } @_ZN14pump_recovered9admin_cto7execute17h')
    j=t.index('\n}\n',i); s=t[i:j]
    s=s.replace(' %new) unnamed_addr',' %new.arg) unnamed_addr',1)
    assert '%new.arg' in s
    s=s.replace('start:\n','start:\n  %new = alloca [33 x i8], align 1\n  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %new, ptr align 1 %new.arg, i64 33, i1 false)\n',1)
    return t[:i]+s+t[j:]
EDITS=[f]
