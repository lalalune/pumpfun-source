import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tools'))
from fnedit import sub_fn
def edit(t):
    t=sub_fn(t,'dereferenceable(1080) %_218, ptr noalias noundef readonly align 8 dereferenceable(136) %_621','dereferenceable(1080) %666, ptr noalias noundef readonly align 8 dereferenceable(136) %_621')
    return t
