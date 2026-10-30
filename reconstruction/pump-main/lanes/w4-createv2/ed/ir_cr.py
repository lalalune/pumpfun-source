import os,sys; sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w4-createv2/scripts'); import ren
M=os.environ.get('CM','gep+late')
def edit(t):
    t=ren.ren(t)
    G='  %v277 = getelementptr inbounds i8, ptr %_232.val, i64 8\n'
    C='  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(32) %v277, ptr noundef nonnull align 1 dereferenceable(32) %creator1, i64 32, i1 false)\n'
    assert t.count(G)==1 and t.count(C)==1
    if 'gep' in M:
        t=t.replace(G,'')
        A='  call void @llvm.lifetime.start.p0(i64 32, ptr nonnull %sol.i), !noalias !5634\n'
        assert t.count(A)==1; t=t.replace(A,G+A)
    if 'late' in M:
        t=t.replace(C,'')
        P='  store i64 %_19.i, ptr %v286, align 8, !noalias !5634\n'
        assert t.count(P)==1; t=t.replace(P,P+C)
    return t
