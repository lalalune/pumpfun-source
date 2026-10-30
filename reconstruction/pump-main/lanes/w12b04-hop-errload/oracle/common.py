G='  %_218 = getelementptr inbounds i8, ptr %_618, i64 8\n'
def rm(t):
    assert t.count(G)==1; return t.replace(G,'',1)
def after(t,anchor):
    assert t.count(anchor)==1, anchor
    return t.replace(anchor,anchor+G,1)
def before(t,anchor):
    assert t.count(anchor)==1, anchor
    return t.replace(anchor,G+anchor,1)
