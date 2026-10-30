import os,runpy
V=[('authority_info',48),('inner_data',24),('_184',48),('_200',24)]
def edit(f):
    f=runpy.run_path(os.path.dirname(__file__)+'/x_phi.py')['edit'](f)
    anchor='  %_178 = getelementptr inbounds i8, ptr %a, i64 128\n'
    assert f.count(anchor)==1
    st=''.join(f'  call void @llvm.lifetime.start.p0(i64 {n}, ptr nonnull %{v})\n' for v,n in V)
    f=f.replace(anchor,st+anchor)
    en=''.join(f'  call void @llvm.lifetime.end.p0(i64 {n}, ptr nonnull %{v})\n' for v,n in V)
    tgt='  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %ix_data)\n'
    assert f.count(tgt)==2
    return f.replace(tgt,tgt+en)
