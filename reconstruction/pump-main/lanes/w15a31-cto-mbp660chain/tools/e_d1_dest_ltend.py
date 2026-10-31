import re
def f(t):
    i=t.index('; preds = %bb2, %bb55\n  call void @llvm.lifetime.end.p0(i64 32, ptr %dest)\n')
    j=t.index('\n',i)+1; k=t.index('\n',j)+1
    assert 'lifetime.end' in t[j:k]
    return t[:j]+t[k:]
EDITS=[f]
HYP='raw IR: drop lifetime.end(dest) in sweep bb56 (Err join) so JT threads the sweep ? Err edges (w13a27 on current main)'
