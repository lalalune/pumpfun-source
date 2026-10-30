# S1 IR + conservative X24 between target.sroa.6 and target1 (emulates the original A->X24->E32 join copy)
AL='  %holder_key = alloca [32 x i8], align 8'
LS='  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %target.sroa.6)\n'
CP=('  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %target.sroa.6.0.target1.sroa_idx, '
    'ptr noundef nonnull align 8 dereferenceable(24) %target.sroa.6, i64 24, i1 false)\n')
E69='  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %target.sroa.6)\n  call void @llvm.lifetime.end.p0(i64 48, ptr nonnull %st)\n  br label %bb65\n'
import os
POS=os.environ.get('X24POS','holder_key')
def edit(t):
    al=[l for l in t.split('\n') if l.startswith('  %'+POS+' = alloca')]
    assert len(al)==1
    t=t.replace(al[0]+'\n', '  %x24 = alloca [24 x i8], align 8\n'+al[0]+'\n',1)
    assert t.count(LS)==1; t=t.replace(LS, LS+'  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %x24)\n')
    assert t.count(CP)==1
    t=t.replace(CP, '  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %x24, ptr noundef nonnull align 8 dereferenceable(24) %target.sroa.6, i64 24, i1 false)\n'
                    '  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %target.sroa.6.0.target1.sroa_idx, ptr noundef nonnull align 8 dereferenceable(24) %x24, i64 24, i1 false)\n'
                    '  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %x24)\n')
    assert t.count(E69)==1; t=t.replace(E69, '  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %x24)\n'+E69)
    return t
