import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tools'))
from fnedit import sub_fn
def edit(t):
    a='  %_618 = load ptr, ptr %a, align 8, !nonnull !2, !align !3, !noundef !2\n'
    t=sub_fn(t,a,a+'  %g57 = getelementptr inbounds i8, ptr %_618, i64 8\n')
    t=sub_fn(t,'dereferenceable(1080) %_218, ptr noalias noundef readonly align 8 dereferenceable(136) %_621','dereferenceable(1080) %g57, ptr noalias noundef readonly align 8 dereferenceable(136) %_621')
    return t
