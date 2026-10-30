def edit(fn):
    a='  br i1 %565, label %bb33, label %bb35\n'
    assert fn.count(a)==1
    return fn.replace(a,'  br i1 %565, label %bb33, label %bb35, !prof !9999901\n')
def edit_module(m): return m+'\n!9999901 = !{!"branch_weights", i32 1, i32 2000}\n'
