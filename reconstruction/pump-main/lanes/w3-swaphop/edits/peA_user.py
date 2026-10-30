import os
def edit(t):
    pos=os.environ.get('POS','_505')
    a="  %"+pos+" = alloca"; i=t.index(a)
    if os.environ.get('BEFORE'): j=i
    else: j=t.index('\n',i)+1
    t=t[:j]+"  %pU = alloca [32 x i8], align 1\n"+t[j:]
    s="  call void @llvm.lifetime.start.p0(i64 32, ptr nonnull %_503)\n"
    assert s in t
    t=t.replace(s,s+"  call void @llvm.lifetime.start.p0(i64 32, ptr nonnull %pU)\n  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %pU, ptr align 1 %_933, i64 32, i1 false)\n",1)
    o="dereferenceable(64) %_989, ptr noalias nocapture noundef nonnull readonly align 1 dereferenceable(32) %_451,"
    assert o in t
    t=t.replace(o,"dereferenceable(64) %_989, ptr noalias nocapture noundef nonnull readonly align 1 dereferenceable(32) %pU,")
    return t
