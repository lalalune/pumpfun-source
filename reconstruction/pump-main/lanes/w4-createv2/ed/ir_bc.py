import runpy
ss=runpy.run_path('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w4-createv2/ed/ir_sel_swap.py')['edit']
import os
MODE=os.environ.get('BCMODE','early')
def edit(t):
    t=ss(t)
    import sys; sys.path.insert(0,'scripts'); import ren; t=ren.ren(t)
    A='''  %v286 = getelementptr inbounds i8, ptr %_235, i64 232
  %_249 = load ptr, ptr %v286, align 8, !nonnull !2, !align !3, !noundef !2
  %v287 = getelementptr inbounds i8, ptr %_249, i64 8
'''
    C='''  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(32) %v287, ptr noundef nonnull align 1 dereferenceable(32) %creator1, i64 32, i1 false)
'''
    assert t.count(A)==1 and t.count(C)==1
    if 'early' in MODE:
        t=t.replace(A,'')
        M='  call void @llvm.lifetime.start.p0(i64 32, ptr nonnull %_131)\n'
        assert t.count(M)==1
        t=t.replace(M,A+M)
    if 'late' in MODE:
        t=t.replace(C,'')
        P='''  store i64 %_139, ptr %v296, align 8
'''
        t=t.replace(P,P+C)
    return t
