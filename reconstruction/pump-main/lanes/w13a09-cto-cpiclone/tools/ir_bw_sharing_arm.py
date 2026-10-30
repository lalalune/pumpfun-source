import os
T,F=os.environ['BWT'],os.environ['BWF']
def edit(fn):
    old='br i1 %569, label %bb34, label %bb36'
    assert fn.count(old)==1
    return fn.replace(old, old+', !prof !99999')
def edit_module(m):
    return m+f'\n!99999 = !{{!"branch_weights", i32 {T}, i32 {F}}}\n'
