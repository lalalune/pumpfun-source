import os
POS=os.environ.get('NCPOS','  store i8 %84, ptr %83, align 1\n')
def f(t):
    i=t.index('define hidden { i64, ptr } @_ZN14pump_recovered9admin_cto7execute17h')
    j=t.index('\n}\n',i); s=t[i:j]
    s=s.replace(' %new) unnamed_addr',' %new.arg) unnamed_addr',1)
    assert s.count(POS)==1,POS
    s=s.replace(POS,POS+'  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %new, ptr align 1 %new.arg, i64 33, i1 false)\n')
    s=s.replace('start:\n','start:\n  %new = alloca [33 x i8], align 1\n',1)
    return t[:i]+s+t[j:]
EDITS=[f]
