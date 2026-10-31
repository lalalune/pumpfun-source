import os
W=os.environ.get('W','7,5')
def f(t):
    y='  br i1 %_123.not.not.i, label %bb30.i, label %bb49.i\n'
    assert t.count(y)==1; t=t.replace(y,y[:-1]+', !prof !99999\n'); t+='\n!99999 = !{!"branch_weights", i32 %s, i32 %s}\n'%tuple(W.split(','))
    return t
EDITS=[f]
