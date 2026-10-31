# oracle: dest's lifetime ends right after the dest check (scoped dest); remove its ends at the joins
import re,os
LE='  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %dest.i), !noalias !8627\n'
def f(t):
    assert t.count(LE)==2; t=t.replace(LE,'')
    a='bb7.i106:                                         ; preds = %bb84\n'
    t=t.replace(a,a+LE)
    b='  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %342, ptr noundef nonnull align 1 dereferenceable(32) %dest.i, i64 32, i1 false), !noalias !8627\n'
    assert t.count(b)==1; t=t.replace(b,b+LE)
    if os.environ.get('MV49'):
        # also move bb49's other lifetime ends into exit (q1 style)
        import runpy
        os.environ['MERGE']='bb49.i'
        t=runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)),'q1.py'))['f'](t)
    return t
EDITS=[f]
