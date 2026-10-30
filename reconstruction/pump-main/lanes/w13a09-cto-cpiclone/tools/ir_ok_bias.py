import os
W=os.environ.get('W','2000')
SEL=os.environ.get('SEL','abc')
BR={'a':'br i1 %666, label %bb36, label %bb63','b':'br i1 %689, label %bb45, label %bb63','c':'br i1 %trunc54.not, label %bb110, label %bb109'}
def edit(fn):
    for k in SEL:
        old=BR[k]; assert fn.count(old)==1,k
        fn=fn.replace(old, old+', !prof !99998')
    return fn
def edit_module(m):
    return m+f'\n!99998 = !{{!"branch_weights", i32 {W}, i32 1}}\n'
